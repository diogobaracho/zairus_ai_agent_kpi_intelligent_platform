#!/usr/bin/env sh
set -eu
exec python -m kpi_mcp --transport "${KPI_MCP_TRANSPORT:-http}"
