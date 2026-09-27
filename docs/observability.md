# Observability

Goal: **every tool call is traceable end to end, and any answer can be reconstructed afterwards.**

## One id: `trace_id`

| Hop | Where it appears |
|---|---|
| Browser → API | optional `X-Correlation-Id` request header (validated `^[A-Za-z0-9_-]{8,64}$`, else replaced) |
| API | `CorrelationIdMiddleware` (pure ASGI) stores it in a ContextVar, echoes it in the response header, and puts it in `RequestContext.trace_id` |
| SSE | first event `session {conversation_id, trace_id, provider, model}` |
| API → MCP | `X-Correlation-Id` header on the streamable-HTTP transport **and** `meta.trace_id` on every `call_tool` |
| MCP | `TraceMiddleware` resolves header → meta → mint, binds a `RequestContext(caller="mcp")` |
| Database | `tool_call_audit.trace_id`, `chat_messages.trace_id` |
| Logs | every JSON log line of both services carries `trace_id` |
| UI | "Trace" link on each assistant message → `/trace/:traceId` → `GET /v1/audit/tool-calls?trace_id=` |

## Structured logs

python-json-logger on the root logger, one JSON object per line, fields: `timestamp`, `level`,
`logger`, `message`, `trace_id`, `service`, plus event fields. Discrete events go through
`log_event(name, **fields)`:

| Event | Fields |
|---|---|
| `http_request` | method, path, status, duration_ms, client_ip |
| `tool_call` | tool_name, arguments, status (`ok`/`error`/`timeout`/`rejected`), duration_ms, error (envelope), result_summary, transport, session_id |
| `llm_turn` | provider, model, stop_reason, input_tokens, output_tokens, duration_ms |
| `agent_run` | conversation_id, iterations, tool_calls, stopped_reason, total tokens |
| `seed` | companies, kpis, estimates, inserted, updated |

Example (MCP):

```json
{"timestamp":"2026-09-24T18:02:11.412Z","level":"INFO","logger":"kpi.metrics","message":"tool_call","trace_id":"9f1c2ab4d0e3f5a7","service":"kpi-mcp","tool_name":"get_kpi_history","arguments":{"ticker":"ORBY","kpi":"Totl Revenue"},"status":"error","duration_ms":3,"error":{"code":"kpi_not_found","suggestions":[{"value":"total_revenue","label":"Total Revenue ($MM)","score":95.2}]}}
```

Sensitive data: no secrets are ever logged (settings redact `*_KEY`, `*_TOKEN`, `*_URL` password
parts); user messages are logged only as length + hash at INFO, full text at DEBUG.

## Audit table

`tool_call_audit` (see [data-model.md](data-model.md)) is written by the MCP `AuditMiddleware`
for every call regardless of caller (chat agent, Claude Desktop, Cursor, tests). Query it via
`GET /v1/audit/tool-calls?trace_id=…&tool_name=…&status=…&limit=…` or SQL. Audit failures are
logged and never fail the tool call.

## Health

- `GET /healthz` — process is up (both services).
- `GET /readyz` — API: `SELECT 1` + MCP `list_tools` reachability + provider configured;
  MCP: `SELECT 1`. Returns 503 with the failing check named.

## Metrics

Low-volume discrete events are log lines (queryable in any aggregator). Latency histograms are
derived from `http_request.duration_ms` and `tool_call.duration_ms`. `scripts/perf_smoke.py`
computes P95 for the acceptance targets locally.

## Tracing (optional)

`OTEL_SDK_DISABLED=true` by default. Setting it to `false` with `OTEL_EXPORTER_OTLP_ENDPOINT`
enables FastAPI, SQLAlchemy and httpx auto-instrumentation; spans carry `trace_id` as an
attribute so log lines and spans join. Not exercised in CI.

## Reconstructing an interaction

1. Take the `trace_id` from the UI, the SSE `session` event or the `X-Correlation-Id` header.
2. `GET /v1/chat/conversations/{id}` → messages with `steps` (tool, arguments, status, duration,
   result preview, error).
3. `GET /v1/audit/tool-calls?trace_id=…` → the authoritative per-call rows from the MCP side.
4. `docker compose logs api mcp | grep <trace_id>` → LLM turns, guards that fired, timings.

Walkthrough with real output: [how-to/debug-a-tool-call.md](how-to/debug-a-tool-call.md).
