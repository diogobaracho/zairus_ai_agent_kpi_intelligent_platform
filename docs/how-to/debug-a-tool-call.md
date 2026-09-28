# Debug a tool call

Scenario: a user reports "the chat said ORBY has no revenue data".

1. Get the `trace_id`: from the chat UI (trace link on the answer), the SSE `session` event, or
   the `X-Correlation-Id` response header.
2. Reconstruct the conversation:

```bash
curl -s localhost:8080/v1/chat/conversations/<id> | jq '.messages[-1].steps'
```

   Each step shows `tool`, `arguments`, `status`, `duration_ms`, `result_preview`, `error`.
3. Query the authoritative audit rows:

```bash
curl -s 'localhost:8080/v1/audit/tool-calls?trace_id=<trace_id>' | jq '.items[] | {tool_name, arguments, status, duration_ms, error}'
```

4. Read the logs of both services for that id:

```bash
docker compose logs api mcp | grep <trace_id> | jq -c 'select(.message=="tool_call" or .message=="llm_turn" or .message=="agent_run")'
```

   Look for `status: rejected` (guard fired: unknown tool, duplicate failing call, oversize args),
   `timeout`, or an envelope with `suggestions` the model ignored.
5. Reproduce the tool call directly:

```bash
uv run python scripts/mcp_smoke.py --url http://localhost:8090/mcp --tool get_kpi_history --args '{"ticker":"ORBY","kpi":"revenue"}'
```

6. If the tool is right and the answer is wrong, the issue is prompting: check `agent_run.stopped_reason`
   and the final text; adjust `agent/prompts.py` and add the transcript to the eval notes.

## Verify

A correct diagnosis names one of: data (seed), tool (service/envelope), guard (loop), or prompt.

## What usually goes wrong

- No audit rows for the trace: the API could not reach MCP (`readyz.checks.mcp`), the step
  will be `status: error` with `code: upstream_unavailable`.
- Logs lack `trace_id`: a middleware was added with `BaseHTTPMiddleware`, which breaks
  ContextVar propagation; use pure ASGI.
