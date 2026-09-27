# Future improvements

Ordered by the value they add to a production agent platform.

1. **Authentication and RBAC** — OIDC at the API and MCP HTTP transport; `Principal` already
   flows through `RequestContext`. Tool policy per role (e.g. some tenants cannot see QTD).
2. **Multi-tenant data isolation** — `tenant_id` on data tables + Postgres RLS keyed on
   `current_setting('app.tenant_id')`, restricted DB role, cross-tenant tests
   ([how-to/extend-to-multi-tenant.md](how-to/extend-to-multi-tenant.md)).
3. **Redis-backed rate limiting and budgets** — per-tenant token buckets and per-conversation
   token/cost budgets; today's limiter is per process.
4. **Tool result caching** — QTD snapshots update at most daily; cache `get_kpi_qtd` and
   `list_company_kpis` with a short TTL keyed by tenant.
5. **Agent evaluation suite** — a golden set of questions with expected tool sequences and
   answer checks; run nightly against the stub and weekly against the real model.
6. **OpenTelemetry end to end** — export spans from API, MCP and SQLAlchemy; join with `trace_id`.
7. **Semantic KPI search** — embeddings for KPI descriptions so "how many people signed up"
   resolves to `paying_customers`.
8. **Ingestion pipeline** — replace the CSV seed with a job consuming the data provider's warehouse
   (Databricks/Delta export), with schema validation and change auditing.
9. **Trigram search and partitioning** — `pg_trgm` is already indexed; at 100x data, partition
   `kpi_estimates` by company and add read replicas.
10. **Richer tools** — `compare_kpi_across_companies`, sector aggregates, and a
    `get_company_estimates` bundle tool if agents need fewer round trips.
11. **Streaming resume and cancellation** — SSE `Last-Event-ID` replay and server-side cancel.
12. **UI** — charts in the chat answer, saved conversations list, export of the audit trail.
13. **Localise the chat app** — the website already ships English and Brazilian Portuguese with
    react-intl; the chat app is English-only today.
