# Chat SSE protocol

`POST /v1/chat` with `{"message": "...", "conversation_id": "<uuid>|null"}` and
`Accept: text/event-stream`. The response streams events, each as:

```
id: 7
event: tool_call_finished
data: {"id":"toolu_01...","tool":"get_kpi_qtd","status":"ok","duration_ms":12,...}

```

A comment line `: keepalive` is sent every 15 s. `retry: 5000` is sent first.

| Event | Data | Notes |
|---|---|---|
| `session` | `{conversation_id, trace_id, provider, model}` | always first |
| `text_delta` | `{delta}` | answer text as it streams |
| `tool_call_started` | `{id, tool, arguments, iteration}` | after sanitisation and guard checks |
| `tool_call_finished` | `{id, tool, status: ok\|error\|timeout\|rejected, duration_ms, result_preview (≤300 chars), error}` | `error` is the envelope `{code, message, suggestions, recovery_hint}` or `null`; `rejected` carries `error.code` in `unknown_tool`, `invalid_tool_input`, `repeated_failing_call` |
| `final` | `{message_id, answer, steps[], usage:{input_tokens, output_tokens, iterations, tool_calls}, stopped_reason}` | `stopped_reason`: `end_turn`, `max_iterations`, `wall_clock`, `refusal`, `max_tokens`, `provider_error` |
| `error` | `{code, message, trace_id}` | terminal; also for `upstream_unavailable` |

Before the stream starts, ordinary problem+json responses apply (`400` validation, `413` body,
`429` rate limit, `404` unknown conversation).

Client: `apps/chat-web/src/api/sse.ts` parses the stream with `fetch` + `ReadableStream` and
dispatches to the chat reducer; the tool execution panel is built from
`tool_call_started`/`tool_call_finished` and the `final.steps` list (authoritative).
