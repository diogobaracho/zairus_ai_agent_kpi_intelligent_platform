"""Stack smoke against the running compose stack: readiness, one SSE run, audit row by trace id."""

from __future__ import annotations

import json
import os

import httpx
import pytest

pytestmark = pytest.mark.e2e
API = os.environ.get("KPI_API_URL", "http://localhost:8080")
MCP = os.environ.get("KPI_MCP_HEALTH_URL", "http://localhost:8090/healthz")


def _sse_events(text: str) -> list[tuple[str, dict]]:  # type: ignore[type-arg]
    events = []
    for block in text.replace("\r\n", "\n").split("\n\n"):
        name, data = None, None
        for line in block.splitlines():
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                data = line[5:].strip()
        if name and data:
            events.append((name, json.loads(data)))
    return events


def test_readiness() -> None:
    ready = httpx.get(f"{API}/readyz", timeout=10).json()
    assert ready["checks"]["db"] == "ok" and ready["checks"]["mcp"] == "ok"
    assert httpx.get(MCP, timeout=10).json()["status"] == "ok"


def test_chat_flow_end_to_end() -> None:
    with httpx.stream(
        "POST",
        f"{API}/v1/chat",
        json={"message": "What is ORBY total revenue QTD?"},
        headers={"accept": "text/event-stream"},
        timeout=60,
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())
    events = _sse_events(body)
    names = [n for n, _ in events]
    assert names[0] == "session" and names[-1] == "final"
    assert "tool_call_started" in names and "tool_call_finished" in names
    session = events[0][1]
    final = events[-1][1]
    assert final["steps"][0]["tool"] == "get_kpi_qtd" and "2026-09-15" in final["answer"]

    audit = httpx.get(
        f"{API}/v1/audit/tool-calls", params={"trace_id": session["trace_id"]}, timeout=10
    ).json()
    assert audit["items"] and audit["items"][0]["tool_name"] == "get_kpi_qtd"
    conv = httpx.get(f"{API}/v1/chat/conversations/{session['conversation_id']}", timeout=10).json()
    assert conv["messages"][-1]["trace_id"] == session["trace_id"]
