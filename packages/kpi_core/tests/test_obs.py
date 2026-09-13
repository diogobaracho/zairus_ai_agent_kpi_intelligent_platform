import json
import logging

import pytest

from kpi_core.obs.correlation import (
    CorrelationIdMiddleware,
    coerce_trace_id,
    correlation_headers,
    get_trace_id,
)
from kpi_core.obs.logging import configure_logging, log_event, redact
from kpi_core.obs.timing import RequestTimingMiddleware


def test_coerce_trace_id() -> None:
    assert coerce_trace_id("abcdef1234567890") == "abcdef1234567890"
    assert coerce_trace_id("bad id!") != "bad id!"
    assert len(coerce_trace_id(None)) == 16


async def test_middleware_adopts_and_echoes() -> None:
    seen: dict[str, str | None] = {}
    sent: list[dict] = []  # type: ignore[type-arg]

    async def app(scope, receive, send):  # type: ignore[no-untyped-def]
        seen["inside"] = get_trace_id()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def send(message):  # type: ignore[no-untyped-def]
        sent.append(message)

    async def receive():  # type: ignore[no-untyped-def]
        return {"type": "http.request"}

    mw = RequestTimingMiddleware(CorrelationIdMiddleware(app))
    scope = {
        "type": "http",
        "headers": [(b"x-correlation-id", b"client-trace-01")],
        "method": "GET",
        "path": "/x",
    }
    await mw(scope, receive, send)
    assert seen["inside"] == "client-trace-01"
    assert (b"x-correlation-id", b"client-trace-01") in sent[0]["headers"]
    assert get_trace_id() is None  # reset after the request
    await mw({"type": "lifespan"}, receive, send)  # passthrough


def test_redact_and_log_event(capsys: pytest.CaptureFixture[str]) -> None:
    assert redact({"api_key": "x", "nested": {"password": "y", "ok": 1}}) == {
        "api_key": "***",
        "nested": {"password": "***", "ok": 1},
    }
    configure_logging("kpi-test", "INFO")
    configure_logging("kpi-test", "INFO")  # idempotent
    root = logging.getLogger()
    handlers = [h for h in root.handlers if getattr(h, "_kpi_json_handler", False)]
    assert len(handlers) == 1
    log_event("tool_call", tool_name="get_kpi_qtd", anthropic_api_key="secret")
    err = capsys.readouterr().err.strip().splitlines()[-1]
    payload = json.loads(err)
    assert payload["event"] == "tool_call" and payload["anthropic_api_key"] == "***"
    assert payload["trace_id"] == "-" and payload["service"] == "kpi-test"
    assert correlation_headers() == {}
