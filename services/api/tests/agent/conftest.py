from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from kpi_api.agent.loop import AgentRunner
from kpi_api.agent.persistence import ConversationStore
from kpi_api.agent.providers.stub import StubLLMProvider, StubTurn
from kpi_api.agent.tools import McpToolGateway, inprocess_client_factory
from kpi_api.app import create_app
from kpi_api.settings import ApiSettings
from kpi_core.context import RequestContext
from kpi_core.repositories.memory import (
    InMemoryAuditRepository,
    InMemoryChatRepository,
    InMemoryKpiRepository,
)
from kpi_mcp.server import create_server
from kpi_mcp.settings import McpSettings


@pytest.fixture
def agent_settings() -> ApiSettings:
    return ApiSettings(env="test", mcp_mode="inprocess", rate_limit_rps=1000, rate_limit_burst=1000)


@pytest.fixture
def audit_repo() -> InMemoryAuditRepository:
    return InMemoryAuditRepository()


@pytest.fixture
def chat_repo() -> InMemoryChatRepository:
    return InMemoryChatRepository()


@pytest.fixture
def gateway(
    repo: InMemoryKpiRepository, audit_repo: InMemoryAuditRepository, agent_settings: ApiSettings
) -> McpToolGateway:
    server = create_server(
        repo,
        audit_repo,
        McpSettings(env="test", mcp_rate_limit_rps=1000, mcp_rate_limit_burst=1000),
    )
    return McpToolGateway(
        inprocess_client_factory(server), timeout_s=agent_settings.agent_tool_timeout_s
    )


@pytest.fixture
def ctx() -> RequestContext:
    return RequestContext(trace_id="agent-test-trace-01", caller="rest")


def make_runner(
    provider: StubLLMProvider,
    gateway: McpToolGateway,
    chat_repo: InMemoryChatRepository,
    settings: ApiSettings,
) -> AgentRunner:
    return AgentRunner(provider, gateway, ConversationStore(chat_repo), settings)


async def collect(
    runner: AgentRunner, ctx: RequestContext, text: str, conversation_id: str | None = None
) -> list[Any]:
    return [
        event async for event in runner.run(ctx, conversation_id=conversation_id, user_text=text)
    ]


def script(*turns: StubTurn) -> StubLLMProvider:
    return StubLLMProvider(list(turns))


def tool_call(name: str, **input: Any) -> dict[str, Any]:
    return {"name": name, "input": input}


@pytest.fixture
def agent_app(
    repo: InMemoryKpiRepository,
    audit_repo: InMemoryAuditRepository,
    chat_repo: InMemoryChatRepository,
    gateway: McpToolGateway,
    agent_settings: ApiSettings,
) -> FastAPI:
    return create_app(
        agent_settings,
        repo=repo,
        audit_repo=audit_repo,
        chat_repo=chat_repo,
        provider=StubLLMProvider(),
        mcp_gateway=gateway,
    )


@pytest.fixture
async def agent_client(agent_app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=agent_app), base_url="http://test"
    ) as client:
        yield client


def parse_sse(text: str) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    for block in re.split(r"\r?\n\r?\n", text):
        name, data = None, None
        for line in block.splitlines():
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                data = line[5:].strip()
        if name and data is not None:
            events.append((name, json.loads(data)))
    return events
