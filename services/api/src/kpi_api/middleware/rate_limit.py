"""Token-bucket rate limiting per client IP (in-process; see ADR-0010)."""

from __future__ import annotations

import json
import time
from collections.abc import MutableMapping
from typing import Any

from kpi_core.errors import RateLimited
from kpi_core.obs.correlation import ASGIApp, Receive, Scope, Send, get_trace_id


class TokenBucket:
    __slots__ = ("burst", "rate", "tokens", "updated")

    def __init__(self, rate: float, burst: int) -> None:
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.updated = time.monotonic()

    def take(self, now: float | None = None) -> tuple[bool, float]:
        now = time.monotonic() if now is None else now
        elapsed = max(0.0, now - self.updated)
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True, 0.0
        return False, (1 - self.tokens) / self.rate


class TokenBucketRateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        rate: float,
        burst: int,
        exempt_paths: tuple[str, ...] = ("/healthz", "/readyz"),
        max_clients: int = 10_000,
    ) -> None:
        self.app = app
        self.rate = rate
        self.burst = burst
        self.exempt = exempt_paths
        self.max_clients = max_clients
        self._buckets: dict[str, TokenBucket] = {}

    def _bucket(self, key: str) -> TokenBucket:
        bucket = self._buckets.get(key)
        if bucket is None:
            if len(self._buckets) >= self.max_clients:
                self._buckets.clear()
            bucket = self._buckets[key] = TokenBucket(self.rate, self.burst)
        return bucket

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") in self.exempt:
            await self.app(scope, receive, send)
            return
        client = scope.get("client") or ("unknown", 0)
        allowed, wait = self._bucket(str(client[0])).take()
        if allowed:
            await self.app(scope, receive, send)
            return
        retry_after = max(1, int(wait + 0.999))
        error = RateLimited(
            "Too many requests from this client",
            recovery_hint=f"Retry after {retry_after} seconds.",
            retry_after_seconds=retry_after,
        )
        body = json.dumps(
            error.to_problem(instance=scope.get("path"), trace_id=get_trace_id())
        ).encode()
        headers: list[tuple[bytes, bytes]] = [
            (b"content-type", b"application/problem+json"),
            (b"content-length", str(len(body)).encode()),
            (b"retry-after", str(retry_after).encode()),
        ]
        await send({"type": "http.response.start", "status": 429, "headers": headers})
        await send({"type": "http.response.body", "body": body})


def _unused(_: MutableMapping[str, Any]) -> None:  # pragma: no cover - keeps typing imports honest
    return None
