"""HTTP (header trace propagation into Postgres audit rows) and stdio (subprocess) transports."""

import asyncio
import os
import socket
from pathlib import Path

import pytest
import uvicorn
from fastmcp import Client
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kpi_core.repositories.sqlalchemy_repo import SqlAlchemyAuditRepository, SqlAlchemyKpiRepository
from kpi_mcp.server import create_server
from kpi_mcp.settings import McpSettings

pytestmark = pytest.mark.integration
REPO_ROOT = Path(__file__).resolve().parents[4]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


async def test_http_transport_header_reaches_audit(
    sql_sessions: async_sessionmaker[AsyncSession],
) -> None:
    settings = McpSettings(env="test", mcp_transport="http")
    server = create_server(
        SqlAlchemyKpiRepository(sql_sessions), SqlAlchemyAuditRepository(sql_sessions), settings
    )
    app = server.http_app(path="/mcp")
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    uv_server = uvicorn.Server(config)
    # Serve on the test's own event loop: asyncpg connections are loop-bound, and a server
    # thread with a second loop would reuse the cached engine from the wrong loop.
    serve_task = asyncio.create_task(uv_server.serve())
    for _ in range(50):
        if uv_server.started:
            break
        await asyncio.sleep(0.1)
    try:
        transport = StreamableHttpTransport(
            url=f"http://127.0.0.1:{port}/mcp", headers={"X-Correlation-Id": "http-trace-0001"}
        )
        async with Client(transport) as client:
            tools = await client.list_tools()
            assert len(tools) == 4
            result = await client.call_tool("get_kpi_qtd", {"ticker": "ORBY", "kpi": "revenue"})
            assert result.structured_content is not None
            assert result.structured_content["trace_id"] == "http-trace-0001"
        rows = await SqlAlchemyAuditRepository(sql_sessions).query(
            tenant_id="default", trace_id="http-trace-0001"
        )
        assert rows and rows[0].tool_name == "get_kpi_qtd" and rows[0].status == "ok"
        assert rows[0].transport in ("http", "streamable-http")
    finally:
        uv_server.should_exit = True
        await asyncio.wait_for(serve_task, timeout=10)


async def test_stdio_transport_lists_tools(migrated_database_url: str) -> None:
    env = {**os.environ, "KPI_DATABASE_URL": migrated_database_url, "KPI_LOG_LEVEL": "WARNING"}
    transport = StdioTransport(
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
        env=env,
        cwd=str(REPO_ROOT),
    )
    async with Client(transport) as client:
        tools = await client.list_tools()
        assert {t.name for t in tools} == {
            "search_companies",
            "list_company_kpis",
            "get_kpi_history",
            "get_kpi_qtd",
        }
        result = await client.call_tool("search_companies", {"query": "ORBY"})
        assert result.structured_content is not None and result.structured_content["total"] == 1
