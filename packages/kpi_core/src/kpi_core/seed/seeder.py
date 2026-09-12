"""Idempotent upsert of CSV rows into Postgres. A second run inserts 0 rows."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from kpi_core.db.orm import CompanyRow, KpiEstimateRow, KpiRow
from kpi_core.models import SeedReport
from kpi_core.seed.csv_loader import SeedRow

_SENTINEL_DATE = date(1, 1, 1)


async def seed_database(session: AsyncSession, rows: list[SeedRow]) -> SeedReport:
    """Upsert companies, kpis and estimates in the caller's transaction."""
    companies = {r.ticker: r for r in rows}
    kpis = {r.kpi_slug: r for r in rows}

    for ticker, row in sorted(companies.items()):
        stmt = insert(CompanyRow).values(ticker=ticker, name=row.company_name, sector=row.sector)
        stmt = stmt.on_conflict_do_update(
            index_elements=[CompanyRow.ticker],
            set_={"name": row.company_name, "sector": row.sector},
        )
        await session.execute(stmt)
    for slug, row in sorted(kpis.items()):
        stmt = insert(KpiRow).values(
            slug=slug,
            name=row.kpi,
            display_name=row.kpi_display_name,
            unit=row.unit,
            unit_kind=row.unit_kind,
            scale=row.scale,
            description=f"{row.kpi_display_name} in {row.unit}, estimated quarterly by ZairusData.",
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[KpiRow.slug],
            set_={
                "name": row.kpi,
                "display_name": row.kpi_display_name,
                "unit": row.unit,
                "unit_kind": row.unit_kind,
                "scale": row.scale,
            },
        )
        await session.execute(stmt)

    company_ids: dict[str, int] = {
        t: i for t, i in (await session.execute(select(CompanyRow.ticker, CompanyRow.id))).all()
    }
    kpi_ids: dict[str, int] = {
        s: i for s, i in (await session.execute(select(KpiRow.slug, KpiRow.id))).all()
    }

    existing = (
        await session.execute(
            select(
                KpiEstimateRow.company_id,
                KpiEstimateRow.kpi_id,
                KpiEstimateRow.period,
                KpiEstimateRow.estimate_type,
                KpiEstimateRow.as_of,
            )
        )
    ).all()
    existing_keys = {(c, k, p, t, a or _SENTINEL_DATE) for c, k, p, t, a in existing}

    inserted = updated = 0
    for row in rows:
        cid, kid = company_ids[row.ticker], kpi_ids[row.kpi_slug]
        key = (cid, kid, row.period, row.estimate_type, row.as_of or _SENTINEL_DATE)
        if key in existing_keys:
            updated += 1
        else:
            inserted += 1
            existing_keys.add(key)
        stmt = insert(KpiEstimateRow).values(
            company_id=cid,
            kpi_id=kid,
            period=row.period,
            period_start=row.period_start,
            period_end=row.period_end,
            estimate_type=row.estimate_type,
            value=row.value,
            as_of=row.as_of,
        )
        stmt = stmt.on_conflict_do_update(constraint="uq_estimates_key", set_={"value": row.value})
        await session.execute(stmt)

    return SeedReport(
        companies=len(companies),
        kpis=len(kpis),
        estimates=len(rows),
        inserted=inserted,
        updated=updated,
    )
