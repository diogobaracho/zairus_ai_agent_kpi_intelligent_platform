"""Tool-call audit: record never fails the caller; query for inspection."""

from __future__ import annotations

import logging

from kpi_core.models import ToolCallAudit
from kpi_core.obs.logging import log_event
from kpi_core.repositories.protocols import AuditRepository

logger = logging.getLogger(__name__)


async def record_tool_call(repo: AuditRepository, audit: ToolCallAudit) -> None:
    """Persist and log one tool call. Storage failures are logged, never raised."""
    log_event(
        "tool_call",
        tool_name=audit.tool_name,
        arguments=audit.arguments,
        status=audit.status,
        duration_ms=audit.duration_ms,
        error=audit.error,
        result_summary=audit.result_summary,
        caller=audit.caller,
        transport=audit.transport,
        session_id=audit.session_id,
        conversation_id=audit.conversation_id,
        trace_id=audit.trace_id,
    )
    try:
        await repo.record(audit)
    except Exception:
        logger.exception(
            "audit_failed", extra={"tool_name": audit.tool_name, "trace_id": audit.trace_id}
        )


async def query_tool_calls(
    repo: AuditRepository,
    *,
    tenant_id: str,
    trace_id: str | None = None,
    tool_name: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[ToolCallAudit]:
    return await repo.query(
        tenant_id=tenant_id,
        trace_id=trace_id,
        tool_name=tool_name,
        status=status,
        limit=min(limit, 200),
    )
