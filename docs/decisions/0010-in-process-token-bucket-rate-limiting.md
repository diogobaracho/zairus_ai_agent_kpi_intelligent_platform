# ADR-0010: In-process token-bucket rate limiting per client IP

- **Status**: Accepted
- **Date**: 2026-09-24

## Context

The acceptance criteria require rate limiting without authentication.

## Decision

Pure-ASGI token-bucket middleware in the API keyed by client IP, `429` problem+json with
`Retry-After`; FastMCP's `RateLimitingMiddleware` on the MCP server. Limits via settings.

## Alternatives considered

| Option | Why not |
|---|---|
| Redis-backed limiter | Correct across replicas but adds a dependency the brief does not need |
| Reverse-proxy limits only | Not portable across providers; app-level limits are testable |

## Consequences

- **Good**: testable in-process; zero extra infrastructure.
- **Bad**: per replica; behind NAT many users share an IP.
- **Unverified**: none.

## Revisit if

The API runs with more than one replica or per-tenant quotas are needed.
