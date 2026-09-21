#!/usr/bin/env sh
# One-shot: apply migrations and load the sample dataset (idempotent). Demo data is opt-in.
set -eu
python -m kpi_core.cli migrate
python -m kpi_core.cli seed /app/data/kpi_sample.csv
if [ "${KPI_SEED_DEMO:-false}" = "true" ]; then python -m kpi_core.cli seed /app/data/demo_edge_cases.csv; fi
