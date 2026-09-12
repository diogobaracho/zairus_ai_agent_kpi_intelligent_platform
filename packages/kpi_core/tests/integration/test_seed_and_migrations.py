from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kpi_core.db.orm import CompanyRow, KpiEstimateRow, KpiRow
from kpi_core.seed.csv_loader import read_kpi_csv
from kpi_core.seed.seeder import seed_database

pytestmark = pytest.mark.integration


async def test_seed_is_idempotent(
    sql_sessions: async_sessionmaker[AsyncSession], sample_csv_path: Path
) -> None:
    rows = read_kpi_csv(sample_csv_path)
    async with sql_sessions() as session:
        report = await seed_database(session, rows)
        await session.commit()
    assert (report.companies, report.kpis, report.estimates) == (16, 13, 1062)
    assert report.inserted == 0 and report.updated == 1062  # session fixture already seeded once
    async with sql_sessions() as session:
        estimates = (await session.execute(select(func.count(KpiEstimateRow.id)))).scalar_one()
        companies = (await session.execute(select(func.count(CompanyRow.id)))).scalar_one()
        kpis = (await session.execute(select(func.count(KpiRow.id)))).scalar_one()
    assert (estimates, companies, kpis) == (1093, 19, 13)


async def test_constraints_present(sql_sessions: async_sessionmaker[AsyncSession]) -> None:
    from sqlalchemy import inspect

    async with sql_sessions() as session:

        def _inspect(sync_conn):  # type: ignore[no-untyped-def]
            insp = inspect(sync_conn)
            return (
                {c["name"] for c in insp.get_unique_constraints("kpi_estimates")},
                {i["name"] for i in insp.get_indexes("companies")},
                {i["name"] for i in insp.get_indexes("kpi_estimates")},
            )

        uniques, company_indexes, estimate_indexes = await (await session.connection()).run_sync(
            _inspect
        )
    assert "uq_estimates_key" in uniques
    assert {
        "ix_companies_sector",
        "ix_companies_lower_name",
        "ix_companies_name_trgm",
    } <= company_indexes
    assert {"ix_estimates_lookup", "ix_estimates_qtd"} <= estimate_indexes
