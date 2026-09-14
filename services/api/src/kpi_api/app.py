"""FastAPI application factory.

Middleware order (outermost first): correlation id → timing → body limit → rate limit → CORS →
routers. Repositories are injected so tests run on in-memory implementations.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from kpi_api import __version__
from kpi_api.agent.loop import AgentRunner
from kpi_api.agent.persistence import ConversationStore
from kpi_api.agent.providers import get_provider
from kpi_api.agent.providers.base import LLMProvider
from kpi_api.agent.tools import McpToolGateway, http_client_factory, inprocess_client_factory
from kpi_api.errors import install_exception_handlers
from kpi_api.middleware.body_limit import MaxBodySizeMiddleware
from kpi_api.middleware.rate_limit import TokenBucketRateLimitMiddleware
from kpi_api.routers import audit, chat, companies, estimates, health, kpis, meta, sectors
from kpi_api.settings import ApiSettings
from kpi_core.db.engine import dispose_engines, get_sessionmaker
from kpi_core.obs.correlation import CorrelationIdMiddleware
from kpi_core.obs.logging import configure_logging
from kpi_core.obs.telemetry import configure_telemetry
from kpi_core.obs.timing import RequestTimingMiddleware
from kpi_core.repositories.protocols import AuditRepository, ChatRepository, KpiRepository
from kpi_core.repositories.sqlalchemy_repo import (
    SqlAlchemyAuditRepository,
    SqlAlchemyChatRepository,
    SqlAlchemyKpiRepository,
)

PingDb = Callable[[], Awaitable[None]]


async def _ping_ok() -> None:
    return None


def create_app(
    settings: ApiSettings | None = None,
    *,
    repo: KpiRepository | None = None,
    audit_repo: AuditRepository | None = None,
    chat_repo: ChatRepository | None = None,
    ping_db: PingDb | None = None,
    provider: LLMProvider | None = None,
    mcp_gateway: McpToolGateway | None = None,
) -> FastAPI:
    settings = settings or ApiSettings()

    if repo is None or audit_repo is None or chat_repo is None:
        sessions = get_sessionmaker(settings.database_url)
        repo = repo or SqlAlchemyKpiRepository(sessions)
        audit_repo = audit_repo or SqlAlchemyAuditRepository(sessions)
        chat_repo = chat_repo or SqlAlchemyChatRepository(sessions)

        async def _ping_db() -> None:
            async with sessions() as session:
                (await session.execute(select(1))).scalar_one()

        ping_db = ping_db or _ping_db

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(settings.service_name, settings.log_level)
        yield
        await dispose_engines()

    app = FastAPI(
        title="Zairus KPI Intelligent Platform API",
        version=__version__,
        description="REST access to ZairusData KPI estimates and the explainable chat agent.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.repo = repo
    app.state.audit_repo = audit_repo
    app.state.chat_repo = chat_repo
    app.state.ping_db = ping_db or _ping_ok

    if mcp_gateway is None:
        mcp_gateway = build_gateway(settings, repo, audit_repo)
    provider = provider or get_provider(settings)
    app.state.mcp_gateway = mcp_gateway
    app.state.provider = provider
    app.state.agent_runner = AgentRunner(
        provider, mcp_gateway, ConversationStore(chat_repo), settings
    )

    install_exception_handlers(app)
    for router in (
        health.router, sectors.router, companies.router, kpis.router, estimates.router,
        chat.router, audit.router, meta.router,
    ):  # fmt: skip
        app.include_router(router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=[settings.correlation_header],
    )
    app.add_middleware(
        TokenBucketRateLimitMiddleware,
        rate=settings.rate_limit_rps,
        burst=settings.rate_limit_burst,
    )
    app.add_middleware(MaxBodySizeMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(CorrelationIdMiddleware, header=settings.correlation_header)
    configure_telemetry(settings.service_name, app=app)
    return app


def build_gateway(
    settings: ApiSettings, repo: KpiRepository, audit_repo: AuditRepository
) -> McpToolGateway:
    """HTTP to the MCP service (default) or an in-process server sharing this API's repositories."""
    if settings.mcp_mode == "inprocess":
        from kpi_mcp.server import create_server
        from kpi_mcp.settings import McpSettings

        server = create_server(
            repo,
            audit_repo,
            McpSettings(env=settings.env, database_url=settings.database_url, mcp_transport="http"),
        )
        factory = inprocess_client_factory(server)
    else:
        factory = http_client_factory(settings.mcp_url, settings.correlation_header)
    return McpToolGateway(factory, timeout_s=settings.agent_tool_timeout_s)


def app_state(app: FastAPI) -> dict[str, Any]:  # pragma: no cover - debugging helper
    return dict(vars(app.state))
