from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from kpi_api.dependencies import get_audit_repo, get_context
from kpi_api.schemas.chat import AuditList
from kpi_core.context import RequestContext
from kpi_core.repositories.protocols import AuditRepository
from kpi_core.services import audit as audit_service

router = APIRouter(prefix="/v1/audit", tags=["audit"])


@router.get(
    "/tool-calls",
    response_model=AuditList,
    summary="Tool-call audit rows (filter by trace_id, tool, status)",
)
async def tool_calls(
    ctx: Annotated[RequestContext, Depends(get_context)],
    repo: Annotated[AuditRepository, Depends(get_audit_repo)],
    trace_id: Annotated[str | None, Query(max_length=64)] = None,
    tool_name: Annotated[str | None, Query(max_length=64)] = None,
    status: Annotated[str | None, Query(pattern="^(ok|error|timeout|rejected)$")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AuditList:
    rows = await audit_service.query_tool_calls(
        repo,
        tenant_id=ctx.tenant_id,
        trace_id=trace_id,
        tool_name=tool_name,
        status=status,
        limit=limit,
    )
    return AuditList(items=rows)
