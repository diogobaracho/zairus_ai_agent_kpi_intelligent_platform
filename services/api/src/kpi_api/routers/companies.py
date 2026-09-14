from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from kpi_api.dependencies import get_context, get_repo
from kpi_api.schemas.common import CompanyPage
from kpi_core.context import RequestContext
from kpi_core.models import Company, CompanyEstimates
from kpi_core.repositories.protocols import KpiRepository
from kpi_core.services import companies, estimates

router = APIRouter(prefix="/v1/companies", tags=["discovery"])

TickerPath = Annotated[
    str, Path(min_length=1, max_length=64, description="Ticker (case-insensitive)")
]


@router.get("", response_model=CompanyPage, summary="Search companies by ticker or partial name")
async def search(
    ctx: Annotated[RequestContext, Depends(get_context)],
    repo: Annotated[KpiRepository, Depends(get_repo)],
    q: Annotated[
        str | None, Query(max_length=64, description="Ticker or partial company name")
    ] = None,
    sector: Annotated[str | None, Query(max_length=64)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CompanyPage:
    page = await companies.search_companies(
        ctx, repo, query=q, sector=sector, limit=limit, offset=offset
    )
    return CompanyPage(
        items=page.items,
        total=page.total,
        limit=page.limit,
        offset=page.offset,
        suggestions=page.suggestions,
    )


@router.get("/{ticker}", response_model=Company, summary="Get one company by ticker")
async def get_company(
    ticker: TickerPath,
    ctx: Annotated[RequestContext, Depends(get_context)],
    repo: Annotated[KpiRepository, Depends(get_repo)],
) -> Company:
    return await companies.get_company(ctx, repo, ticker)


@router.get(
    "/{ticker}/estimates",
    response_model=CompanyEstimates,
    summary="All KPI estimates for a company: history and current QTD, kept separate",
)
async def company_estimates(
    ticker: TickerPath,
    ctx: Annotated[RequestContext, Depends(get_context)],
    repo: Annotated[KpiRepository, Depends(get_repo)],
) -> CompanyEstimates:
    return await estimates.get_company_estimates(ctx, repo, ticker=ticker)
