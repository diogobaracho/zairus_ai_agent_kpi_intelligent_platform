"""Server factory: tools + middleware chain + /healthz.

Middleware order (outermost first): rate limit → trace (binds RequestContext) → audit (records
every outcome, including sanitiser rejections) → sanitise → tool.
"""

from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from kpi_core.branding import get_brand
from kpi_core.db.engine import get_sessionmaker
from kpi_core.repositories.protocols import AuditRepository, KpiRepository
from kpi_core.repositories.sqlalchemy_repo import SqlAlchemyAuditRepository, SqlAlchemyKpiRepository
from kpi_mcp import __version__
from kpi_mcp.middleware.audit import AuditMiddleware
from kpi_mcp.middleware.sanitize import ArgSanitizingMiddleware
from kpi_mcp.middleware.trace import TraceMiddleware
from kpi_mcp.settings import McpSettings
from kpi_mcp.tools import register_tools

INSTRUCTIONS = """{provider} KPI estimates for public companies: quarterly historical estimates and
current quarter-to-date (QTD) snapshots. Typical flow: search_companies (find the ticker) ->
list_company_kpis (see what is published) -> get_kpi_history or get_kpi_qtd. Every error is a JSON
envelope with `code`, `message`, `suggestions` and `recovery_hint`; retry once with a suggestion
before telling the user. Always cite ticker, KPI, unit, period and (for QTD) the as_of date."""


def create_server(
    repo: KpiRepository,
    audit_repo: AuditRepository,
    settings: McpSettings | None = None,
) -> FastMCP:
    settings = settings or McpSettings()
    brand = get_brand()
    mcp = FastMCP(
        brand.mcp_server_name,
        instructions=INSTRUCTIONS.format(provider=brand.data_provider),
        version=__version__,
        mask_error_details=True,
    )
    allowed = register_tools(mcp, repo, settings)
    mcp.add_middleware(
        RateLimitingMiddleware(
            max_requests_per_second=settings.mcp_rate_limit_rps,
            burst_capacity=settings.mcp_rate_limit_burst,
        )
    )
    mcp.add_middleware(TraceMiddleware(settings))
    mcp.add_middleware(AuditMiddleware(audit_repo, settings))
    mcp.add_middleware(ArgSanitizingMiddleware(allowed, max_chars=settings.mcp_max_arg_chars))

    @mcp.custom_route("/healthz", methods=["GET"], include_in_schema=False)
    async def healthz(_: Request) -> JSONResponse:
        return JSONResponse(
            {"status": "ok", "service": settings.service_name, "version": __version__}
        )

    return mcp


def build_default_server(settings: McpSettings | None = None) -> FastMCP:
    """Postgres-backed server from environment settings (used by the entrypoints)."""
    settings = settings or McpSettings()
    sessions = get_sessionmaker(settings.database_url)
    return create_server(
        SqlAlchemyKpiRepository(sessions), SqlAlchemyAuditRepository(sessions), settings
    )
