"""History, QTD and full-company estimate retrieval."""

from __future__ import annotations

from kpi_core.context import RequestContext
from kpi_core.models import (
    CompanyEstimates,
    KpiDefinition,
    KpiHistory,
    KpiQtd,
    KpiSeries,
    PeriodRange,
)
from kpi_core.periods import missing_periods, validate_range
from kpi_core.repositories.protocols import KpiRepository
from kpi_core.services.companies import get_company
from kpi_core.services.kpis import resolve_kpi
from kpi_core.validation import clamp_limit

DEFAULT_HISTORY_LIMIT = 64
MAX_HISTORY_LIMIT = 64


async def get_kpi_history(
    ctx: RequestContext,
    repo: KpiRepository,
    *,
    ticker: str,
    kpi: str,
    from_period: str | None = None,
    to_period: str | None = None,
    limit: int | None = None,
) -> KpiHistory:
    """Completed-quarter estimates, chronological. Empty ranges are a success with a note."""
    company = await get_company(ctx, repo, ticker)
    definition = await resolve_kpi(ctx, repo, kpi, ticker=company.ticker)
    start, end = validate_range(from_period, to_period)
    limit_v = clamp_limit(limit, default=DEFAULT_HISTORY_LIMIT, maximum=MAX_HISTORY_LIMIT)
    points, total = await repo.get_history(
        ctx,
        ticker=company.ticker,
        kpi_slug=definition.slug,
        from_period=str(start) if start else None,
        to_period=str(end) if end else None,
        limit=limit_v,
    )
    points = sorted(points, key=lambda p: p.period_start)
    available = await repo.get_available_range(ctx, ticker=company.ticker, kpi_slug=definition.slug)
    requested = PeriodRange(
        from_period=str(start) if start else None, to_period=str(end) if end else None
    )
    note: str | None = None
    if not points:
        if available is None:
            note = f"No historical estimates are published for {company.ticker} {definition.slug}."
        else:
            note = (
                f"No historical estimates for {company.ticker} {definition.slug} "
                "in the requested range; "
                f"data is available for {available.from_period}..{available.to_period}."
            )
    else:
        gaps = missing_periods([p.period for p in points])
        if gaps:
            note = f"History has gaps: no estimates for {', '.join(gaps)}."
    return KpiHistory(
        company=company,
        kpi=definition,
        points=points,
        count=len(points),
        requested_range=requested if (start or end) else None,
        available_range=available,
        truncated=total > len(points),
        note=note,
    )


async def get_kpi_qtd(ctx: RequestContext, repo: KpiRepository, *, ticker: str, kpi: str) -> KpiQtd:
    """Current quarter-to-date snapshots (ascending by as_of) with the latest flagged."""
    company = await get_company(ctx, repo, ticker)
    definition = await resolve_kpi(ctx, repo, kpi, ticker=company.ticker)
    snapshots = sorted(
        await repo.get_qtd_snapshots(ctx, ticker=company.ticker, kpi_slug=definition.slug),
        key=lambda s: s.as_of,
    )
    latest = snapshots[-1] if snapshots else None
    prior = await repo.get_latest_historical(ctx, ticker=company.ticker, kpi_slug=definition.slug)
    note = (
        None
        if latest
        else f"No QTD snapshots are published for {company.ticker} {definition.slug}."
    )
    return KpiQtd(
        company=company,
        kpi=definition,
        period=latest.period if latest else None,
        latest=latest,
        snapshots=snapshots,
        prior_quarter=prior,
        note=note,
    )


async def get_company_estimates(
    ctx: RequestContext, repo: KpiRepository, *, ticker: str
) -> CompanyEstimates:
    """Every KPI of a company with its full history and latest QTD, kept separate."""
    company = await get_company(ctx, repo, ticker)
    series: list[KpiSeries] = []
    for company_kpi in await repo.list_company_kpis(ctx, company.ticker):
        points, _ = await repo.get_history(
            ctx,
            ticker=company.ticker,
            kpi_slug=company_kpi.slug,
            from_period=None,
            to_period=None,
            limit=MAX_HISTORY_LIMIT,
        )
        snapshots = await repo.get_qtd_snapshots(
            ctx, ticker=company.ticker, kpi_slug=company_kpi.slug
        )
        latest = max(snapshots, key=lambda s: s.as_of) if snapshots else None
        definition = KpiDefinition.model_validate(
            company_kpi.model_dump(include=set(KpiDefinition.model_fields))
        )
        series.append(
            KpiSeries(
                kpi=definition,
                history=sorted(points, key=lambda p: p.period_start),
                qtd_period=latest.period if latest else None,
                qtd_latest=latest,
            )
        )
    return CompanyEstimates(company=company, series=series)
