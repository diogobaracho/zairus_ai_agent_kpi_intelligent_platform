# KPI Intelligent Platform — single entry point. `make help` lists targets.
.DEFAULT_GOAL := help
SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

UV      ?= uv
PNPM    ?= corepack pnpm
COMPOSE ?= docker compose
ALL_PROFILES := --profile backend --profile chat --profile website
PY_UNIT_MARK := "not integration and not e2e and not live"

##@ General
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n"} \
	  /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } \
	  /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

##@ Setup
doctor: ## Check toolchain versions
	@bash scripts/doctor.sh

bootstrap: ## Install Python and JS workspaces
	$(UV) sync --all-packages
	corepack enable >/dev/null 2>&1 || true
	$(PNPM) install
	@$(MAKE) --no-print-directory doctor

##@ Stack (Docker Compose)
up: ## Start everything: postgres, migrate+seed, api, mcp, chat-web, website
	$(COMPOSE) $(ALL_PROFILES) up -d --build
	@bash scripts/wait_for_http.sh http://localhost:8080/readyz 90 || ($(COMPOSE) $(ALL_PROFILES) logs api migrate; exit 1)
	@echo "chat-web: http://localhost:3000  website: http://localhost:3001  api: http://localhost:8080/docs  mcp: http://localhost:8090/mcp"

up-backend: ## Start only postgres, migrate+seed, mcp and api
	$(COMPOSE) --profile backend up -d --build
	@bash scripts/wait_for_http.sh http://localhost:8080/readyz 90 || ($(COMPOSE) --profile backend logs api migrate; exit 1)

up-chat: ## Start the backend plus the chat web app
	$(COMPOSE) --profile backend --profile chat up -d --build

up-website: ## Start only the marketing website (no backend needed)
	$(COMPOSE) --profile website up -d --build
	@bash scripts/wait_for_http.sh http://localhost:3001/ 60
	@echo "website: http://localhost:3001"

down: ## Stop the stack
	$(COMPOSE) $(ALL_PROFILES) down

down-v: ## Stop the stack and delete volumes
	$(COMPOSE) $(ALL_PROFILES) down -v

logs: ## Tail stack logs
	$(COMPOSE) $(ALL_PROFILES) logs -f --tail=100

ps: ## Show stack status
	$(COMPOSE) $(ALL_PROFILES) ps

##@ Database
migrate: ## Run Alembic migrations against KPI_DATABASE_URL
	$(UV) run python -m kpi_core.cli migrate

seed: ## Load data/kpi_sample.csv (idempotent)
	$(UV) run python -m kpi_core.cli seed data/kpi_sample.csv

seed-demo: ## Load data/demo_edge_cases.csv edge-case companies (idempotent)
	$(UV) run python -m kpi_core.cli seed data/demo_edge_cases.csv

##@ Run services locally (no containers)
api: ## Run the API with reload on :8080
	$(UV) run uvicorn kpi_api.app:create_app --factory --reload --host 0.0.0.0 --port 8080

mcp-http: ## Run the MCP server over streamable HTTP on :8090
	$(UV) run python -m kpi_mcp --transport http

mcp-stdio: ## Run the MCP server over stdio (for desktop clients)
	$(UV) run python -m kpi_mcp --transport stdio

web: ## Run chat-web dev server on :5173
	$(PNPM) --filter chat-web dev

website: ## Run website dev server on :5174
	$(PNPM) --filter website dev

demo-chat: ## Stream one chat question over SSE (Q="...")
	@bash scripts/demo_chat.sh "$${Q:-What is ORBY total revenue QTD?}"

##@ Quality
lint: ## Ruff + eslint + prettier check
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(PNPM) -r --if-present lint
	$(PNPM) exec prettier --check "apps/**/*.{ts,tsx,css,json}" "tests/e2e/**/*.ts" || true

format: ## Format Python and TypeScript
	$(UV) run ruff format .
	$(UV) run ruff check --fix .
	$(PNPM) exec prettier --write "apps/**/*.{ts,tsx,css,json}" "tests/e2e/**/*.ts" || true

typecheck: ## mypy strict + tsc
	$(UV) run mypy .
	$(PNPM) -r --if-present typecheck

test: ## Fast suite: Python unit tests with coverage gate + JS unit tests
	$(UV) run pytest -m $(PY_UNIT_MARK) --cov --cov-report=term-missing
	$(PNPM) -r --if-present test

test-integration: ## Postgres-backed tests (testcontainers or KPI_TEST_DATABASE_URL)
	$(UV) run pytest -m integration

sample-data: ## Regenerate the synthetic CSVs in data/ (deterministic)
	python3 scripts/generate_sample_data.py

test-e2e: ## Playwright + smoke against the compose stack (stub LLM)
	$(COMPOSE) $(ALL_PROFILES) up -d --build
	@bash scripts/wait_for_http.sh http://localhost:8080/readyz 120
	$(PNPM) --filter e2e test:e2e
	$(UV) run pytest -m e2e

perf-smoke: ## P95 latency check against the running stack
	$(UV) run python scripts/perf_smoke.py

docs-check: ## Doc links, raw-SQL gate, hard-coded brand check, sample-data drift, tool-doc drift
	python3 scripts/check_doc_links.py
	python3 scripts/audit_docs.py
	python3 scripts/generate_sample_data.py --check
	@test -f scripts/check_tool_docs.py && $(UV) run python scripts/check_tool_docs.py || true

tool-docs: ## Regenerate docs/reference/mcp-tools.json from the server
	$(UV) run python scripts/check_tool_docs.py --update

ci: lint typecheck test docs-check ## Everything CI runs, in CI's order

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

.PHONY: help doctor bootstrap up up-backend up-chat up-website sample-data down down-v logs ps migrate seed seed-demo api mcp-http mcp-stdio web website demo-chat lint format typecheck test test-integration test-e2e perf-smoke docs-check tool-docs ci clean
