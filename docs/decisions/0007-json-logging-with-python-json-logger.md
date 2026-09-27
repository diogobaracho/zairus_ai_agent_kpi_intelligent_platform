# ADR-0007: JSON logs via python-json-logger and a tool_call_audit table, OpenTelemetry optional

- **Status**: Accepted
- **Date**: 2026-09-24

## Context

The brief requires every tool call to be logged with tool name, arguments, duration, status and
error, and to be inspectable after the fact.

## Decision

Stdlib `logging` with python-json-logger on the root logger and a ContextVar filter injecting
`trace_id`; `log_event(name, **fields)` for discrete events. The MCP `AuditMiddleware` also
writes a `tool_call_audit` row per call. OpenTelemetry instrumentation is wired but disabled by
default.

## Alternatives considered

| Option | Why not |
|---|---|
| structlog | uvicorn, SQLAlchemy, FastMCP and the Anthropic SDK log via stdlib; a second pipeline adds bridging for no gain |
| Logs only, no audit table | Log retention is not a query surface; the UI trace page needs a queryable store |
| Full OTel + Grafana stack in compose | Valuable, but outside the brief's scope; kept optional |

## Consequences

- **Good**: one id joins UI, logs and DB; audit works for external MCP clients too.
- **Bad**: audit writes add a DB round trip per tool call (async, failure-tolerant).
- **Unverified**: OTel export.

## Revisit if

Tool-call volume makes synchronous audit writes a bottleneck (batch or queue them).
