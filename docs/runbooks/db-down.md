# Database down

**Symptom**: `/readyz` → 503 `{"checks":{"db":"fail"}}`; REST returns `500 internal_error`;
MCP tools return `internal_error` envelopes; audit writes are skipped (logged as `audit_failed`).

**Working as designed?** Tools fail closed; the audit middleware never blocks a tool because of
its own failure.

**Diagnose**: `docker compose ps postgres`, `docker compose logs postgres`, connection string in
`KPI_DATABASE_URL`, pool exhaustion (`sqlalchemy.pool` warnings).

**Fix**: restart Postgres; if migrations are behind, run the migrate job; if pool exhausted,
restart API/MCP.

**Escalate**: data corruption or disk full.
