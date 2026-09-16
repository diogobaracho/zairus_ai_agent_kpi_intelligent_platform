"""Map KpiError to the MCP error envelope carried by ToolError (-> isError: true)."""

from __future__ import annotations

import json
from collections.abc import Awaitable
from typing import Any

from fastmcp.exceptions import ToolError

from kpi_core.errors import KpiError
from kpi_core.obs.correlation import get_trace_id


def envelope_for(error: KpiError, trace_id: str | None = None) -> dict[str, Any]:
    return error.to_tool_envelope(trace_id=trace_id or get_trace_id())


def kpi_error_to_tool_error(error: KpiError, trace_id: str | None = None) -> ToolError:
    return ToolError(json.dumps(envelope_for(error, trace_id)))


def parse_envelope(text: str) -> dict[str, Any] | None:
    """The envelope dict if `text` is one, else None."""
    try:
        payload = json.loads(text)
    except (TypeError, ValueError):
        return None
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        error: dict[str, Any] = payload["error"]
        return error
    return None


async def run_tool[T](awaitable: Awaitable[T]) -> T:
    """Await a service call; convert KpiError into the envelope. Anything else stays masked."""
    try:
        return await awaitable
    except KpiError as error:
        raise kpi_error_to_tool_error(error) from None
