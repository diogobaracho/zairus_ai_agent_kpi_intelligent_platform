"""Tool surface: exactly four read-only tools, LLM-friendly schemas, no identity parameters."""

import json
import os
from pathlib import Path

from fastmcp import Client

SNAPSHOT = Path(__file__).resolve().parents[3] / "docs" / "reference" / "mcp-tools.json"
EXPECTED = {"search_companies", "list_company_kpis", "get_kpi_history", "get_kpi_qtd"}
FORBIDDEN_PARAMS = {"tenant_id", "tenant", "principal", "user_id", "company_id", "kpi_id", "id"}


async def test_exactly_four_read_only_tools(client: Client) -> None:
    tools = await client.list_tools()
    assert {t.name for t in tools} == EXPECTED
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        assert (
            tool.annotations.idempotent_hint is True and tool.annotations.open_world_hint is False
        )
        assert tool.description and "Use" in tool.description
        props = tool.input_schema.get("properties", {})
        assert set(props).isdisjoint(FORBIDDEN_PARAMS)
        assert len(props) <= 5
        assert tool.input_schema.get("additionalProperties") is False
        assert tool.output_schema and "trace_id" in tool.output_schema.get("properties", {})


async def test_schema_snapshot_matches_docs(client: Client) -> None:
    tools = await client.list_tools()
    current = [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
            "output_schema": t.output_schema,
            "annotations": t.annotations.model_dump(exclude_none=True) if t.annotations else None,
        }
        for t in sorted(tools, key=lambda t: t.name)
    ]
    rendered = json.dumps(current, indent=2, sort_keys=True) + "\n"
    if os.environ.get("UPDATE_SNAPSHOTS") == "1" or not SNAPSHOT.exists():
        SNAPSHOT.write_text(rendered)
    assert rendered == SNAPSHOT.read_text(), (
        "tool schemas drifted from docs/reference/mcp-tools.json"
    )
