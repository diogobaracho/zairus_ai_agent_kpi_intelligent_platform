# REST API (`services/api`, port 8080)

Base path `/v1`. All responses are JSON; errors are RFC 9457 `application/problem+json`
(see [error-codes.md](error-codes.md)). Every response carries `X-Correlation-Id`.
Interactive docs: `/docs` (OpenAPI).

| Method | Path | Query / body | Returns |
|---|---|---|---|
| GET | `/healthz` | – | `{status:"ok", service, version}` |
| GET | `/readyz` | – | `{status, checks:{db, mcp, llm_provider}}`; 503 if a check fails |
| GET | `/v1/sectors` | – | `{items:[{name, company_count}]}` |
| GET | `/v1/companies` | `q` (≤64), `sector`, `limit` (1..100, 20), `offset` | `{items:[Company], total, limit, offset, suggestions[]}` (suggestions only when empty) |
| GET | `/v1/companies/{ticker}` | – | `Company` |
| GET | `/v1/companies/{ticker}/kpis` | – | `{company, items:[CompanyKpi]}` |
| GET | `/v1/companies/{ticker}/kpis/{kpi}/history` | `from_period`, `to_period` (`YYYYQn`), `limit` (≤64) | `KpiHistory` |
| GET | `/v1/companies/{ticker}/kpis/{kpi}/qtd` | – | `KpiQtd` |
| GET | `/v1/companies/{ticker}/estimates` | – | `CompanyEstimates` (every KPI: history + current QTD, separated) |
| GET | `/v1/kpis` | – | `{items:[KpiDefinition]}` |
| POST | `/v1/chat` | `{message (≤4000), conversation_id?}` | `text/event-stream` ([sse-protocol.md](sse-protocol.md)) |
| GET | `/v1/chat/conversations` | `limit` | `{items:[{id, created_at, updated_at, title}]}` |
| GET | `/v1/chat/conversations/{id}` | – | `{id, messages:[{id, seq, role, content, steps, usage, trace_id, stopped_reason, created_at}]}` |
| GET | `/v1/audit/tool-calls` | `trace_id`, `tool_name`, `status`, `limit` (≤200) | `{items:[ToolCallAudit]}` |
| GET | `/v1/meta/tools` | – | `{items:[{name, description, input_schema, strict}]}` — the tools the agent sees |

`{kpi}` accepts a slug (`total_revenue`), the canonical name (`Total Revenue ($MM)`), or an alias
(`revenue`). `{ticker}` is case-insensitive.

## Shapes

```jsonc
// Company
{"ticker":"ORBY","name":"Orbitly Analytics","sector":"Software"}
// CompanyKpi
{"slug":"total_revenue","name":"Total Revenue ($MM)","display_name":"Total Revenue","unit":"$MM",
 "unit_kind":"currency","scale":1000000,"description":"...","first_period":"2023Q1","last_period":"2026Q2","has_qtd":true}
// KpiHistory
{"company":{...},"kpi":{...},"points":[{"period":"2023Q1","period_start":"2022-01-01","period_end":"2022-03-31","value":128.67,"unit":"$MM"}],
 "count":16,"requested_range":null,"available_range":{"from_period":"2023Q1","to_period":"2026Q2"},"truncated":false,"note":null}
// KpiQtd
{"company":{...},"kpi":{...},"period":"2026Q3","latest":{"as_of":"2026-09-15","value":164.22,"unit":"$"},
 "snapshots":[{"as_of":"2026-07-31","value":162.95,"unit":"$"},...],"prior_quarter":{"period":"2026Q2","value":173.83,"unit":"$"},"note":null}
```

## Examples

```bash
curl -s 'localhost:8080/v1/companies?q=orbitly' | jq '.items[0]'
curl -s 'localhost:8080/v1/companies?sector=Software' | jq '.total'       # 2 (3 with make seed-demo)
curl -si localhost:8080/v1/companies/ORBYY | sed -n '1p;/^{/p'              # 404 + problem with suggestions
curl -s 'localhost:8080/v1/companies/ORBY/kpis/revenue/history?from_period=2025Q3' | jq '.count'   # 4
curl -s 'localhost:8080/v1/companies/ORBY/kpis/total_revenue/qtd' | jq '.latest'
curl -N -X POST localhost:8080/v1/chat -H 'content-type: application/json' -d '{"message":"What is ORBY total revenue QTD?"}'
```

Rate limit: `KPI_RATE_LIMIT_RPS` requests/second with burst `KPI_RATE_LIMIT_BURST` per client IP;
exceeding it returns `429` with `Retry-After`. Body limit 16 KiB → `413`.
