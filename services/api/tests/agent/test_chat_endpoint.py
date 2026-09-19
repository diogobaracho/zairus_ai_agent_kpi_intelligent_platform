from httpx import AsyncClient

from .conftest import parse_sse


async def test_chat_streams_events_and_persists(agent_client: AsyncClient) -> None:
    response = await agent_client.post(
        "/v1/chat", json={"message": "What is ORBY total revenue QTD?"}
    )
    assert response.status_code == 200 and response.headers["content-type"].startswith(
        "text/event-stream"
    )
    assert response.headers["x-accel-buffering"] == "no"
    events = parse_sse(response.text)
    names = [n for n, _ in events]
    assert names[0] == "session" and names[-1] == "final"
    assert (
        names.index("tool_call_started") < names.index("tool_call_finished") < names.index("final")
    )
    session = events[0][1]
    assert session["provider"] == "stub" and len(session["trace_id"]) == 16
    final = events[-1][1]
    assert final["steps"][0]["tool"] == "get_kpi_qtd" and final["stopped_reason"] == "end_turn"
    assert final["usage"]["tool_calls"] == 1 and "2026-09-15" in final["answer"]

    conv = (await agent_client.get(f"/v1/chat/conversations/{session['conversation_id']}")).json()
    assert [m["role"] for m in conv["messages"]] == ["user", "assistant"]
    assert (
        conv["messages"][1]["steps"][0]["status"] == "ok"
        and conv["messages"][1]["trace_id"] == session["trace_id"]
    )

    audit = (
        await agent_client.get("/v1/audit/tool-calls", params={"trace_id": session["trace_id"]})
    ).json()
    assert audit["items"][0]["tool_name"] == "get_kpi_qtd" and audit["items"][0]["status"] == "ok"
    listing = (await agent_client.get("/v1/chat/conversations")).json()
    assert listing["items"][0]["id"] == session["conversation_id"]


async def test_chat_recovery_visible_in_stream(agent_client: AsyncClient) -> None:
    response = await agent_client.post("/v1/chat", json={"message": "Show ORBYY revenue history"})
    finished = [d for n, d in parse_sse(response.text) if n == "tool_call_finished"]
    assert [f["status"] for f in finished] == ["error", "ok"]
    assert (
        finished[0]["error"]["code"] == "company_not_found"
        and finished[0]["error"]["suggestions"][0]["value"] == "ORBY"
    )


async def test_chat_continues_conversation_and_404(agent_client: AsyncClient) -> None:
    first = parse_sse(
        (await agent_client.post("/v1/chat", json={"message": "ORBY customers QTD"})).text
    )
    conv_id = first[0][1]["conversation_id"]
    second = parse_sse(
        (
            await agent_client.post(
                "/v1/chat", json={"message": "and churn history?", "conversation_id": conv_id}
            )
        ).text
    )
    assert second[0][1]["conversation_id"] == conv_id
    conv = (await agent_client.get(f"/v1/chat/conversations/{conv_id}")).json()
    assert len(conv["messages"]) == 4
    missing = await agent_client.post(
        "/v1/chat", json={"message": "hi", "conversation_id": "does-not-exist"}
    )
    assert missing.status_code == 404 and missing.json()["code"] == "conversation_not_found"
    assert (await agent_client.get("/v1/chat/conversations/nope")).status_code == 404


async def test_chat_validation(agent_client: AsyncClient) -> None:
    assert (await agent_client.post("/v1/chat", json={"message": ""})).status_code == 400
    assert (await agent_client.post("/v1/chat", json={"message": "x" * 4001})).status_code == 400
    assert (
        await agent_client.post("/v1/chat", json={"message": "x", "extra": 1})
    ).status_code == 400


async def test_meta_tools_lists_agent_view(agent_client: AsyncClient) -> None:
    body = (await agent_client.get("/v1/meta/tools")).json()
    assert {t["name"] for t in body["items"]} == {
        "search_companies",
        "list_company_kpis",
        "get_kpi_history",
        "get_kpi_qtd",
    }
    assert next(t for t in body["items"] if t["name"] == "get_kpi_qtd")["strict"] is True


async def test_audit_filters(agent_client: AsyncClient) -> None:
    await agent_client.post("/v1/chat", json={"message": "ORBYY revenue QTD"})
    errors = (await agent_client.get("/v1/audit/tool-calls", params={"status": "error"})).json()[
        "items"
    ]
    assert errors and errors[0]["error"]["code"] == "company_not_found"
    assert (
        await agent_client.get("/v1/audit/tool-calls", params={"status": "bogus"})
    ).status_code == 400
