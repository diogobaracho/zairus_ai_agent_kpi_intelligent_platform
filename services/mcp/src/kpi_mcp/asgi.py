"""ASGI entrypoint: `uvicorn kpi_mcp.asgi:app --port 8090` serves /mcp and /healthz."""

from __future__ import annotations

from kpi_core.obs.logging import configure_logging
from kpi_mcp.server import build_default_server
from kpi_mcp.settings import McpSettings

settings = McpSettings()
configure_logging(settings.service_name, settings.log_level)
mcp = build_default_server(settings)
app = mcp.http_app(path=settings.mcp_path)
