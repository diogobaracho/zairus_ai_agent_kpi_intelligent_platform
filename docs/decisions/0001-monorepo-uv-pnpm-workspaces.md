# ADR-0001: Monorepo with a uv workspace (Python) and a pnpm workspace (TypeScript)

- **Status**: Accepted
- **Date**: 2026-09-24

## Context

The brief asks for a Python backend, a Python MCP server and a TypeScript/React frontend, plus a
marketing website. They must be easy to run and test together locally, yet deployable alone.

## Decision

One repository. Python packages (`packages/kpi_core`, `services/api`, `services/mcp`) form a uv
workspace with a single lockfile and shared lint/type/test config in the root `pyproject.toml`.
TypeScript apps (`apps/chat-web`, `apps/website`, `tests/e2e`) form a pnpm workspace. A root
Makefile is the single entry point, and `make ci` runs exactly what CI runs.

## Alternatives considered

| Option | Why not |
|---|---|
| Separate repos per service | Slower to review and run; cross-cutting changes need coordinated releases |
| Poetry per package | No workspace concept; uv is faster and gives one lockfile |
| Turborepo/Nx for everything | Overkill for two SPAs; pnpm workspaces are enough |

## Consequences

- **Good**: one `make up`; shared conventions; `kpi_core` reused by both adapters without publishing.
- **Bad**: a monorepo needs import-boundary discipline (`AGENTS.md` rules + mypy paths).
- **Unverified**: CI runtime with both toolchains on GitHub-hosted runners.

## Revisit if

A service needs a different Python version or must be released on its own cadence.
