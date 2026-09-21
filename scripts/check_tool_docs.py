#!/usr/bin/env python3
"""Keep docs/reference/mcp-tools.json in sync with the server's tools/list output.

uv run python scripts/check_tool_docs.py            # fail if drifted
uv run python scripts/check_tool_docs.py --update   # rewrite the snapshot
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from fastmcp import Client

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = REPO_ROOT / "docs" / "reference" / "mcp-tools.json"


async def current_tools() -> str:
    from kpi_core.repositories.memory import InMemoryAuditRepository, InMemoryKpiRepository
    from kpi_mcp.server import create_server
    from kpi_mcp.settings import McpSettings

    repo = InMemoryKpiRepository.from_csv(REPO_ROOT / "data" / "kpi_sample.csv")
    async with Client(
        create_server(repo, InMemoryAuditRepository(), McpSettings(env="test"))
    ) as client:
        tools = await client.list_tools()
    payload = [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
            "output_schema": t.output_schema,
            "annotations": t.annotations.model_dump(exclude_none=True) if t.annotations else None,
        }
        for t in sorted(tools, key=lambda t: t.name)
    ]
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main(argv: list[str]) -> int:
    rendered = asyncio.run(current_tools())
    if "--update" in argv or not SNAPSHOT.exists():
        SNAPSHOT.write_text(rendered)
        print(f"wrote {SNAPSHOT.relative_to(REPO_ROOT)}")
        return 0
    if rendered != SNAPSHOT.read_text():
        print(
            f"FAIL: {SNAPSHOT.relative_to(REPO_ROOT)} is out of date; run with --update and review"
        )
        return 1
    print("OK: MCP tool docs match the server")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
