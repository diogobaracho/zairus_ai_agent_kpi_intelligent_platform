from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from kpi_api.app import create_app
from kpi_api.settings import ApiSettings
from kpi_core.repositories.memory import (
    InMemoryAuditRepository,
    InMemoryChatRepository,
    InMemoryKpiRepository,
)


@pytest.fixture(scope="session")
def repo(sample_csv_path: Path, edge_cases_csv_path: Path) -> InMemoryKpiRepository:
    return InMemoryKpiRepository.from_csv(sample_csv_path, edge_cases_csv_path)


@pytest.fixture
def settings() -> ApiSettings:
    return ApiSettings(env="test", rate_limit_rps=1000, rate_limit_burst=1000, mcp_mode="inprocess")


@pytest.fixture
def app(settings: ApiSettings, repo: InMemoryKpiRepository) -> FastAPI:
    return create_app(
        settings,
        repo=repo,
        audit_repo=InMemoryAuditRepository(),
        chat_repo=InMemoryChatRepository(),
    )


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
