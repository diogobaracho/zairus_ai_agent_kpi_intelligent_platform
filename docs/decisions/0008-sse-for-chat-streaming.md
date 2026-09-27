# ADR-0008: Server-sent events over a POST request for chat streaming

- **Status**: Accepted
- **Date**: 2026-09-24

## Context

The UI must show tool calls as they happen and stream the answer.

## Decision

`POST /v1/chat` returns `text/event-stream` with typed events (`session`, `text_delta`,
`tool_call_started`, `tool_call_finished`, `final`, `error`), sequence ids and keepalives. The
browser uses `fetch` + `ReadableStream` (not `EventSource`, which cannot POST). nginx disables
buffering for `/api/`.

## Alternatives considered

| Option | Why not |
|---|---|
| WebSocket | Bidirectional not needed; more proxy configuration |
| Polling a job id | Latency and complexity for a chat UI |

## Consequences

- **Good**: simple, proxy-friendly, replayable event log per message.
- **Bad**: no client → server messages mid-stream (cancel is an abort).
- **Unverified**: behaviour behind other reverse proxies than nginx (documented settings).

## Revisit if

Cancellation or mid-run user input becomes a requirement.
