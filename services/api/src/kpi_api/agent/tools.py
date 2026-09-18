"""MCP tool gateway: list tools, convert schemas for Anthropic, execute calls with trace ids."""

from __future__ import annotations

import copy
import json
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport

from kpi_api.agent.types import McpToolSpec, ToolOutcome

ClientFactory = Callable[[str], Client[Any]]  # trace_id -> configured client


def http_client_factory(url: str, header: str = "X-Correlation-Id") -> ClientFactory:
    def factory(trace_id: str) -> Client[Any]:
        return Client(StreamableHttpTransport(url=url, headers={header: trace_id}))

    return factory


def inprocess_client_factory(server: FastMCP) -> ClientFactory:
    def factory(trace_id: str) -> Client[Any]:
        return Client(server)

    return factory


def is_strict_compatible(schema: dict[str, Any]) -> bool:
    """Anthropic strict mode needs additionalProperties=false and every property required."""
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    if schema.get("additionalProperties") is not False or set(props) != required:
        return False
    return "$ref" not in json.dumps(schema)


def to_anthropic_tool(spec: McpToolSpec) -> dict[str, Any]:
    schema = copy.deepcopy(spec.input_schema)
    schema.setdefault("type", "object")
    schema["additionalProperties"] = False
    tool: dict[str, Any] = {
        "name": spec.name,
        "description": spec.description,
        "input_schema": schema,
    }
    if is_strict_compatible(schema):
        tool["strict"] = True
    return tool


@dataclass
class McpSession:
    """One connected client for the duration of an agent run."""

    client: Client[Any]
    trace_id: str
    timeout_s: float

    async def list_tools(self) -> list[McpToolSpec]:
        tools = await self.client.list_tools()
        return [
            McpToolSpec(
                name=t.name, description=(t.description or "").strip(), input_schema=t.input_schema
            )
            for t in tools
        ]

    async def call(
        self, name: str, args: dict[str, Any], *, conversation_id: str | None = None
    ) -> ToolOutcome:
        started = time.perf_counter()
        result = await self.client.call_tool(
            name,
            args,
            timeout=self.timeout_s,
            raise_on_error=False,
            meta={"trace_id": self.trace_id, "conversation_id": conversation_id, "caller": "agent"},
        )
        duration = int((time.perf_counter() - started) * 1000)
        text = "".join(getattr(block, "text", "") for block in result.content)
        if result.is_error:
            error = _parse_envelope(text) or {
                "code": "tool_error",
                "message": text,
                "retryable": False,
            }
            rejected = error.get("code") == "validation_error"
            return ToolOutcome(
                status="rejected" if rejected else "error",
                text=text,
                error=error,
                duration_ms=duration,
            )
        structured = (
            result.structured_content if isinstance(result.structured_content, dict) else None
        )
        if structured is not None:
            text = json.dumps(structured, default=str)
        return ToolOutcome(status="ok", text=text, duration_ms=duration, structured=structured)


def _parse_envelope(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except (TypeError, ValueError):
        return None
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        error: dict[str, Any] = payload["error"]
        return error
    return None


class McpToolGateway:
    def __init__(
        self, factory: ClientFactory, *, timeout_s: float = 10.0, cache_ttl_s: float = 60.0
    ) -> None:
        self._factory = factory
        self.timeout_s = timeout_s
        self._cache_ttl = cache_ttl_s
        self._cached: tuple[float, list[McpToolSpec]] | None = None

    @asynccontextmanager
    async def session(self, trace_id: str) -> AsyncIterator[McpSession]:
        client = self._factory(trace_id)
        async with client:
            yield McpSession(client=client, trace_id=trace_id, timeout_s=self.timeout_s)

    async def cached_tools(self, session: McpSession) -> list[McpToolSpec]:
        now = time.monotonic()
        if self._cached and now - self._cached[0] < self._cache_ttl:
            return self._cached[1]
        specs = await session.list_tools()
        self._cached = (now, specs)
        return specs

    async def list_tools(self, trace_id: str = "meta") -> list[McpToolSpec]:
        async with self.session(trace_id) as session:
            return await self.cached_tools(session)
