"""LLM providers. `anthropic` needs a key; `stub` is deterministic and always available."""

from __future__ import annotations

import logging

from kpi_api.agent.providers.base import LLMProvider
from kpi_api.agent.providers.stub import StubLLMProvider
from kpi_api.settings import ApiSettings

logger = logging.getLogger(__name__)


def get_provider(settings: ApiSettings) -> LLMProvider:
    if settings.llm_provider == "anthropic":
        from kpi_api.agent.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(settings)
    logger.warning("llm_provider=stub: answers are scripted, not model-generated")
    return StubLLMProvider(model=settings.llm_model)
