from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from sse_starlette.sse import EventSourceResponse

from kpi_api.agent.loop import AgentRunner
from kpi_api.agent.sse import to_sse
from kpi_api.dependencies import get_chat_repo, get_context
from kpi_api.schemas.chat import ChatMessageOut, ChatRequest, ConversationList, ConversationOut
from kpi_core.context import RequestContext
from kpi_core.models import Conversation
from kpi_core.repositories.protocols import ChatRepository
from kpi_core.services import chat as chat_service

router = APIRouter(prefix="/v1/chat", tags=["chat"])


def _conversation_out(conv: Conversation) -> ConversationOut:
    return ConversationOut(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at.isoformat() if conv.created_at else None,
        updated_at=conv.updated_at.isoformat() if conv.updated_at else None,
        messages=[
            ChatMessageOut(
                id=m.id,
                seq=m.seq,
                role=m.role,
                content=m.content,
                steps=m.steps,
                usage=m.usage,
                trace_id=m.trace_id,
                stopped_reason=m.stopped_reason,
                created_at=m.created_at.isoformat() if m.created_at else None,
            )
            for m in conv.messages
        ],
    )


@router.post(
    "",
    summary="Ask a question; the answer streams as server-sent events with every tool call",
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def chat(
    body: ChatRequest,
    request: Request,
    ctx: Annotated[RequestContext, Depends(get_context)],
) -> EventSourceResponse:
    runner: AgentRunner = request.app.state.agent_runner
    if (
        body.conversation_id
    ):  # validate before the stream starts so a 404 is a normal problem document
        await chat_service.get_conversation(ctx, request.app.state.chat_repo, body.conversation_id)

    async def events() -> AsyncIterator[dict[str, Any]]:
        seq = 0
        async for event in runner.run(
            ctx, conversation_id=body.conversation_id, user_text=body.message
        ):
            seq += 1
            yield to_sse(event, seq)

    return EventSourceResponse(
        events(),
        ping=15,
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "X-Correlation-Id": ctx.trace_id,
        },
    )


@router.get("/conversations", response_model=ConversationList, summary="Recent conversations")
async def list_conversations(
    ctx: Annotated[RequestContext, Depends(get_context)],
    repo: Annotated[ChatRepository, Depends(get_chat_repo)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ConversationList:
    items = await chat_service.list_conversations(ctx, repo, limit=limit)
    return ConversationList(items=[_conversation_out(c) for c in items])


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationOut,
    summary="One conversation with its messages and tool steps",
)
async def get_conversation(
    conversation_id: str,
    ctx: Annotated[RequestContext, Depends(get_context)],
    repo: Annotated[ChatRepository, Depends(get_chat_repo)],
) -> ConversationOut:
    return _conversation_out(await chat_service.get_conversation(ctx, repo, conversation_id))
