from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from kpi_api.dependencies import get_context, get_repo
from kpi_api.schemas.common import CompanyKpiList, KpiList
from kpi_core.context import RequestContext
from kpi_core.repositories.protocols import KpiRepository
from kpi_core.services import companies, kpis

router = APIRouter(prefix="/v1", tags=["discovery"])


@router.get("/kpis", response_model=KpiList, summary="KPI catalogue with normalised metadata")
async def list_kpis(
    ctx: Annotated[RequestContext, Depends(get_context)],
    repo: Annotated[KpiRepository, Depends(get_repo)],
) -> KpiList:
    return KpiList(items=await kpis.list_kpi_catalog(ctx, repo))


@router.get(
    "/companies/{ticker}/kpis",
    response_model=CompanyKpiList,
    summary="KPIs published for a company",
)
async def company_kpis(
    ticker: Annotated[str, Path(min_length=1, max_length=64)],
    ctx: Annotated[RequestContext, Depends(get_context)],
    repo: Annotated[KpiRepository, Depends(get_repo)],
) -> CompanyKpiList:
    company = await companies.get_company(ctx, repo, ticker)
    return CompanyKpiList(
        company=company, items=await kpis.list_company_kpis(ctx, repo, company.ticker)
    )
