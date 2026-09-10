"""Repository-wide pytest configuration and shared fixtures.

Lives at the repo root so every workspace member's tests (siblings, not descendants of each
other) can see the same fixtures. Disables OpenTelemetry export for the whole session.

Integration fixtures: a Postgres reached via `KPI_TEST_DATABASE_URL` (CI service, or `make up`'s
database) or, when unset, a `postgres:16-alpine` testcontainer. Migrations run once per session
and the sample + demo datasets are seeded once.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest

os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("KPI_ENV", "test")

REPO_ROOT = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data"


@pytest.fixture(scope="session")
def sample_csv_path() -> Path:
    return DATA_DIR / "kpi_sample.csv"


@pytest.fixture(scope="session")
def edge_cases_csv_path() -> Path:
    return DATA_DIR / "demo_edge_cases.csv"


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    """Async SQLAlchemy URL of a disposable Postgres (env override or testcontainers)."""
    env_url = os.environ.get("KPI_TEST_DATABASE_URL")
    if env_url:
        yield env_url
        return
    from testcontainers.community.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        yield pg.get_connection_url()


@pytest.fixture(scope="session")
def migrated_database_url(
    postgres_url: str, sample_csv_path: Path, edge_cases_csv_path: Path
) -> str:
    """Postgres at Alembic head with both datasets loaded once per session."""
    from kpi_core.cli import run_migrations, run_seed
    from kpi_core.db.engine import dispose_engines

    sync_url = postgres_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    run_migrations(sync_url)

    async def _seed_all() -> None:
        # One event loop for both seeds; cached engines are bound to it and disposed with it.
        await run_seed(sample_csv_path, postgres_url)
        await run_seed(edge_cases_csv_path, postgres_url)
        await dispose_engines()

    asyncio.run(_seed_all())
    return postgres_url


@pytest.fixture
async def sql_sessions(migrated_database_url: str) -> AsyncIterator[object]:
    """A fresh sessionmaker per test (engine per URL is cached and disposed at the end)."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(migrated_database_url)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()
