"""AgentEvent -> server-sent event dicts consumed by sse-starlette."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from kpi_api.agent.types import (
    AgentEvent,
    ErrorEvent,
    FinalEvent,
    SessionEvent,
    TextDeltaEvent,
    ToolCallFinishedEvent,
    ToolCallStartedEvent,
)


def event_name(event: AgentEvent) -> str:
    return {
        SessionEvent: "session",
        TextDeltaEvent: "text_delta",
        ToolCallStartedEvent: "tool_call_started",
        ToolCallFinishedEvent: "tool_call_finished",
        FinalEvent: "final",
        ErrorEvent: "error",
    }[type(event)]


def event_data(event: AgentEvent) -> dict[str, Any]:
    if isinstance(event, ToolCallStartedEvent):
        step = event.step
        return {
            "id": step.id,
            "tool": step.tool,
            "arguments": step.arguments,
            "iteration": step.iteration,
        }
    if isinstance(event, ToolCallFinishedEvent):
        return event.step.to_dict()
    if isinstance(event, FinalEvent):
        return {
            "message_id": event.message_id,
            "answer": event.answer,
            "steps": [s.to_dict() for s in event.steps],
            "usage": {
                "input_tokens": event.usage.input_tokens,
                "output_tokens": event.usage.output_tokens,
                "iterations": event.iterations,
                "tool_calls": len(event.steps),
            },
            "stopped_reason": event.stopped_reason,
        }
    if isinstance(event, ErrorEvent):
        return {
            "code": event.code,
            "message": event.message,
            "trace_id": event.trace_id,
            "steps": [s.to_dict() for s in event.steps],
        }
    return asdict(event)


def to_sse(event: AgentEvent, seq: int) -> dict[str, Any]:
    return {
        "event": event_name(event),
        "data": json.dumps(event_data(event), default=str),
        "id": str(seq),
    }
