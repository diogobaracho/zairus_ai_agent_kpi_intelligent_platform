# ADR-0009: In-memory repository for the fast suite, real Postgres for integration

- **Status**: Accepted
- **Date**: 2026-09-24

## Context

Coverage over 80 % on business logic must be enforced without making `make test` depend on Docker.

## Decision

`InMemoryKpiRepository.from_csv` implements the same protocol as the SQL repository; a shared
contract test module runs against both. Unit suites for services, MCP tools (in-memory
`fastmcp.Client`) and the agent (stub provider) need nothing running. Integration tests use
testcontainers locally or `KPI_TEST_DATABASE_URL` in CI.

## Alternatives considered

| Option | Why not |
|---|---|
| SQLite for unit tests | Different SQL dialect; hides Postgres-specific behaviour |
| Mock the repository per test | Drifts from real semantics; contract tests keep both honest |

## Consequences

- **Good**: fast feedback; the in-memory repo also powers the in-process MCP mode.
- **Bad**: two repository implementations to maintain (mitigated by the contract suite).
- **Unverified**: none.

## Revisit if

Repository semantics become too rich to keep two implementations aligned.
