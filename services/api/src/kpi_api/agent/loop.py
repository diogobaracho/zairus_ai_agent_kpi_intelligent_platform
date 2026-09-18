"""The guarded tool loop. Every LLM failure mode has a named guard here (docs/security.md)."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from kpi_api.agent.guards import CallLedger, preview, sanitize_tool_args, truncate_result
from kpi_api.agent.persistence import ConversationStore
from kpi_api.agent.prompts import build_system_prompt
from kpi_api.agent.providers.base import LLMProvider
from kpi_api.agent.tools import McpSession, McpToolGateway, to_anthropic_tool
from kpi_api.agent.types import (
    AgentEvent,
    ErrorEvent,
    FinalEvent,
    SessionEvent,
    Step,
    StoppedReason,
    TextDelta,
    TextDeltaEvent,
    ToolCallFinishedEvent,
    ToolCallStartedEvent,
    ToolOutcome,
    ToolUseComplete,
    ToolUseStart,
    TurnEnd,
    Usage,
)
from kpi_api.settings import ApiSettings
from kpi_core.context import RequestContext
from kpi_core.errors import KpiError
from kpi_core.obs.logging import log_event
from kpi_core.validation import sanitize_text

logger = logging.getLogger(__name__)
TOOL_BUDGET_RESULT = (
    '{"error":{"code":"tool_budget","message":"too many tool calls in one turn; call fewer tools"}}'
)


def fallback_text(stopped: StoppedReason, steps: list[Step]) -> str:
    calls = len(steps)
    if stopped == "refusal":
        return "The model declined to answer this request."
    if stopped == "max_iterations":
        return (
            f"I stopped after {calls} tool call(s) without reaching a final answer. "
            "Try a narrower question, for example one company and one KPI."
        )
    if stopped == "wall_clock":
        return "This took too long to complete. Please retry with a narrower question."
    if stopped == "max_tokens":
        return "The answer was cut off by the output limit. Please ask for a narrower range."
    if stopped == "provider_error":
        return (
            "The language model is unavailable right now. "
            "Your tool calls were recorded; please retry."
        )
    return "I could not produce an answer from the available data."


class AgentRunner:
    def __init__(
        self,
        provider: LLMProvider,
        gateway: McpToolGateway,
        store: ConversationStore,
        settings: ApiSettings,
    ) -> None:
        self.provider = provider
        self.gateway = gateway
        self.store = store
        self.settings = settings

    async def run(
        self, ctx: RequestContext, *, conversation_id: str | None, user_text: str
    ) -> AsyncIterator[AgentEvent]:
        settings = self.settings
        text = sanitize_text(user_text, max_len=settings.agent_max_message_chars, field="message")
        conversation = await self.store.open(ctx, conversation_id)
        yield SessionEvent(conversation.id, ctx.trace_id, self.provider.name, self.provider.model)
        history = self.store.history_messages(conversation, settings.agent_history_window)
        user_message = await self.store.append_user(ctx, conversation, text)
        messages: list[dict[str, Any]] = [*history, {"role": "user", "content": text}]

        steps: list[Step] = []
        answer: list[str] = []
        usage = Usage()
        stopped: StoppedReason = "end_turn"
        iteration = 0
        deadline = time.monotonic() + settings.agent_max_wall_clock_s
        ledger = CallLedger()
        started = time.perf_counter()
        try:
            async with self.gateway.session(ctx.trace_id) as session:
                specs = {s.name: s for s in await self.gateway.cached_tools(session)}
                tools = [to_anthropic_tool(s) for s in specs.values()]
                system = build_system_prompt(set(specs))
                for iteration in range(1, settings.agent_max_iterations + 1):
                    if time.monotonic() > deadline:
                        stopped = "wall_clock"
                        break
                    pending: list[ToolUseComplete] = []
                    stop_reason = "end_turn"
                    async for event in self.provider.stream_turn(
                        system=system, messages=messages, tools=tools
                    ):
                        if isinstance(event, TextDelta):
                            answer.append(event.text)
                            yield TextDeltaEvent(event.text)
                        elif isinstance(event, ToolUseStart):
                            continue
                        elif isinstance(event, ToolUseComplete):
                            pending.append(event)
                        elif isinstance(event, TurnEnd):
                            usage = usage + event.usage
                            stop_reason = event.stop_reason
                            if event.assistant_content:
                                messages.append(
                                    {"role": "assistant", "content": event.assistant_content}
                                )
                    log_event(
                        "llm_turn",
                        provider=self.provider.name,
                        model=self.provider.model,
                        iteration=iteration,
                        stop_reason=stop_reason,
                        tool_uses=len(pending),
                    )
                    if stop_reason == "refusal":
                        stopped = "refusal"
                        break
                    if stop_reason == "max_tokens" and pending:
                        stopped = "max_tokens"  # never execute a possibly truncated tool input
                        break
                    if stop_reason == "pause_turn":
                        continue
                    if not pending:
                        stopped = "end_turn"
                        break
                    results: list[dict[str, Any]] = []
                    for call in pending[: settings.agent_max_parallel_tools]:
                        step, rejection = self._prepare(call, specs, ledger, iteration)
                        if rejection is not None:
                            outcome = rejection
                        else:
                            yield ToolCallStartedEvent(step)
                            outcome = await self._call(
                                session, step.tool, step.arguments, conversation.id
                            )
                        ledger.record(step.tool, step.arguments, outcome)
                        step.status = outcome.status
                        step.duration_ms = outcome.duration_ms
                        step.error = outcome.error
                        step.result_preview = preview(outcome.text)
                        steps.append(step)
                        yield ToolCallFinishedEvent(step)
                        results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": call.id,
                                "content": truncate_result(
                                    outcome.text, settings.agent_max_result_chars
                                ),
                                "is_error": outcome.status != "ok",
                            }
                        )
                    for extra in pending[settings.agent_max_parallel_tools :]:
                        results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": extra.id,
                                "content": TOOL_BUDGET_RESULT,
                                "is_error": True,
                            }
                        )
                    messages.append(
                        {"role": "user", "content": results}
                    )  # ALL results in ONE message
                else:
                    stopped = "max_iterations"
        except KpiError as error:
            stopped = "provider_error"
            final_text = fallback_text(stopped, steps)
            await self._persist(
                ctx, conversation, user_message.seq + 1, final_text, steps, usage, stopped
            )
            yield ErrorEvent(error.code, error.detail, ctx.trace_id, steps)
            return
        except Exception:
            logger.exception("agent_run_failed", extra={"trace_id": ctx.trace_id})
            stopped = "provider_error"
            final_text = fallback_text(stopped, steps)
            await self._persist(
                ctx, conversation, user_message.seq + 1, final_text, steps, usage, stopped
            )
            yield ErrorEvent(
                "internal_error", "The agent failed unexpectedly.", ctx.trace_id, steps
            )
            return

        final_text = "".join(answer).strip() or fallback_text(stopped, steps)
        if not answer:
            for chunk in (final_text,):
                yield TextDeltaEvent(chunk)
        message = await self._persist(
            ctx, conversation, user_message.seq + 1, final_text, steps, usage, stopped
        )
        log_event(
            "agent_run",
            conversation_id=conversation.id,
            iterations=iteration,
            tool_calls=len(steps),
            stopped_reason=stopped,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        yield FinalEvent(message.id, final_text, steps, usage, iteration, stopped)

    def _prepare(
        self,
        call: ToolUseComplete,
        specs: dict[str, Any],
        ledger: CallLedger,
        iteration: int,
    ) -> tuple[Step, ToolOutcome | None]:
        """Build the step and decide whether the call is rejected before execution."""
        step = Step(
            id=call.id, tool=call.name, arguments=dict(call.input or {}), iteration=iteration
        )
        if call.parse_error or call.input is None:
            return step, ToolOutcome.rejected(
                "invalid_tool_input", f"Tool input could not be parsed: {call.parse_error}"
            )
        if call.name not in specs:
            return step, ToolOutcome.rejected(
                "unknown_tool", f"No tool named '{call.name}'.", available=sorted(specs)
            )
        args, dropped = sanitize_tool_args(call.input, specs[call.name])
        if dropped:
            log_event("tool_args_dropped", tool=call.name, dropped=dropped)
        step.arguments = args
        verdict = ledger.verdict(call.name, args)
        if verdict == "repeated_failing_call":
            return step, ToolOutcome.rejected(
                verdict,
                "This exact call was already made and failed; use the suggestions or answer "
                "with what you have.",
            )
        if verdict == "repeated_identical_call":
            return step, ToolOutcome.rejected(
                verdict, "This exact call already succeeded twice; do not repeat it."
            )
        return step, None

    async def _call(
        self, session: McpSession, name: str, args: dict[str, Any], conversation_id: str
    ) -> ToolOutcome:
        try:
            return await asyncio.wait_for(
                session.call(name, args, conversation_id=conversation_id),
                timeout=self.settings.agent_tool_timeout_s,
            )
        except TimeoutError:
            return ToolOutcome.failed(
                "tool_timeout",
                f"{name} exceeded {self.settings.agent_tool_timeout_s}s",
                status="timeout",
            )
        except Exception as exc:
            logger.warning("mcp_call_failed", extra={"tool": name, "error": type(exc).__name__})
            return ToolOutcome.failed(
                "upstream_unavailable", "The KPI tool server could not be reached."
            )

    async def _persist(
        self,
        ctx: RequestContext,
        conversation: Any,
        seq: int,
        text: str,
        steps: list[Step],
        usage: Usage,
        stopped: StoppedReason,
    ) -> Any:
        return await self.store.append_assistant(
            ctx, conversation, seq=seq, text=text, steps=steps, usage=usage, stopped_reason=stopped
        )
