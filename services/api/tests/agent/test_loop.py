import asyncio

import pytest

from kpi_api.agent.providers.base import LLMProvider
from kpi_api.agent.providers.stub import StubLLMProvider, StubTurn
from kpi_api.agent.tools import McpToolGateway
from kpi_api.agent.types import (
    ErrorEvent,
    FinalEvent,
    SessionEvent,
    TextDeltaEvent,
    ToolCallFinishedEvent,
)
from kpi_api.settings import ApiSettings
from kpi_core.errors import UpstreamUnavailable
from kpi_core.repositories.memory import InMemoryAuditRepository, InMemoryChatRepository

from .conftest import collect, make_runner, script, tool_call


def names(events):  # type: ignore[no-untyped-def]
    return [type(e).__name__ for e in events]


async def test_happy_path_qtd(
    gateway: McpToolGateway,
    chat_repo: InMemoryChatRepository,
    agent_settings: ApiSettings,
    ctx,
    audit_repo: InMemoryAuditRepository,
) -> None:  # type: ignore[no-untyped-def]
    provider = StubLLMProvider()
    runner = make_runner(provider, gateway, chat_repo, agent_settings)
    events = await collect(runner, ctx, "What is ORBY total revenue QTD?")
    assert isinstance(events[0], SessionEvent) and events[0].trace_id == ctx.trace_id
    finished = [e for e in events if isinstance(e, ToolCallFinishedEvent)]
    assert [s.step.tool for s in finished] == ["get_kpi_qtd"] and finished[0].step.status == "ok"
    assert finished[0].step.arguments == {"ticker": "ORBY", "kpi": "total_revenue"}
    final = events[-1]
    assert (
        isinstance(final, FinalEvent)
        and final.stopped_reason == "end_turn"
        and "2026-09-15" in final.answer
    )
    assert any(isinstance(e, TextDeltaEvent) for e in events)
    # persisted: user + assistant with steps; audit row carries the same trace id
    conv = await chat_repo.get_conversation(ctx, events[0].conversation_id)
    assert conv is not None and [m.role for m in conv.messages] == ["user", "assistant"]
    assert (
        conv.messages[1].steps[0]["tool"] == "get_kpi_qtd"
        and conv.messages[1].stopped_reason == "end_turn"
    )
    assert (
        audit_repo.rows[-1].trace_id == ctx.trace_id
        and audit_repo.rows[-1].conversation_id == conv.id
    )
    assert audit_repo.rows[-1].caller == "agent"
    # all tool results of a turn were sent back in ONE user message
    second_turn = provider.seen_messages[1]
    assert second_turn[-1]["role"] == "user" and all(
        b["type"] == "tool_result" for b in second_turn[-1]["content"]
    )


async def test_recovery_after_company_not_found(gateway, chat_repo, agent_settings, ctx) -> None:  # type: ignore[no-untyped-def]
    runner = make_runner(StubLLMProvider(), gateway, chat_repo, agent_settings)
    events = await collect(runner, ctx, "Show ORBYY revenue history")
    finished = [e.step for e in events if isinstance(e, ToolCallFinishedEvent)]
    assert [s.status for s in finished] == ["error", "ok"]
    assert finished[0].error is not None and finished[0].error["code"] == "company_not_found"
    assert finished[1].arguments["ticker"] == "ORBY"
    final = events[-1]
    assert isinstance(final, FinalEvent) and "2026Q2" in final.answer


async def test_history_preserved_across_turns(gateway, chat_repo, agent_settings, ctx) -> None:  # type: ignore[no-untyped-def]
    provider = StubLLMProvider()
    runner = make_runner(provider, gateway, chat_repo, agent_settings)
    first = await collect(runner, ctx, "What is ORBY total revenue QTD?")
    conv_id = first[0].conversation_id  # type: ignore[union-attr]
    await collect(runner, ctx, "And KSTL ARR history?", conversation_id=conv_id)
    later = provider.seen_messages[-1]
    assert (
        later[0]["content"] == "What is ORBY total revenue QTD?" and later[1]["role"] == "assistant"
    )
    conv = await chat_repo.get_conversation(ctx, conv_id)
    assert conv is not None and len(conv.messages) == 4


async def test_unknown_tool_is_rejected(gateway, chat_repo, agent_settings, ctx) -> None:  # type: ignore[no-untyped-def]
    provider = script(
        StubTurn(tool_calls=[tool_call("drop_table", ticker="ORBY")]), StubTurn(text="ok")
    )
    events = await collect(
        runner := make_runner(provider, gateway, chat_repo, agent_settings), ctx, "x"
    )
    step = next(e.step for e in events if isinstance(e, ToolCallFinishedEvent))
    assert (
        step.status == "rejected"
        and step.error["code"] == "unknown_tool"
        and "get_kpi_qtd" in step.error["available"]
    )  # type: ignore[index]
    assert runner is not None


async def test_parse_error_is_rejected(gateway, chat_repo, agent_settings, ctx) -> None:  # type: ignore[no-untyped-def]
    provider = script(
        StubTurn(parse_error="unterminated string", stop_reason="tool_use"), StubTurn(text="ok")
    )
    events = await collect(make_runner(provider, gateway, chat_repo, agent_settings), ctx, "x")
    step = next(e.step for e in events if isinstance(e, ToolCallFinishedEvent))
    assert step.status == "rejected" and step.error["code"] == "invalid_tool_input"  # type: ignore[index]


async def test_identity_keys_dropped(gateway, chat_repo, agent_settings, ctx) -> None:  # type: ignore[no-untyped-def]
    provider = script(
        StubTurn(
            tool_calls=[tool_call("get_kpi_qtd", ticker="ORBY", kpi="revenue", tenant_id="evil")]
        ),
        StubTurn(text="ok"),
    )
    events = await collect(make_runner(provider, gateway, chat_repo, agent_settings), ctx, "x")
    step = next(e.step for e in events if isinstance(e, ToolCallFinishedEvent))
    assert step.status == "ok" and "tenant_id" not in step.arguments


async def test_repeated_failing_call_rejected(gateway, chat_repo, agent_settings, ctx) -> None:  # type: ignore[no-untyped-def]
    bad = tool_call("get_kpi_qtd", ticker="ORBYY", kpi="revenue")
    provider = script(
        StubTurn(tool_calls=[bad]), StubTurn(tool_calls=[bad]), StubTurn(text="giving up")
    )
    events = await collect(make_runner(provider, gateway, chat_repo, agent_settings), ctx, "x")
    statuses = [
        (e.step.status, (e.step.error or {}).get("code"))
        for e in events
        if isinstance(e, ToolCallFinishedEvent)
    ]
    assert statuses == [("error", "company_not_found"), ("rejected", "repeated_failing_call")]


async def test_max_iterations_stops(gateway, chat_repo, agent_settings, ctx) -> None:  # type: ignore[no-untyped-def]
    settings = agent_settings.model_copy(update={"agent_max_iterations": 3})
    provider = script(
        *[StubTurn(tool_calls=[tool_call("search_companies", query=f"q{i}")]) for i in range(10)]
    )
    events = await collect(make_runner(provider, gateway, chat_repo, settings), ctx, "x")
    final = events[-1]
    assert (
        isinstance(final, FinalEvent)
        and final.stopped_reason == "max_iterations"
        and final.iterations == 3
    )
    assert len(final.steps) == 3 and "stopped after 3" in final.answer


async def test_tool_budget_per_turn(gateway, chat_repo, agent_settings, ctx) -> None:  # type: ignore[no-untyped-def]
    settings = agent_settings.model_copy(update={"agent_max_parallel_tools": 1})
    provider = script(
        StubTurn(
            tool_calls=[
                tool_call("search_companies", query="a"),
                tool_call("search_companies", query="b"),
            ]
        ),
        StubTurn(text="ok"),
    )
    events = await collect(make_runner(provider, gateway, chat_repo, settings), ctx, "x")
    assert len([e for e in events if isinstance(e, ToolCallFinishedEvent)]) == 1
    results = provider.seen_messages[1][-1]["content"]
    assert len(results) == 2 and results[1]["is_error"] and "tool_budget" in results[1]["content"]


async def test_tool_timeout(gateway, chat_repo, agent_settings, ctx, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    settings = agent_settings.model_copy(update={"agent_tool_timeout_s": 0.05})
    from kpi_api.agent import tools as tools_module

    async def slow(self, name, args, *, conversation_id=None):  # type: ignore[no-untyped-def]
        await asyncio.sleep(0.5)
        raise AssertionError("should have timed out")

    monkeypatch.setattr(tools_module.McpSession, "call", slow)
    provider = script(
        StubTurn(tool_calls=[tool_call("get_kpi_qtd", ticker="ORBY", kpi="revenue")]),
        StubTurn(text="ok"),
    )
    events = await collect(make_runner(provider, gateway, chat_repo, settings), ctx, "x")
    step = next(e.step for e in events if isinstance(e, ToolCallFinishedEvent))
    assert step.status == "timeout" and step.error["code"] == "tool_timeout"  # type: ignore[index]


async def test_result_truncation(gateway, chat_repo, agent_settings, ctx) -> None:  # type: ignore[no-untyped-def]
    settings = agent_settings.model_copy(update={"agent_max_result_chars": 200})
    provider = script(
        StubTurn(tool_calls=[tool_call("get_kpi_history", ticker="ORBY", kpi="revenue")]),
        StubTurn(text="ok"),
    )
    await collect(make_runner(provider, gateway, chat_repo, settings), ctx, "x")
    content = provider.seen_messages[1][-1]["content"][0]["content"]
    assert len(content) < 300 and "[truncated" in content


async def test_refusal_and_max_tokens(gateway, chat_repo, agent_settings, ctx) -> None:  # type: ignore[no-untyped-def]
    events = await collect(
        make_runner(script(StubTurn(stop_reason="refusal")), gateway, chat_repo, agent_settings),
        ctx,
        "x",
    )
    final = events[-1]
    assert (
        isinstance(final, FinalEvent)
        and final.stopped_reason == "refusal"
        and "declined" in final.answer
    )
    provider = script(
        StubTurn(
            tool_calls=[tool_call("get_kpi_qtd", ticker="ORBY", kpi="revenue")],
            stop_reason="max_tokens",
        )
    )
    events = await collect(make_runner(provider, gateway, chat_repo, agent_settings), ctx, "x")
    assert not any(
        isinstance(e, ToolCallFinishedEvent) for e in events
    )  # truncated input never executed
    assert isinstance(events[-1], FinalEvent) and events[-1].stopped_reason == "max_tokens"


async def test_provider_outage_emits_error_and_persists(
    gateway, chat_repo, agent_settings, ctx
) -> None:  # type: ignore[no-untyped-def]
    class Broken(LLMProvider):
        name, model = "broken", "x"

        async def stream_turn(self, *, system, messages, tools):  # type: ignore[no-untyped-def]
            raise UpstreamUnavailable("LLM down")
            yield  # pragma: no cover

    events = await collect(make_runner(Broken(), gateway, chat_repo, agent_settings), ctx, "x")
    assert isinstance(events[-1], ErrorEvent) and events[-1].code == "upstream_unavailable"
    conv = await chat_repo.get_conversation(ctx, events[0].conversation_id)  # type: ignore[union-attr]
    assert conv is not None and conv.messages[-1].stopped_reason == "provider_error"


async def test_message_too_long_rejected(gateway, chat_repo, agent_settings, ctx) -> None:  # type: ignore[no-untyped-def]
    runner = make_runner(StubLLMProvider(), gateway, chat_repo, agent_settings)
    with pytest.raises(Exception):  # noqa: B017 - ValidationError from sanitize_text before any event
        await collect(runner, ctx, "x" * 5000)
