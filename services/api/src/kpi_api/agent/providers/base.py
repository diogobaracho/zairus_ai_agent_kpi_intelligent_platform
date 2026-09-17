from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from kpi_api.agent.types import LLMEvent


class LLMProvider(ABC):
    name: str = "base"
    model: str = ""

    @abstractmethod
    def stream_turn(
        self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AsyncIterator[LLMEvent]:
        """Yield TextDelta / ToolUseStart / ToolUseComplete events and finish with TurnEnd."""
        raise NotImplementedError
