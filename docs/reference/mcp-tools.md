# MCP tools (`services/mcp`)

Server name: `mcpServerName` from `brand.config.json` (default `zairus-kpi`). Transports: stdio (`python -m kpi_mcp --transport stdio`) and streamable
HTTP (`http://localhost:8090/mcp`). All tools are read-only and idempotent
(`readOnlyHint=true, idempotentHint=true, openWorldHint=false`). Inputs use public identifiers
only; no internal ids, no tenant or user fields. Every success payload includes `trace_id`.

| Tool | Use it when | Parameters | Returns |
|---|---|---|---|
| `search_companies` | You need a ticker, want companies in a sector, or want to see what exists | `query?` string ≤64 (ticker or partial name), `sector?` string ≤64, `limit` int 1..100 (20) | `companies[] {ticker, name, sector}`, `total`, `sector_filter`, `suggestions[]` (only when nothing matched), `sectors_available[]` (only when called with no arguments) |
| `list_company_kpis` | You know the ticker and need the KPI names/units and their coverage | `ticker` string ≤10 | `company`, `kpis[] {slug, name, display_name, unit, unit_kind, scale, description, first_period, last_period, has_qtd}` |
| `get_kpi_history` | You need completed-quarter estimates for one KPI | `ticker`, `kpi` (slug, name or alias, ≤80), `from_period?`, `to_period?` (`YYYYQn`), `limit` ≤64 | `company`, `kpi`, `points[]` ascending `{period, period_start, period_end, value, unit}`, `count`, `requested_range`, `available_range`, `truncated`, `note` |
| `get_kpi_qtd` | You need the current quarter-to-date estimate and its snapshots | `ticker`, `kpi` | `company`, `kpi`, `period`, `latest {as_of, value, unit}`, `snapshots[]` ascending by `as_of`, `prior_quarter {period, value, unit}`, `note` |

Typical sequences: *"What's ORBY's QTD revenue?"* → `get_kpi_qtd(ORBY, revenue)` (one call);
*"Compare ARR growth across software companies"* → `search_companies(sector=...)` →
`get_kpi_history(...)` per company. A model that is unsure of a ticker should call
`search_companies` first; suggestions make a wrong guess cheap.

## Error envelope

Raised as an MCP tool error (`isError: true`); the text content is:

```json
{"error":{"code":"kpi_not_found","message":"KPI 'Totl Revenue' not found for ORBY",
 "suggestions":[{"value":"total_revenue","label":"Total Revenue ($MM)","score":95.2}],
 "recovery_hint":"Retry with kpi set to suggestions[0].value, or call list_company_kpis(ticker='ORBY').",
 "retryable":true,"trace_id":"9f1c2ab4d0e3f5a7"}}
```

| Code | When | Suggestions |
|---|---|---|
| `invalid_ticker` | ticker fails `^[A-Z0-9][A-Z0-9.\-]{0,9}$` after upper-casing | – |
| `company_not_found` | no company with that ticker/name | closest tickers/names |
| `kpi_not_found` | KPI unknown, or known but not published for this company | closest KPI slugs; hint to call `list_company_kpis` |
| `sector_not_found` | sector filter matches nothing | closest sectors |
| `invalid_period` / `invalid_period_range` | bad `YYYYQn` or from > to | example format |
| `validation_error` | parameter length/type violations, unknown keys | field names |
| `rate_limited` | too many calls; FastMCP answers at the protocol level (`MCPError: Rate limit exceeded`) rather than with this envelope, and the limiter also counts handshake requests | retry after a second |
| `internal_error` | unexpected failure (details masked) | – |

Empty data is **not** an error: `get_kpi_history` with a range outside the data returns
`points: []` with `note` and `available_range`; `get_kpi_qtd` for a company without snapshots
returns `latest: null` with `note`.

## Examples

```jsonc
// search_companies {"query":"orbit"}
{"companies":[{"ticker":"ORBF","name":"Orbital Freight","sector":"Logistics"},{"ticker":"ORBY","name":"Orbitly Analytics","sector":"Software"}],"total":2,"sector_filter":null,"suggestions":[],"trace_id":"..."}

// search_companies {} (discovery)
{"companies":[...19...],"total":19,"sectors_available":["Consumer Hardware","Cybersecurity","Digital Health",...],"trace_id":"..."}

// search_companies {"query":"Orbitly Analitycs"}   -> success with suggestions
{"companies":[],"total":0,"suggestions":[{"value":"ORBY","label":"Orbitly Analytics (ORBY)","score":92.1}],"trace_id":"..."}

// get_kpi_history {"ticker":"ORBY","kpi":"revenue","from_period":"2025Q1"}
{"company":{...},"kpi":{"slug":"total_revenue","name":"Total Revenue ($MM)","unit":"$MM"},"points":[{"period":"2025Q1",...},{"period":"2025Q2",...},{"period":"2025Q3",...},{"period":"2026Q2",...}],"count":4,"requested_range":{"from_period":"2025Q1","to_period":null},"available_range":{"from_period":"2023Q1","to_period":"2026Q2"},"truncated":false,"note":null,"trace_id":"..."}

// get_kpi_qtd {"ticker":"GAPW","kpi":"total_revenue"}   (demo company without snapshots)
{"company":{"ticker":"GAPW",...},"kpi":{...},"period":null,"latest":null,"snapshots":[],"prior_quarter":{"period":"2026Q2","value":151.5,"unit":"$MM"},"note":"No QTD snapshots published for GAPW total_revenue.","trace_id":"..."}
```

## Schema snapshot

`mcp-tools.json` (generated by `make tool-docs`, checked by `scripts/check_tool_docs.py`) holds the
exact `tools/list` output, so this page and the server cannot drift silently.
