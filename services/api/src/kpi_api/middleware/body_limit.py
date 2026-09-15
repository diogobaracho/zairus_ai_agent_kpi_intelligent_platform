"""Reject request bodies above a byte cap with a 413 problem document."""

from __future__ import annotations

import json
from collections.abc import MutableMapping
from typing import Any

from kpi_core.errors import PayloadTooLarge
from kpi_core.obs.correlation import ASGIApp, Receive, Scope, Send, get_trace_id


class MaxBodySizeMiddleware:
    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def _reject(self, scope: Scope, send: Send) -> None:
        error = PayloadTooLarge(
            f"Request body exceeds {self.max_bytes} bytes",
            recovery_hint=f"Send at most {self.max_bytes} bytes.",
        )
        body = json.dumps(
            error.to_problem(instance=scope.get("path"), trace_id=get_trace_id())
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/problem+json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        for key, value in scope.get("headers", []):
            if key == b"content-length":
                try:
                    if int(value) > self.max_bytes:
                        await self._reject(scope, send)
                        return
                except ValueError:
                    break
        received = 0
        rejected = False

        async def counting_receive() -> MutableMapping[str, Any]:
            nonlocal received, rejected
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    rejected = True
                    raise PayloadTooLarge(f"Request body exceeds {self.max_bytes} bytes")
            return message

        try:
            await self.app(scope, counting_receive, send)
        except PayloadTooLarge:
            if rejected:
                await self._reject(scope, send)
            else:
                raise
