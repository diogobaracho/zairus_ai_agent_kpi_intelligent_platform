"""FastAPI dependencies: request context and repositories from app state."""

from __future__ import annotations

from fastapi import Request

from kpi_api.settings import ApiSettings
from kpi_core.context import RequestContext
from kpi_core.obs.correlation import get_trace_id
from kpi_core.repositories.protocols import AuditRepository, ChatRepository, KpiRepository


def get_settings_dep(request: Request) -> ApiSettings:
    settings: ApiSettings = request.app.state.settings
    return settings


def get_context(request: Request) -> RequestContext:
    """Server-built identity: never derived from request bodies or tool arguments."""
    settings: ApiSettings = request.app.state.settings
    return RequestContext(
        trace_id=get_trace_id() or request.scope.get("state", {}).get("trace_id", "-"),
        tenant_id=settings.default_tenant_id,
        caller="rest",
    )


def get_repo(request: Request) -> KpiRepository:
    repo: KpiRepository = request.app.state.repo
    return repo


def get_audit_repo(request: Request) -> AuditRepository:
    repo: AuditRepository = request.app.state.audit_repo
    return repo


def get_chat_repo(request: Request) -> ChatRepository:
    repo: ChatRepository = request.app.state.chat_repo
    return repo
