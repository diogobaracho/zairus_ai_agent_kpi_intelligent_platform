"""Correlation-id (trace_id) propagation.

One id, generated at whichever edge sees a request first, attached to every log line, echoed on
every response, forwarded on every outbound call, and recorded on every error body and audit row.
Stored in a ContextVar so it follows the async task. The middleware is pure ASGI on purpose:
Starlette's `BaseHTTPMiddleware` breaks ContextVar propagation into the endpoint.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, MutableMapping
from contextvars import ContextVar
from typing import Any

from kpi_core.context import new_trace_id

DEFAULT_HEADER = "X-Correlation-Id"
_VALID_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

_trace_id: ContextVar[str | None] = ContextVar("kpi_trace_id", default=None)

Scope = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


def get_trace_id() -> str | None:
    return _trace_id.get()


def set_trace_id(value: str | None) -> None:
    _trace_id.set(value)


def coerce_trace_id(incoming: str | None) -> str:
    """Adopt a well-formed client id, otherwise mint one. Never used for authorisation."""
    if incoming and _VALID_ID.match(incoming):
        return incoming
    return new_trace_id()


class CorrelationIdMiddleware:
    """Adopts or mints a trace id per HTTP request and echoes it back."""

    def __init__(self, app: ASGIApp, header: str = DEFAULT_HEADER) -> None:
        self.app = app
        self.header = header
        self._header_bytes = header.lower().encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        incoming: str | None = None
        for key, value in scope.get("headers", []):
            if key == self._header_bytes:
                incoming = value.decode("latin-1")
                break
        trace_id = coerce_trace_id(incoming)
        scope.setdefault("state", {})["trace_id"] = trace_id
        token = _trace_id.set(trace_id)

        async def send_with_header(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((self._header_bytes, trace_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        finally:
            _trace_id.reset(token)


def correlation_headers(header: str = DEFAULT_HEADER) -> dict[str, str]:
    """Headers for an outbound call so the id survives the hop."""
    current = get_trace_id()
    return {header: current} if current else {}
