"""Conversation persistence: history for the model, rows for the audit trail."""

from __future__ import annotations

import uuid
from typing import Any

from kpi_api.agent.types import Step, Usage
from kpi_core.context import RequestContext
from kpi_core.models import ChatMessage, Conversation
from kpi_core.repositories.protocols import ChatRepository
from kpi_core.services import chat as chat_service


class ConversationStore:
    def __init__(self, repo: ChatRepository) -> None:
        self.repo = repo

    async def open(self, ctx: RequestContext, conversation_id: str | None) -> Conversation:
        return await chat_service.get_or_create_conversation(ctx, self.repo, conversation_id)

    @staticmethod
    def history_messages(conversation: Conversation, window: int) -> list[dict[str, Any]]:
        """Prior user/assistant text only (tool blocks are not replayed: small context, no
        coupling to a provider's thinking-block replay rules)."""
        recent = conversation.messages[-window:] if window else []
        history: list[dict[str, Any]] = []
        for message in recent:
            if message.content:
                history.append({"role": message.role, "content": message.content})
        return history

    async def append_user(
        self, ctx: RequestContext, conversation: Conversation, text: str
    ) -> ChatMessage:
        message = ChatMessage(
            id=uuid.uuid4().hex,
            conversation_id=conversation.id,
            seq=len(conversation.messages) + 1,
            role="user",
            content=text,
            trace_id=ctx.trace_id,
        )
        return await chat_service.append_message(ctx, self.repo, message)

    async def append_assistant(
        self,
        ctx: RequestContext,
        conversation: Conversation,
        *,
        seq: int,
        text: str,
        steps: list[Step],
        usage: Usage,
        stopped_reason: str,
    ) -> ChatMessage:
        message = ChatMessage(
            id=uuid.uuid4().hex,
            conversation_id=conversation.id,
            seq=seq,
            role="assistant",
            content=text,
            steps=[s.to_dict() for s in steps],
            usage={"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens},
            trace_id=ctx.trace_id,
            stopped_reason=stopped_reason,
        )
        return await chat_service.append_message(ctx, self.repo, message)
