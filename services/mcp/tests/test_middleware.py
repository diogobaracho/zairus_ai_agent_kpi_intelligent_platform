import json

from fastmcp import Client

from kpi_core.repositories.memory import InMemoryAuditRepository, InMemoryKpiRepository
from kpi_mcp.server import create_server
from kpi_mcp.settings import McpSettings


async def test_audit_row_per_call_with_trace_from_meta(
    client: Client, audit_repo: InMemoryAuditRepository
) -> None:
    await client.call_tool(
        "get_kpi_qtd",
        {"ticker": "ORBY", "kpi": "revenue"},
        meta={"trace_id": "agent-trace-0001", "conversation_id": "conv1", "caller": "agent"},
    )
    await client.call_tool(
        "get_kpi_qtd", {"ticker": "ORBYY", "kpi": "revenue"}, raise_on_error=False
    )
    ok, err = audit_repo.rows
    assert ok.tool_name == "get_kpi_qtd" and ok.status == "ok" and ok.trace_id == "agent-trace-0001"
    assert ok.arguments == {"ticker": "ORBY", "kpi": "revenue"} and ok.duration_ms >= 0
    assert (
        ok.conversation_id == "conv1"
        and ok.caller == "agent"
        and "latest_as_of=2026-09-15" in (ok.result_summary or "")
    )
    assert (
        err.status == "error" and err.error is not None and err.error["code"] == "company_not_found"
    )
    assert len(err.trace_id) == 16 and err.trace_id != ok.trace_id  # minted when no meta/header


async def test_result_carries_same_trace_id(
    client: Client, audit_repo: InMemoryAuditRepository
) -> None:
    result = await client.call_tool(
        "search_companies", {"query": "ORBY"}, meta={"trace_id": "trace-xyz-0002"}
    )
    assert (
        result.structured_content is not None
        and result.structured_content["trace_id"] == "trace-xyz-0002"
    )
    assert audit_repo.rows[-1].trace_id == "trace-xyz-0002"


async def test_sanitizer_rejects_unknown_and_oversized(
    client: Client, audit_repo: InMemoryAuditRepository
) -> None:
    result = await client.call_tool(
        "get_kpi_qtd", {"ticker": "ORBY", "kpi": "revenue", "tenant_id": "x"}, raise_on_error=False
    )
    err = json.loads(result.content[0].text)["error"]  # type: ignore[union-attr]
    assert result.is_error and err["code"] == "validation_error" and "tenant_id" in err["message"]
    assert audit_repo.rows[-1].status == "rejected"
    result = await client.call_tool(
        "get_kpi_qtd", {"ticker": "A" * 300, "kpi": "revenue"}, raise_on_error=False
    )
    err = json.loads(result.content[0].text)["error"]  # type: ignore[union-attr]
    assert err["code"] == "validation_error" and "too long" in err["message"]
    result = await client.call_tool(
        "get_kpi_qtd", {"ticker": "IG\x00C", "kpi": "revenue"}, raise_on_error=False
    )
    assert "control characters" in json.loads(result.content[0].text)["error"]["message"]  # type: ignore[union-attr]
    result = await client.call_tool(
        "get_kpi_qtd", {"ticker": ["ORBY"], "kpi": "revenue"}, raise_on_error=False
    )
    assert "scalar" in json.loads(result.content[0].text)["error"]["recovery_hint"]  # type: ignore[union-attr]


async def test_sanitizer_strips_whitespace(client: Client) -> None:
    data = (
        await client.call_tool("get_kpi_qtd", {"ticker": "  orby ", "kpi": " revenue "})
    ).structured_content
    assert data is not None and data["company"]["ticker"] == "ORBY"


async def test_rate_limit(repo: InMemoryKpiRepository) -> None:
    from mcp.shared.exceptions import MCPError

    settings = McpSettings(env="test", mcp_rate_limit_rps=1, mcp_rate_limit_burst=3)
    server = create_server(repo, InMemoryAuditRepository(), settings)
    limited = 0
    async with Client(server) as client:
        for _ in range(6):
            try:
                await client.call_tool("search_companies", {"query": "ORBY"}, raise_on_error=False)
            except (
                MCPError
            ) as exc:  # the limiter answers at the protocol level, not as a tool error
                assert "Rate limit" in str(exc)
                limited += 1
    assert 1 <= limited <= 5  # initialize/list requests also consume tokens


async def test_healthz_route(server) -> None:  # type: ignore[no-untyped-def]
    from httpx import ASGITransport, AsyncClient

    app = server.http_app(path="/mcp")
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            response = await http.get("/healthz")
    assert response.status_code == 200 and response.json()["status"] == "ok"
