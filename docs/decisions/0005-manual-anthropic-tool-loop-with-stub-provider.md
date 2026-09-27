# ADR-0005: Manual Anthropic tool loop with explicit guards, streamed over SSE, plus a stub provider

- **Status**: Accepted
- **Date**: 2026-09-24

## Context

The chat must show every tool call live and guard against LLM tool-calling failure modes. The
SDK's `tool_runner` hides the loop; Anthropic's hosted MCP connector needs a public URL. The stack
must run with zero API keys.

## Decision

`kpi_api.agent.loop` drives `messages.stream` manually: it converts MCP tool schemas to Anthropic
tools, executes `tool_use` blocks through the MCP client, and emits `AgentEvent`s consumed by the
SSE endpoint. Guards: iteration budget, duplicate-failing-call ledger, per-tool timeout, wall clock,
result truncation, unknown-tool and parse-error rejection, `max_tokens`/`refusal`/`pause_turn`
handling. Providers implement one interface; `StubLLMProvider` is deterministic and default.
Default model `claude-opus-5`, configurable.

## Alternatives considered

| Option | Why not |
|---|---|
| `client.beta.messages.tool_runner` | Beta; no per-step hooks for streaming UI events; cannot inject rejections |
| Anthropic MCP connector (`mcp_servers`) | Requires a publicly reachable MCP URL; bypasses our audit middleware ordering |
| LangChain/LangGraph | Extra abstraction for four tools; harder to reason about and to test deterministically |
| WebSocket instead of SSE | SSE is one-way, simpler through proxies, enough for streaming |

## Consequences

- **Good**: every guard is visible and tested; demo works offline; provider is swappable.
- **Bad**: more loop code to own; the stub can drift from real-model behaviour.
- **Unverified**: real-model recovery rates at scale; only the opt-in live tests exercise a real model.

## Revisit if

The API adds server-side compaction or the SDK runner gains per-step hooks.
