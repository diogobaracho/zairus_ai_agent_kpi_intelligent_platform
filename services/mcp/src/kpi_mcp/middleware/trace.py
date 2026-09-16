"""Bind a RequestContext (trace id, tenant, caller) for the duration of a tool call.

Trace id resolution order: `meta.trace_id` sent by the client (the chat agent sets it) →
`X-Correlation-Id` header (HTTP transport) → minted. Identity never comes from tool arguments.
"""

from __future__ import annotations

from typing import Any

from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

from kpi_core.context import RequestContext, bind_context, reset_context
from kpi_core.obs.correlation import coerce_trace_id, set_trace_id
from kpi_mcp.settings import McpSettings


def _as_dict(meta: Any) -> dict[str, Any]:
    if meta is None:
        return {}
    if isinstance(meta, dict):
        return dict(meta)
    dump = getattr(meta, "model_dump", None)
    if callable(dump):
        data = dump(exclude_none=True)
        extra = getattr(meta, "model_extra", None) or {}
        return {**data, **extra}
    return {}


def _meta(context: MiddlewareContext[Any]) -> dict[str, Any]:
    """Client-supplied request metadata (`meta=` on call_tool): message._meta first, then the
    request context's merged meta."""
    merged = _as_dict(getattr(context.message, "meta", None))
    fc = context.fastmcp_context
    if fc is not None:
        try:
            request_context = fc.request_context
        except Exception:
            request_context = None
        if request_context is not None:
            merged = {**_as_dict(request_context.meta), **merged}
    return merged


def resolve_trace_id(context: MiddlewareContext[Any], header: str) -> str:
    candidate = _meta(context).get("trace_id")
    if not candidate:
        try:
            headers = get_http_headers()
        except Exception:
            headers = {}
        candidate = headers.get(header.lower())
    return coerce_trace_id(str(candidate) if candidate else None)


def transport_name(context: MiddlewareContext[Any]) -> str | None:
    fc = context.fastmcp_context
    value = getattr(fc, "transport", None) if fc is not None else None
    return str(value) if value else None


def session_id(context: MiddlewareContext[Any]) -> str | None:
    fc = context.fastmcp_context
    try:
        value = fc.session_id if fc is not None else None
    except Exception:
        return None
    return str(value) if value else None


class TraceMiddleware(Middleware):
    def __init__(self, settings: McpSettings) -> None:
        self.settings = settings

    async def on_call_tool(
        self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]
    ) -> Any:
        trace_id = resolve_trace_id(context, self.settings.correlation_header)
        ctx = RequestContext(
            trace_id=trace_id,
            tenant_id=self.settings.default_tenant_id,
            caller="mcp",
            session_id=session_id(context),
        )
        set_trace_id(trace_id)
        token = bind_context(ctx)
        try:
            return await call_next(context)
        finally:
            reset_context(token)
            set_trace_id(None)
