"""One audit row + one `tool_call` log line per tool call, whatever the caller or outcome."""

from __future__ import annotations

import time
from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

from kpi_core.context import current_context
from kpi_core.models import ToolCallAudit
from kpi_core.repositories.protocols import AuditRepository
from kpi_core.services.audit import record_tool_call
from kpi_mcp.envelope import parse_envelope
from kpi_mcp.middleware.trace import _meta, session_id, transport_name
from kpi_mcp.settings import McpSettings

_REJECTED_CODES = {"validation_error", "invalid_ticker", "invalid_period", "invalid_period_range"}


def summarize(result: Any) -> str | None:
    """Short human summary of a successful result (never the payload)."""
    structured = getattr(result, "structured_content", None)
    if not isinstance(structured, dict):
        return None
    parts: list[str] = []
    for key in ("total", "count"):
        if key in structured:
            parts.append(f"{key}={structured[key]}")
    for key in ("companies", "kpis", "points", "snapshots"):
        if isinstance(structured.get(key), list):
            parts.append(f"{key}={len(structured[key])}")
    latest = structured.get("latest")
    if isinstance(latest, dict) and latest.get("as_of"):
        parts.append(f"latest_as_of={latest['as_of']}")
    if structured.get("note"):
        parts.append("note")
    return " ".join(parts) or "ok"


class AuditMiddleware(Middleware):
    def __init__(self, audit_repo: AuditRepository, settings: McpSettings) -> None:
        self.audit_repo = audit_repo
        self.settings = settings

    async def on_call_tool(
        self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]
    ) -> Any:
        started = time.perf_counter()
        status = "ok"
        error: dict[str, Any] | None = None
        summary: str | None = None
        try:
            result = await call_next(context)
            summary = summarize(result)
            return result
        except ToolError as exc:
            envelope = parse_envelope(str(exc))
            # FastMCP masks unexpected exceptions as ToolError("Error calling tool ...") before
            # middleware sees them; anything that is not our envelope is an internal error.
            error = envelope or {"code": "internal_error", "message": str(exc)}
            status = "rejected" if error.get("code") in _REJECTED_CODES else "error"
            raise
        except TimeoutError:
            status, error = "timeout", {"code": "tool_timeout", "message": "tool timed out"}
            raise
        except Exception as exc:
            status, error = "error", {"code": "internal_error", "message": type(exc).__name__}
            raise
        finally:
            ctx = current_context()
            meta = _meta(context)
            await record_tool_call(
                self.audit_repo,
                ToolCallAudit(
                    tenant_id=ctx.tenant_id if ctx else self.settings.default_tenant_id,
                    trace_id=ctx.trace_id if ctx else "-",
                    session_id=session_id(context),
                    conversation_id=str(meta["conversation_id"])
                    if meta.get("conversation_id")
                    else None,
                    tool_name=context.message.name,
                    arguments=dict(context.message.arguments or {}),
                    status=status,
                    duration_ms=int((time.perf_counter() - started) * 1000),
                    error=error,
                    result_summary=summary,
                    caller=str(meta.get("caller") or "mcp"),
                    transport=transport_name(context) or self.settings.mcp_transport,
                ),
            )
