"""`python -m kpi_core.cli migrate | seed <csv> | check`."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

from kpi_core.db.engine import dispose_engines, session_scope
from kpi_core.obs.logging import configure_logging, log_event
from kpi_core.seed.csv_loader import read_kpi_csv
from kpi_core.seed.seeder import seed_database
from kpi_core.settings import get_settings

ALEMBIC_DIR = Path(__file__).resolve().parent.parent.parent


def run_migrations(database_url: str | None = None) -> None:
    from alembic import command
    from alembic.config import Config

    settings = get_settings()
    cfg = Config(str(ALEMBIC_DIR / "alembic.ini"))
    cfg.set_main_option(
        "script_location", str(ALEMBIC_DIR / "src" / "kpi_core" / "db" / "migrations")
    )
    url = database_url or settings.sync_database_url
    cfg.cmd_opts = argparse.Namespace(x=[f"url={url}"])
    command.upgrade(cfg, "head")


async def run_seed(path: Path, database_url: str | None = None) -> None:
    settings = get_settings()
    rows = read_kpi_csv(path)
    async with session_scope(database_url or settings.database_url) as session:
        report = await seed_database(session, rows)
    await dispose_engines()  # same loop as the connections; a later loop cannot close them cleanly
    log_event("seed", file=str(path), **report.model_dump())
    print(f"SeedReport({', '.join(f'{k}={v}' for k, v in report.model_dump().items())})")


async def run_check(database_url: str | None = None) -> None:
    settings = get_settings()
    async with session_scope(database_url or settings.database_url) as session:
        value = (await session.execute(select(1))).scalar_one()
    await dispose_engines()
    print(f"db ok ({value})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kpi_core.cli")
    parser.add_argument("--database-url", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate", help="apply Alembic migrations to head")
    seed = sub.add_parser("seed", help="load a KPI CSV (idempotent)")
    seed.add_argument("path", type=Path)
    sub.add_parser("check", help="SELECT 1")
    args = parser.parse_args(argv)
    configure_logging("kpi-cli", get_settings().log_level)
    if args.command == "migrate":
        run_migrations(args.database_url)
        print("migrations applied")
    elif args.command == "seed":
        asyncio.run(run_seed(args.path, args.database_url))
    elif args.command == "check":
        asyncio.run(run_check(args.database_url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
