#!/usr/bin/env sh
set -eu
exec uvicorn kpi_api.app:create_app --factory --host "${KPI_API_HOST:-0.0.0.0}" --port "${KPI_API_PORT:-8080}"
