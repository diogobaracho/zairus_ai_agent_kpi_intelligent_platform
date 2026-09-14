from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from kpi_api.dependencies import get_context, get_repo
from kpi_core.context import RequestContext
from kpi_core.models import KpiHistory, KpiQtd
from kpi_core.repositories.protocols import KpiRepository
from kpi_core.services import estimates

router = APIRouter(prefix="/v1/companies/{ticker}/kpis/{kpi}", tags=["estimates"])

TickerPath = Annotated[str, Path(min_length=1, max_length=64)]
KpiPath = Annotated[str, Path(min_length=1, max_length=80, description="KPI slug, name or alias")]


@router.get(
    "/history", response_model=KpiHistory, summary="Historical quarterly estimates, chronological"
)
async def history(
    ticker: TickerPath,
    kpi: KpiPath,
    ctx: Annotated[RequestContext, Depends(get_context)],
    repo: Annotated[KpiRepository, Depends(get_repo)],
    from_period: Annotated[str | None, Query(max_length=8, description="YYYYQn")] = None,
    to_period: Annotated[str | None, Query(max_length=8, description="YYYYQn")] = None,
    limit: Annotated[int, Query(ge=1, le=64)] = 64,
) -> KpiHistory:
    return await estimates.get_kpi_history(
        ctx, repo, ticker=ticker, kpi=kpi, from_period=from_period, to_period=to_period, limit=limit
    )


@router.get(
    "/qtd",
    response_model=KpiQtd,
    summary="Current quarter-to-date snapshots with the latest flagged",
)
async def qtd(
    ticker: TickerPath,
    kpi: KpiPath,
    ctx: Annotated[RequestContext, Depends(get_context)],
    repo: Annotated[KpiRepository, Depends(get_repo)],
) -> KpiQtd:
    return await estimates.get_kpi_qtd(ctx, repo, ticker=ticker, kpi=kpi)
