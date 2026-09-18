from kpi_api.agent.tools import McpToolGateway, is_strict_compatible, to_anthropic_tool
from kpi_api.agent.types import McpToolSpec


async def test_real_tools_convert_for_anthropic(gateway: McpToolGateway) -> None:
    specs = await gateway.list_tools("t")
    tools = {t["name"]: t for t in (to_anthropic_tool(s) for s in specs)}
    assert set(tools) == {"search_companies", "list_company_kpis", "get_kpi_history", "get_kpi_qtd"}
    for tool in tools.values():
        assert tool["input_schema"]["additionalProperties"] is False and tool["description"]
        assert "tenant_id" not in tool["input_schema"]["properties"]
    assert (
        tools["list_company_kpis"].get("strict") is True
        and tools["get_kpi_qtd"].get("strict") is True
    )
    assert "strict" not in tools["search_companies"]  # optional params -> not fully required


def test_strict_compatibility_rules() -> None:
    assert is_strict_compatible(
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {"a": {}},
            "required": ["a"],
        }
    )
    assert not is_strict_compatible({"type": "object", "properties": {"a": {}}, "required": ["a"]})
    assert not is_strict_compatible(
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {"a": {}, "b": {}},
            "required": ["a"],
        }
    )
    spec = McpToolSpec("x", "d", {"properties": {"a": {"type": "string"}}, "required": ["a"]})
    converted = to_anthropic_tool(spec)
    assert converted["input_schema"]["type"] == "object" and converted["strict"] is True


async def test_gateway_caches_tool_list(gateway: McpToolGateway) -> None:
    first = await gateway.list_tools("a")
    second = await gateway.list_tools("b")
    assert first is second
