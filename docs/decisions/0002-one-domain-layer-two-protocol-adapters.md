# ADR-0002: One domain layer (kpi_core), two protocol adapters (REST and MCP)

- **Status**: Accepted
- **Date**: 2026-09-24

## Context

The same data must be served to humans (REST/UI) and to agents (MCP). Duplicating query and
suggestion logic in two servers would make the error semantics diverge, which is exactly what an
LLM cannot cope with.

## Decision

All business logic lives in `packages/kpi_core/services`. `services/api` routers and
`services/mcp` tools are thin adapters that validate transport-specific input, call one service
function with a server-built `RequestContext`, and serialise the result or the `KpiError`.
Enforced by import rules in `AGENTS.md` and by the repository contract tests.

## Alternatives considered

| Option | Why not |
|---|---|
| MCP server calls the REST API over HTTP | Extra hop, error shapes translated twice, harder to test in-process |
| Everything in one FastAPI app with MCP mounted | Couples deployments; MCP must run standalone for desktop clients |

## Consequences

- **Good**: adding a tool is one function; suggestions identical in REST and MCP; unit tests run on the in-memory repository.
- **Bad**: a third package to version and document.
- **Unverified**: none.

## Revisit if

Adapters start needing different data shapes that cannot be expressed as DTOs in `kpi_core`.
