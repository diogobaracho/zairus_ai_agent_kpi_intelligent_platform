import pytest

from kpi_core.context import RequestContext
from kpi_core.errors import InvalidPeriod, InvalidPeriodRange, KpiNotFound
from kpi_core.repositories.memory import InMemoryKpiRepository
from kpi_core.services import estimates


async def test_history_full_and_chronological(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    hist = await estimates.get_kpi_history(ctx, memory_repo, ticker="orby", kpi="revenue")
    assert (
        hist.count == 14
        and hist.points[0].period == "2023Q1"
        and hist.points[-1].period == "2026Q2"
    )
    assert hist.points == sorted(hist.points, key=lambda p: p.period_start)
    assert hist.available_range is not None and hist.available_range.to_period == "2026Q2"
    assert hist.note is None and not hist.truncated and hist.requested_range is None
    assert all(p.unit == "$MM" for p in hist.points)


async def test_history_range_and_truncation(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    hist = await estimates.get_kpi_history(
        ctx, memory_repo, ticker="ORBY", kpi="total_revenue", from_period="2025Q3"
    )
    assert [p.period for p in hist.points] == ["2025Q3", "2025Q4", "2026Q1", "2026Q2"]
    assert hist.requested_range is not None and hist.requested_range.from_period == "2025Q3"
    short = await estimates.get_kpi_history(
        ctx, memory_repo, ticker="ORBY", kpi="total_revenue", limit=3
    )
    assert short.count == 3 and short.truncated


async def test_history_empty_range_is_success_with_note(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    hist = await estimates.get_kpi_history(
        ctx, memory_repo, ticker="ORBY", kpi="churn", from_period="2019Q1", to_period="2019Q4"
    )
    assert hist.points == [] and hist.count == 0
    assert hist.note is not None and "2023Q1..2026Q2" in hist.note


async def test_history_no_data_at_all(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    hist = await estimates.get_kpi_history(ctx, memory_repo, ticker="FRSH", kpi="paying_customers")
    assert (
        hist.points == [] and hist.available_range is None and "No historical" in (hist.note or "")
    )


async def test_history_gaps_note(ctx: RequestContext, memory_repo: InMemoryKpiRepository) -> None:
    hist = await estimates.get_kpi_history(ctx, memory_repo, ticker="SPRW", kpi="arr")
    assert hist.count == 5 and "gaps" in (hist.note or "") and "2023Q2" in (hist.note or "")


async def test_history_invalid_period_and_range(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    with pytest.raises(InvalidPeriod):
        await estimates.get_kpi_history(
            ctx, memory_repo, ticker="ORBY", kpi="revenue", from_period="Q3 2024"
        )
    with pytest.raises(InvalidPeriodRange):
        await estimates.get_kpi_history(
            ctx, memory_repo, ticker="ORBY", kpi="revenue", from_period="2025Q1", to_period="2024Q1"
        )


async def test_history_kpi_not_for_company(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    with pytest.raises(KpiNotFound):
        await estimates.get_kpi_history(ctx, memory_repo, ticker="GAPW", kpi="arr")


async def test_qtd_latest_and_prior(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    qtd = await estimates.get_kpi_qtd(ctx, memory_repo, ticker="ORBY", kpi="Total Revenue ($MM)")
    assert (
        qtd.period == "2026Q3" and qtd.latest is not None and str(qtd.latest.as_of) == "2026-09-15"
    )
    assert [str(s.as_of) for s in qtd.snapshots] == [
        "2026-07-31",
        "2026-08-15",
        "2026-08-31",
        "2026-09-15",
    ]
    assert qtd.prior_quarter is not None and qtd.prior_quarter.period == "2026Q2"
    assert qtd.note is None


async def test_qtd_missing_is_success_with_note(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    qtd = await estimates.get_kpi_qtd(ctx, memory_repo, ticker="GAPW", kpi="total_revenue")
    assert qtd.latest is None and qtd.snapshots == [] and qtd.period is None
    assert qtd.prior_quarter is not None and "No QTD" in (qtd.note or "")


async def test_qtd_only_company(ctx: RequestContext, memory_repo: InMemoryKpiRepository) -> None:
    qtd = await estimates.get_kpi_qtd(ctx, memory_repo, ticker="FRSH", kpi="customers")
    assert qtd.latest is not None and len(qtd.snapshots) == 4 and qtd.prior_quarter is None


async def test_company_estimates_bundle(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    bundle = await estimates.get_company_estimates(ctx, memory_repo, ticker="ORBY")
    assert bundle.company.ticker == "ORBY" and len(bundle.series) == 5
    rev = next(s for s in bundle.series if s.kpi.slug == "total_revenue")
    assert len(rev.history) == 14 and rev.qtd_period == "2026Q3" and rev.qtd_latest is not None
    gapw = await estimates.get_company_estimates(ctx, memory_repo, ticker="GAPW")
    assert len(gapw.series) == 2 and all(s.qtd_latest is None for s in gapw.series)
