"""Event and value types shared by providers, the loop, SSE and persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

StopReason = Literal["end_turn", "tool_use", "max_tokens", "refusal", "pause_turn", "stop_sequence"]
StepStatus = Literal["ok", "error", "timeout", "rejected"]
StoppedReason = Literal[
    "end_turn",
    "max_iterations",
    "wall_clock",
    "refusal",
    "max_tokens",
    "provider_error",
    "tool_budget",
]


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            self.input_tokens + other.input_tokens, self.output_tokens + other.output_tokens
        )


# --- provider -> loop ------------------------------------------------------------------------
@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class ToolUseStart:
    id: str
    name: str


@dataclass(frozen=True)
class ToolUseComplete:
    id: str
    name: str
    input: dict[str, Any] | None
    parse_error: str | None = None


@dataclass(frozen=True)
class TurnEnd:
    stop_reason: StopReason
    usage: Usage
    assistant_content: list[dict[str, Any]]


LLMEvent = TextDelta | ToolUseStart | ToolUseComplete | TurnEnd


# --- MCP gateway -> loop ---------------------------------------------------------------------
@dataclass(frozen=True)
class McpToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class ToolOutcome:
    status: StepStatus
    text: str
    error: dict[str, Any] | None = None
    duration_ms: int = 0
    structured: dict[str, Any] | None = None

    @classmethod
    def rejected(cls, code: str, message: str, **extra: Any) -> ToolOutcome:
        error = {"code": code, "message": message, "retryable": True, **extra}
        return cls(status="rejected", text=_error_text(error), error=error)

    @classmethod
    def failed(cls, code: str, message: str, status: StepStatus = "error") -> ToolOutcome:
        error = {"code": code, "message": message, "retryable": code != "internal_error"}
        return cls(status=status, text=_error_text(error), error=error)


def _error_text(error: dict[str, Any]) -> str:
    import json

    return json.dumps({"error": error})


# --- loop -> SSE / persistence ---------------------------------------------------------------
@dataclass
class Step:
    id: str
    tool: str
    arguments: dict[str, Any]
    iteration: int
    status: StepStatus = "ok"
    duration_ms: int = 0
    result_preview: str = ""
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tool": self.tool,
            "arguments": self.arguments,
            "iteration": self.iteration,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "result_preview": self.result_preview,
            "error": self.error,
        }


@dataclass(frozen=True)
class SessionEvent:
    conversation_id: str
    trace_id: str
    provider: str
    model: str


@dataclass(frozen=True)
class TextDeltaEvent:
    delta: str


@dataclass(frozen=True)
class ToolCallStartedEvent:
    step: Step


@dataclass(frozen=True)
class ToolCallFinishedEvent:
    step: Step


@dataclass(frozen=True)
class FinalEvent:
    message_id: str
    answer: str
    steps: list[Step]
    usage: Usage
    iterations: int
    stopped_reason: StoppedReason


@dataclass(frozen=True)
class ErrorEvent:
    code: str
    message: str
    trace_id: str
    steps: list[Step] = field(default_factory=list)


AgentEvent = (
    SessionEvent
    | TextDeltaEvent
    | ToolCallStartedEvent
    | ToolCallFinishedEvent
    | FinalEvent
    | ErrorEvent
)
