# ADR-0003: FastMCP 4 with four read-only tools and a structured error envelope

- **Status**: Accepted
- **Date**: 2026-09-24

## Context

The brief recommends FastMCP, asks for 2–4 tools, explicit handling of invalid tickers and
misspelled KPI names, and logging of every call. FastMCP 4.0 (verified 2026-09-24) provides typed
tool parameters, structured output, `ToolError`, middleware hooks and both stdio/HTTP transports.

## Decision

Four tools: `search_companies`, `list_company_kpis`, `get_kpi_history`, `get_kpi_qtd`. Inputs are
public identifiers only (ticker, KPI name/slug/alias, period labels). Recoverable errors are raised
as `ToolError(json)` with the envelope `{code, message, suggestions[], recovery_hint, retryable,
trace_id}` so the client sees `isError: true` and the model has what it needs to retry.
`mask_error_details=True` hides everything else. Empty results are successes with a `note`.

## Alternatives considered

| Option | Why not |
|---|---|
| Return errors as normal results with `ok: false` | Clients and SDKs already treat `isError` specially; mixing would confuse retries |
| One mega tool `query_kpi(...)` | Ambiguous parameters; the model must guess which fields matter |
| Six+ tools (sectors, catalog, compare…) | Above the brief's range; sectors are returned by `search_companies` when called without arguments |
| Raw `mcp` SDK | More boilerplate for the same result; FastMCP is recommended by the brief |

## Consequences

- **Good**: recovery in one retry; identical envelope for every caller; tool docs generated from schemas.
- **Bad**: envelope is a JSON string inside a text block (MCP has no structured error payload yet); FastMCP 4 is new and may drift.
- **Unverified**: behaviour of Claude Desktop's UI when rendering the envelope text.

## Revisit if

MCP adds structured error content, or agents need fewer round trips (bundle tool).
