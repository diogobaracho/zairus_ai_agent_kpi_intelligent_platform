# Error codes

One hierarchy (`kpi_core.errors.KpiError`), two serialisations.

REST (`application/problem+json`):

```json
{"type":"/docs/reference/error-codes#company_not_found","title":"Not found","status":404,
 "detail":"No company with ticker 'ORBYY'","code":"company_not_found",
 "suggestions":[{"value":"ORBY","label":"Orbitly Analytics (ORBY)","score":88.9}],
 "recovery_hint":"Use one of suggestions[].value or search with ?q=","instance":"/v1/companies/ORBYY",
 "trace_id":"9f1c2ab4d0e3f5a7"}
```

MCP: `{"error":{code, message, suggestions, recovery_hint, retryable, trace_id}}` as the text of an
`isError` result.

| Code | HTTP | Class | Retryable | Meaning |
|---|---|---|---|---|
| `validation_error` | 400 | `ValidationError` | yes (fix input) | parameter failed validation |
| `invalid_ticker` | 400 | `InvalidTicker` | yes | ticker format |
| `invalid_period` | 400 | `InvalidPeriod` | yes | not `YYYYQn` |
| `invalid_period_range` | 400 | `InvalidPeriodRange` | yes | from > to |
| `company_not_found` | 404 | `CompanyNotFound` | yes | with suggestions |
| `kpi_not_found` | 404 | `KpiNotFound` | yes | with suggestions; also "not published for this company" |
| `sector_not_found` | 404 | `SectorNotFound` | yes | with suggestions |
| `conversation_not_found` | 404 | `ConversationNotFound` | no | unknown conversation id |
| `payload_too_large` | 413 | `PayloadTooLarge` | no | body over limit |
| `agent_budget_exceeded` | 422 | `AgentBudgetExceeded` | no | loop guards stopped the run |
| `rate_limited` | 429 | `RateLimited` | yes (after `Retry-After`) | token bucket empty |
| `upstream_unavailable` | 503 | `UpstreamUnavailable` | yes | MCP or LLM provider unreachable |
| `tool_timeout` | 504 | `ToolTimeout` | yes | tool exceeded `KPI_AGENT_TOOL_TIMEOUT_S` |
| `internal_error` | 500 | (unhandled) | no | bug; logged with traceback, details masked |

Agent-only rejection codes inside SSE `tool_call_finished.error.code`: `unknown_tool`,
`invalid_tool_input`, `repeated_failing_call`.
