"""Anthropic Messages API provider (streaming). The only module that imports the SDK."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, cast

import anthropic

from kpi_api.agent.providers.base import LLMProvider
from kpi_api.agent.types import (
    LLMEvent,
    StopReason,
    TextDelta,
    ToolUseComplete,
    ToolUseStart,
    TurnEnd,
    Usage,
)
from kpi_api.settings import ApiSettings
from kpi_core.errors import UpstreamUnavailable, ValidationError

FALLBACK_BETA = "server-side-fallback-2026-07-01"


def content_to_dicts(blocks: list[Any]) -> list[dict[str, Any]]:
    """Serialise response blocks for replay; thinking blocks must be echoed back unchanged."""
    return [block.model_dump(exclude_none=True) for block in blocks]


def map_stop_reason(value: str | None) -> StopReason:
    allowed = ("end_turn", "tool_use", "max_tokens", "refusal", "pause_turn", "stop_sequence")
    return cast(StopReason, value) if value in allowed else "end_turn"


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(
        self, settings: ApiSettings, client: anthropic.AsyncAnthropic | None = None
    ) -> None:
        self.settings = settings
        self.model = settings.llm_model
        self.client = client or anthropic.AsyncAnthropic(
            timeout=settings.llm_timeout_s, max_retries=2
        )

    async def stream_turn(
        self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AsyncIterator[LLMEvent]:
        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.settings.llm_max_tokens,
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": messages,
            "tools": tools,
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": self.settings.llm_effort},
        }
        try:
            stream_cm: Any
            if self.settings.llm_fallbacks == "default":
                stream_cm = self.client.beta.messages.stream(
                    **params, betas=[FALLBACK_BETA], fallbacks="default"
                )
            else:
                stream_cm = self.client.messages.stream(**params)
            async with stream_cm as stream:
                async for event in stream:
                    if event.type == "text":
                        yield TextDelta(event.text)
                    elif (
                        event.type == "content_block_start"
                        and event.content_block.type == "tool_use"
                    ):
                        yield ToolUseStart(event.content_block.id, event.content_block.name)
                final = await stream.get_final_message()
        except anthropic.AuthenticationError as exc:
            raise UpstreamUnavailable("LLM provider rejected the API key", reason="auth") from exc
        except anthropic.RateLimitError as exc:
            retry_after = exc.response.headers.get("retry-after", "30")
            raise UpstreamUnavailable(
                "LLM provider is rate limiting requests",
                reason="llm_rate_limited",
                retry_after=retry_after,
            ) from exc
        except anthropic.BadRequestError as exc:
            raise ValidationError(f"LLM request rejected: {exc.message}") from exc
        except anthropic.APIStatusError as exc:
            raise UpstreamUnavailable(
                f"LLM provider error ({exc.status_code})", reason="llm_status"
            ) from exc
        except anthropic.APIConnectionError as exc:
            raise UpstreamUnavailable(
                "Cannot reach the LLM provider", reason="llm_connection"
            ) from exc
        except ValueError as exc:  # unparseable tool input JSON surfaced by the stream
            yield ToolUseComplete(id="unparsed", name="unknown", input=None, parse_error=str(exc))
            yield TurnEnd("end_turn", Usage(), [])
            return
        for block in final.content:
            if block.type == "tool_use":
                raw = block.input
                yield ToolUseComplete(
                    id=block.id,
                    name=block.name,
                    input=raw if isinstance(raw, dict) else None,
                    parse_error=None if isinstance(raw, dict) else "tool input is not an object",
                )
        yield TurnEnd(
            stop_reason=map_stop_reason(final.stop_reason),
            usage=Usage(final.usage.input_tokens, final.usage.output_tokens),
            assistant_content=content_to_dicts(final.content),
        )
