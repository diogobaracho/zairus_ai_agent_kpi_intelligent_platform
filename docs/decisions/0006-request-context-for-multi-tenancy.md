# ADR-0006: RequestContext carries identity; the LLM never does

- **Status**: Accepted
- **Date**: 2026-09-24

## Context

Any serious agent platform gets asked about multi-tenant data isolation and the LLM↔data security boundary. The
brief does not require auth today.

## Decision

Every service function receives `RequestContext(trace_id, tenant_id, principal, caller)` built by
the adapter from server-side facts (headers, settings, transport). Tool schemas contain no identity
fields; unknown keys in tool arguments are dropped and counted. `tenant_id` is persisted on audit
and chat tables now. The documented path to full isolation is: add `tenant_id` to data tables,
enable Postgres RLS keyed on `current_setting('app.tenant_id')` set in `session_scope`, connect as
a restricted role, and add a cross-tenant test per endpoint.

## Alternatives considered

| Option | Why not |
|---|---|
| Add RLS now | Adds a role split and per-test complexity the brief does not ask for |
| Pass tenant as a tool parameter | The model could choose any tenant; unacceptable |

## Consequences

- **Good**: the boundary exists from day one and is testable; RLS is an additive change.
- **Bad**: `tenant_id` is a constant today, which can look vestigial without this ADR.
- **Unverified**: RLS performance with the partial indexes.

## Revisit if

A second tenant appears.
