#!/usr/bin/env python3
"""Exercise the MCP server from the command line (HTTP, stdio or in-memory).

Examples:
  uv run python scripts/mcp_smoke.py --list
  uv run python scripts/mcp_smoke.py --list --descriptions
  uv run python scripts/mcp_smoke.py --schema get_kpi_history
  uv run python scripts/mcp_smoke.py --tool get_kpi_qtd --args '{"ticker":"ORBY","kpi":"revenue"}'
  uv run python scripts/mcp_smoke.py --stdio --list
  uv run python scripts/mcp_smoke.py --memory --tool search_companies --args '{"query":"orbit"}'
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport

REPO_ROOT = Path(__file__).resolve().parent.parent


def build_client(args: argparse.Namespace) -> Client:  # type: ignore[type-arg]
    if args.memory:
        from kpi_core.repositories.memory import InMemoryAuditRepository, InMemoryKpiRepository
        from kpi_mcp.server import create_server
        from kpi_mcp.settings import McpSettings

        repo = InMemoryKpiRepository.from_csv(
            REPO_ROOT / "data" / "kpi_sample.csv", REPO_ROOT / "data" / "demo_edge_cases.csv"
        )
        return Client(create_server(repo, InMemoryAuditRepository(), McpSettings(env="test")))
    if args.stdio:
        return Client(
            StdioTransport(
                command="uv",
                args=[
                    "run",
                    "--project",
                    "services/mcp",
                    "python",
                    "-m",
                    "kpi_mcp",
                    "--transport",
                    "stdio",
                ],
                env=dict(os.environ),
                cwd=str(REPO_ROOT),
            )
        )
    headers = {"X-Correlation-Id": args.trace_id} if args.trace_id else None
    return Client(StreamableHttpTransport(url=args.url, headers=headers))


async def run(args: argparse.Namespace) -> int:
    async with build_client(args) as client:
        if args.list or args.schema:
            tools = await client.list_tools()
            for tool in sorted(tools, key=lambda t: t.name):
                if args.schema and tool.name != args.schema:
                    continue
                print(
                    f"- {tool.name}  params={sorted(tool.input_schema.get('properties', {}))}  "
                    f"read_only={tool.annotations.read_only_hint if tool.annotations else None}"
                )
                if args.descriptions:
                    print("    " + (tool.description or "").strip().replace("\n", "\n    "))
                if args.schema:
                    print(json.dumps(tool.input_schema, indent=2))
            if not args.tool:
                return 0
        if args.tool:
            arguments = json.loads(args.args or "{}")
            meta = {"trace_id": args.trace_id} if args.trace_id else None
            result = await client.call_tool(args.tool, arguments, raise_on_error=False, meta=meta)
            if result.is_error:
                text = result.content[0].text if result.content else ""
                print("isError: true")
                try:
                    print(json.dumps(json.loads(text), indent=2))
                except ValueError:
                    print(text)
                return 2
            print(json.dumps(result.structured_content, indent=2, default=str))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--url", default=os.environ.get("KPI_MCP_URL", "http://localhost:8090/mcp"))
    parser.add_argument("--stdio", action="store_true", help="spawn the server over stdio")
    parser.add_argument(
        "--memory", action="store_true", help="in-process server over the CSV files (no DB)"
    )
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--descriptions", action="store_true")
    parser.add_argument("--schema", metavar="TOOL")
    parser.add_argument("--tool", metavar="TOOL")
    parser.add_argument("--args", metavar="JSON")
    parser.add_argument("--trace-id", metavar="ID")
    args = parser.parse_args()
    if not (args.list or args.schema or args.tool):
        parser.error("choose --list, --schema TOOL or --tool TOOL")
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
