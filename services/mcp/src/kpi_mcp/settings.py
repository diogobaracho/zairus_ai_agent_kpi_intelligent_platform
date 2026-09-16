"""MCP service settings (extends the shared KpiSettings)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from kpi_core.settings import KpiSettings


class McpSettings(KpiSettings):
    service_name: str = "kpi-mcp"
    mcp_transport: Literal["stdio", "http"] = "http"
    mcp_host: str = "0.0.0.0"  # noqa: S104 - container bind address; override with KPI_MCP_HOST
    mcp_port: int = 8090
    mcp_path: str = "/mcp"
    mcp_rate_limit_rps: float = Field(default=20.0, gt=0)
    mcp_rate_limit_burst: int = Field(default=40, ge=1)
    mcp_max_history_points: int = Field(default=64, ge=1, le=64)
    mcp_max_arg_chars: int = Field(default=256, ge=16)
