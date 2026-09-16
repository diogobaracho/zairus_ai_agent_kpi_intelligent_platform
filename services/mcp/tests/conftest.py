from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastmcp import Client, FastMCP

from kpi_core.repositories.memory import InMemoryAuditRepository, InMemoryKpiRepository
from kpi_mcp.server import create_server
from kpi_mcp.settings import McpSettings


@pytest.fixture(scope="session")
def repo(sample_csv_path: Path, edge_cases_csv_path: Path) -> InMemoryKpiRepository:
    return InMemoryKpiRepository.from_csv(sample_csv_path, edge_cases_csv_path)


@pytest.fixture
def audit_repo() -> InMemoryAuditRepository:
    return InMemoryAuditRepository()


@pytest.fixture
def settings() -> McpSettings:
    return McpSettings(env="test", mcp_rate_limit_rps=1000, mcp_rate_limit_burst=1000)


@pytest.fixture
def server(
    repo: InMemoryKpiRepository, audit_repo: InMemoryAuditRepository, settings: McpSettings
) -> FastMCP:
    return create_server(repo, audit_repo, settings)


@pytest.fixture
async def client(server: FastMCP) -> AsyncIterator[Client]:
    async with Client(server) as client:
        yield client
