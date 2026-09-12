"""Conversation persistence for the chat agent."""

from __future__ import annotations

import uuid

from kpi_core.context import RequestContext
from kpi_core.errors import ConversationNotFound
from kpi_core.models import ChatMessage, Conversation
from kpi_core.repositories.protocols import ChatRepository


def new_conversation_id() -> str:
    return uuid.uuid4().hex


async def get_or_create_conversation(
    ctx: RequestContext, repo: ChatRepository, conversation_id: str | None
) -> Conversation:
    if conversation_id:
        existing = await repo.get_conversation(ctx, conversation_id)
        if existing is None:
            raise ConversationNotFound(f"No conversation '{conversation_id}'")
        return existing
    return await repo.create_conversation(ctx, new_conversation_id())


async def get_conversation(
    ctx: RequestContext, repo: ChatRepository, conversation_id: str
) -> Conversation:
    conv = await repo.get_conversation(ctx, conversation_id)
    if conv is None:
        raise ConversationNotFound(f"No conversation '{conversation_id}'")
    return conv


async def list_conversations(
    ctx: RequestContext, repo: ChatRepository, *, limit: int = 20
) -> list[Conversation]:
    return await repo.list_conversations(ctx, limit=min(limit, 100))


async def append_message(
    ctx: RequestContext, repo: ChatRepository, message: ChatMessage
) -> ChatMessage:
    return await repo.append_message(ctx, message)
