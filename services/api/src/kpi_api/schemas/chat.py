from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from kpi_core.models import ToolCallAudit


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=4000, description="The user's question")
    conversation_id: str | None = Field(
        default=None, min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"
    )


class ChatMessageOut(BaseModel):
    id: str
    seq: int
    role: str
    content: str
    steps: list[dict[str, Any]]
    usage: dict[str, Any] | None
    trace_id: str
    stopped_reason: str | None
    created_at: str | None


class ConversationOut(BaseModel):
    id: str
    title: str | None
    created_at: str | None
    updated_at: str | None
    messages: list[ChatMessageOut]


class ConversationList(BaseModel):
    items: list[ConversationOut]


class AuditList(BaseModel):
    items: list[ToolCallAudit]


class ToolInfo(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    strict: bool


class ToolList(BaseModel):
    items: list[ToolInfo]
