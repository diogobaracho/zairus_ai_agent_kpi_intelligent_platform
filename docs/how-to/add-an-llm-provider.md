# Add an LLM provider

Providers implement `LLMProvider.stream_turn(system, messages, tools) -> AsyncIterator[LLMEvent]`
in `services/api/src/kpi_api/agent/providers/`.

1. Create `providers/<vendor>_provider.py`. Map the vendor's streaming events to `TextDelta`,
   `ToolUseStart`, `ToolUseComplete(id, name, input, parse_error)` and `TurnEnd(stop_reason,
   usage, assistant_content)`. Keep vendor imports inside this file only.
2. Map vendor exceptions to `UpstreamUnavailable` (retryable) or `ValidationError` (not).
3. Convert tool definitions from the Anthropic-style dict if the vendor's format differs
   (add `to_<vendor>_tool` next to `to_anthropic_tool`).
4. Register in `providers/__init__.py::get_provider` under a new `KPI_LLM_PROVIDER` value.
5. Tests: a fake vendor client that emits the documented events; assert the mapping and the
   error translation. Add a `live` test guarded by the vendor's API key variable.
6. Document the variables in `docs/reference/configuration.md`.

## Verify

```bash
KPI_LLM_PROVIDER=<vendor> uv run pytest services/api/tests/agent -q
```

## What usually goes wrong

- Emitting `TurnEnd` before all tool inputs are complete: the loop will execute partial JSON.
- Returning tool results one per message: put all results of a turn in one user message.
