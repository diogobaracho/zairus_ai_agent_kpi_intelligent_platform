from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from kpi_api.dependencies import get_context, get_repo
from kpi_api.schemas.common import SectorList
from kpi_core.context import RequestContext
from kpi_core.repositories.protocols import KpiRepository
from kpi_core.services import companies

router = APIRouter(prefix="/v1", tags=["discovery"])


@router.get("/sectors", response_model=SectorList, summary="List sectors with company counts")
async def list_sectors(
    ctx: Annotated[RequestContext, Depends(get_context)],
    repo: Annotated[KpiRepository, Depends(get_repo)],
) -> SectorList:
    return SectorList(items=await companies.list_sectors(ctx, repo))
