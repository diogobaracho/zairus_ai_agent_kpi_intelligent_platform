import logging

import pytest

from kpi_core.context import RequestContext
from kpi_core.errors import ConversationNotFound
from kpi_core.models import ChatMessage, ToolCallAudit
from kpi_core.repositories.memory import InMemoryAuditRepository, InMemoryChatRepository
from kpi_core.services import audit, chat


async def test_record_and_query(ctx: RequestContext) -> None:
    repo = InMemoryAuditRepository()
    for status in ("ok", "error"):
        await audit.record_tool_call(
            repo,
            ToolCallAudit(
                trace_id="t1",
                tool_name="get_kpi_qtd",
                arguments={"ticker": "ORBY"},
                status=status,
                duration_ms=3,
            ),
        )
    await audit.record_tool_call(
        repo, ToolCallAudit(trace_id="t2", tool_name="search_companies", status="ok")
    )
    assert len(await audit.query_tool_calls(repo, tenant_id="default", trace_id="t1")) == 2
    assert len(await audit.query_tool_calls(repo, tenant_id="default", status="error")) == 1
    assert len(await audit.query_tool_calls(repo, tenant_id="other")) == 0
    latest = await audit.query_tool_calls(repo, tenant_id="default", limit=1)
    assert latest[0].tool_name == "search_companies"


class _BrokenAudit(InMemoryAuditRepository):
    async def record(self, audit: ToolCallAudit) -> ToolCallAudit:
        raise RuntimeError("db down")


async def test_record_never_raises(ctx: RequestContext, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        await audit.record_tool_call(
            _BrokenAudit(), ToolCallAudit(trace_id="t", tool_name="x", status="ok")
        )
    assert any("audit_failed" in r.getMessage() for r in caplog.records)


async def test_conversations(ctx: RequestContext) -> None:
    repo = InMemoryChatRepository()
    conv = await chat.get_or_create_conversation(ctx, repo, None)
    msg = ChatMessage(
        id="m1", conversation_id=conv.id, seq=1, role="user", content="hi ORBY", trace_id="t"
    )
    await chat.append_message(ctx, repo, msg)
    loaded = await chat.get_conversation(ctx, repo, conv.id)
    assert loaded.messages[0].content == "hi ORBY" and loaded.title == "hi ORBY"
    assert (await chat.list_conversations(ctx, repo))[0].id == conv.id
    with pytest.raises(ConversationNotFound):
        await chat.get_conversation(ctx, repo, "missing")
    other = RequestContext(trace_id="x", tenant_id="other", caller="test")
    with pytest.raises(ConversationNotFound):
        await chat.get_conversation(other, repo, conv.id)
