# Run the tests

1. `make test` — fast suite: Python unit tests with the 80 % coverage gate plus `pnpm -r test`.
   Needs nothing running.
2. `make test-integration` — Postgres-backed tests. Uses `KPI_TEST_DATABASE_URL` if set, else
   starts a `postgres:16-alpine` testcontainer (Docker required).
3. `make test-e2e` — brings the compose stack up with the stub provider, waits for `/readyz`,
   runs Playwright (`tests/e2e`) and the pytest `e2e` smoke, then tears down.
4. `uv run pytest -m live` — one real Anthropic tool-calling turn; requires
   `ANTHROPIC_API_KEY`; never runs in CI.
5. `make perf-smoke` — P95 latency for the acceptance targets against the running stack.
6. `make ci` — everything CI runs, in CI's order.

Useful selections:

```bash
uv run pytest packages/kpi_core -k fuzzy -q
uv run pytest services/mcp/tests/test_error_envelope.py -q
uv run pytest services/api/tests/agent -q
pnpm --filter chat-web test -- --run
```

## Verify

```bash
make test
# ... passed; TOTAL coverage >= 80%
```

## What usually goes wrong

- **Coverage below gate**: run with `--cov-report=term-missing` to see the lines.
- **testcontainers cannot reach Docker**: export `KPI_TEST_DATABASE_URL` pointing at
  `make up`'s Postgres (`postgresql+asyncpg://kpi:kpi@localhost:5432/kpi_test`).
- **Playwright browsers missing**: `pnpm --filter e2e exec playwright install --with-deps`.
- **DeprecationWarning treated as error**: it is deliberate; fix the cause or add a narrowly
  scoped ignore in `pyproject.toml` with a comment.
