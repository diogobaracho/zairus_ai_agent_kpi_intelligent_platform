"""Per-request timing as a structured `http_request` event (pure ASGI)."""

from __future__ import annotations

import time
from collections.abc import MutableMapping
from typing import Any

from kpi_core.obs.correlation import ASGIApp, Receive, Scope, Send
from kpi_core.obs.logging import log_event


class RequestTimingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = time.perf_counter()
        status_holder = {"status": 0}

        async def send_capture(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = int(message.get("status", 0))
            await send(message)

        try:
            await self.app(scope, receive, send_capture)
        finally:
            client = scope.get("client") or ("-", 0)
            log_event(
                "http_request",
                method=scope.get("method"),
                path=scope.get("path"),
                status=status_holder["status"],
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
                client_ip=client[0],
            )
