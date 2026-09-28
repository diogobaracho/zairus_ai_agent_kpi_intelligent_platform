# Extend to multi-tenant data isolation

Today: `RequestContext.tenant_id` is `default`, persisted on audit and chat tables. The LLM never
supplies it. Steps to isolate data per tenant with Postgres row-level security:

1. **Schema**: migration adds `tenant_id TEXT NOT NULL DEFAULT 'default'` to `companies`,
   `kpi_estimates` (and `kpis` if KPI catalogs differ per tenant); extend unique keys to include
   `tenant_id`; backfill.
2. **Roles**: create a restricted role `kpi_app` (no superuser, no BYPASSRLS). Services connect as
   `kpi_app`; migrations keep using the owner role.
3. **RLS**: `ALTER TABLE ... ENABLE ROW LEVEL SECURITY; FORCE ROW LEVEL SECURITY; CREATE POLICY
   tenant_isolation ON companies USING (tenant_id = current_setting('app.tenant_id', true));`
   for each table.
4. **Session binding**: in `kpi_core.db.session_scope(ctx)`, run
   `SET LOCAL app.tenant_id = :tenant_id` at the start of every transaction using the
   `RequestContext`.
5. **Identity source**: API derives `tenant_id` from the authenticated principal (OIDC claim);
   MCP HTTP transport from the bearer token; stdio deployments pin `KPI_TENANT_ID` in env.
6. **Tests**: for every endpoint and tool, a cross-tenant test that seeds two tenants and asserts
   the other tenant's rows are invisible, plus the positive case. Use the restricted role in the
   test engine (superusers bypass RLS).
7. **Audit**: `tool_call_audit.tenant_id` already exists; add it to log lines.

## Verify

```bash
uv run pytest -m integration -k tenant -q
psql -U kpi_app -c "select count(*) from companies"   # only the bound tenant's rows
```

## What usually goes wrong

- Tests pass by accident because they connect as a superuser.
- Cached candidate lists for fuzzy suggestions must be keyed by tenant.
