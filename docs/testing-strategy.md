# Testing strategy

Principle: the fast suite needs nothing running; everything with I/O has a real-integration test;
every claim in the docs has a test or a command that reproduces it.

| Layer | Marker | Tool | Needs | Covers |
|---|---|---|---|---|
| Unit: kpi_core logic + services | (none) | pytest, `InMemoryKpiRepository.from_csv` | nothing | periods, validation, fuzzy suggestions + aliases, error mapping, search/list/history/QTD semantics, empty datasets, CSV loader |
| Unit: repository contract | (none) / `integration` | `tests/repo_contract.py` parametrised over memory and SQL repos | Postgres for the SQL half | both repos return identical results for a fixed query set |
| Unit: API | (none) | httpx `AsyncClient(ASGITransport)` + fake repos | nothing | every route, problem+json shapes, correlation echo, rate limit, body limit, OpenAPI snapshot |
| Unit: MCP tools | (none) | `fastmcp.Client(server)` in-memory | nothing | 4 tools, envelope for bad ticker/KPI/period, empty range, sanitiser, audit rows (in-memory audit repo), rate limit, tool-list snapshot |
| Unit: agent | (none) | `StubLLMProvider` + in-memory MCP client | nothing | happy path, recovery, every failure mode in [security.md](security.md), SSE order, persistence |
| Integration | `integration` | testcontainers Postgres or `KPI_TEST_DATABASE_URL` | Docker or a Postgres | migrations up/down, seed idempotency, SQL repo, latency < 500 ms, MCP over HTTP with trace header, stdio smoke |
| Frontend unit | – | vitest + testing-library | nothing | SSE parser, reducer, chat page streaming + panel + error banner, chart series split, explorer |
| E2E | `e2e` / Playwright | compose stack with stub provider, through nginx | Docker | question → tool calls visible → cited answer; misspelled KPI recovery; explorer chart; reload keeps history; first load < 3 s |
| Live | `live` | real Anthropic call | `ANTHROPIC_API_KEY` | one real tool-calling turn; never in CI |
| Perf smoke | – | `scripts/perf_smoke.py` | running stack | API P95 < 1 s, MCP tool < 2 s |
| Gates | – | `scripts/audit_docs.py`, `check_doc_links.py`, `check_tool_docs.py` | nothing | naming rule, specs completeness, placeholders, raw SQL, doc links, tool-doc drift |

## Commands

| Command | Runs |
|---|---|
| `make test` | `uv run pytest -m "not integration and not e2e and not live" --cov=kpi_core --cov=kpi_api --cov=kpi_mcp --cov-fail-under=80` + `pnpm -r test` |
| `make test-integration` | `uv run pytest -m integration` |
| `make test-e2e` | compose up (stub) → wait `/readyz` → Playwright → pytest `-m e2e` → compose down |
| `make perf-smoke` | latency percentiles against the running stack |
| `make ci` | lint, typecheck, `make test`, docs gates (mirrors `.github/workflows/ci.yml`) |

## Coverage policy

80 % branch coverage gate over `kpi_core`, `kpi_api`, `kpi_mcp`. Omitted on purpose:
`anthropic_provider.py` (live only), `obs/telemetry.py`
(optional), `cli.py`, migrations, tests.

## Fixtures

- Root `conftest.py`: `OTEL_SDK_DISABLED=true`; `csv_rows`; `memory_repo` (sample + demo gaps);
  `postgres_url` (env or testcontainers); `migrated_engine` (Alembic head, seeded once per session).
- `services/api/tests/conftest.py`: app factory with in-memory repos, `StubLLMProvider`, in-process
  MCP client.
- `services/mcp/tests/conftest.py`: server over in-memory repos, `fastmcp.Client(server)`.

## Conventions

`--import-mode=importlib`, strict markers, `DeprecationWarning` is an error, every `tests/` has an
`__init__.py`, tests named after the behaviour (`test_misspelled_kpi_returns_suggestions`).
