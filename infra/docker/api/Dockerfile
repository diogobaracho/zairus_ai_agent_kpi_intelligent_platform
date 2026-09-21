# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
RUN pip install --no-cache-dir uv==0.12.5
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages/kpi_core/pyproject.toml packages/kpi_core/pyproject.toml
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY services/mcp/pyproject.toml services/mcp/pyproject.toml
RUN uv sync --frozen --no-dev --no-install-workspace --package kpi-api
COPY packages packages
COPY services services
RUN uv sync --frozen --no-dev --package kpi-api

FROM python:3.12-slim AS runtime
RUN groupadd --system kpi && useradd --system --gid kpi --home /app kpi
WORKDIR /app
COPY --from=builder --chown=kpi:kpi /app/.venv /app/.venv
COPY --from=builder --chown=kpi:kpi /app/packages /app/packages
COPY --from=builder --chown=kpi:kpi /app/services /app/services
COPY --chown=kpi:kpi data /app/data
COPY --chown=kpi:kpi infra/docker/api/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER kpi
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz', timeout=2)" || exit 1
CMD ["/app/entrypoint.sh"]
