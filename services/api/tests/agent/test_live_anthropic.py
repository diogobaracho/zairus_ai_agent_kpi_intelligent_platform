"""One real tool-calling turn against Anthropic. Never runs in CI (`-m live`, needs a key)."""

import os

import pytest

from kpi_api.agent.providers.anthropic_provider import AnthropicProvider
from kpi_api.agent.types import FinalEvent, ToolCallFinishedEvent
from kpi_api.settings import ApiSettings
from kpi_core.repositories.memory import InMemoryChatRepository

from .conftest import collect, make_runner

pytestmark = pytest.mark.live


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_real_model_calls_tools(gateway, ctx) -> None:  # type: ignore[no-untyped-def]
    settings = ApiSettings(env="test", llm_provider="anthropic", mcp_mode="inprocess")
    runner = make_runner(AnthropicProvider(settings), gateway, InMemoryChatRepository(), settings)  # type: ignore[arg-type]
    events = await collect(
        runner,
        ctx,
        "What's ORBY's QTD total revenue this quarter, and how does it compare to last quarter?",
    )
    tools_called = [e.step.tool for e in events if isinstance(e, ToolCallFinishedEvent)]
    final = events[-1]
    assert "get_kpi_qtd" in tools_called
    assert isinstance(final, FinalEvent) and "ORBY" in final.answer and "2026" in final.answer
    print("\nLIVE TRANSCRIPT tools:", tools_called, "\nanswer:", final.answer)
