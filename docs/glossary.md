# Glossary

One line per term.

| Term | Meaning |
|---|---|
| KPI | Key performance indicator estimated by the data provider for a public company (e.g. Total Revenue) |
| Historical estimate | The data provider's estimate for a completed fiscal quarter (`estimate_type=historical`, `as_of` empty) |
| QTD | Quarter-to-date: an intra-quarter estimate at a point in time (`as_of`), updated at most daily |
| Snapshot | One QTD row for a given `as_of` date |
| Period | Fiscal quarter label `YYYYQn`, e.g. `2026Q2` |
| Ticker | Short company symbol (`ORBY`); the public identifier used by all tools |
| KPI slug | LLM-friendly KPI id (`total_revenue`) derived from the KPI name |
| Suggestion | `{value, label, score}` offered when a ticker, KPI or sector does not match |
| Error envelope | JSON `{error: {code, message, suggestions, recovery_hint, retryable, trace_id}}` returned by MCP tools |
| Problem document | RFC 9457 `application/problem+json` error returned by the REST API |
| MCP | Model Context Protocol: standard for exposing tools/resources to AI clients |
| Tool call | One invocation of an MCP tool, audited as one `tool_call_audit` row |
| Step | The chat agent's record of one tool call inside an assistant turn |
| trace_id | Correlation id shared by a request, its tool calls, logs and audit rows |
| RequestContext | Server-built `{trace_id, tenant_id, principal, caller}` passed to every service |
| Stub provider | Deterministic LLM stand-in that scripts tool calls so the stack runs without API keys |
| SSE | Server-sent events; the chat streaming transport |
