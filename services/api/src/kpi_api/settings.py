"""API service settings (extends the shared KpiSettings)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import NoDecode

from kpi_core.settings import KpiSettings


class ApiSettings(KpiSettings):
    service_name: str = "kpi-api"
    api_host: str = "0.0.0.0"  # noqa: S104 - container bind address; override with KPI_API_HOST
    api_port: int = 8080
    # NoDecode: pydantic-settings must not JSON-parse the env value; the validator splits on commas.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )
    rate_limit_rps: float = Field(default=5.0, gt=0)
    rate_limit_burst: int = Field(default=20, ge=1)
    max_body_bytes: int = Field(default=16 * 1024, ge=1024)

    mcp_url: str = "http://localhost:8090/mcp"
    mcp_mode: Literal["http", "inprocess"] = "http"

    llm_provider: Literal["stub", "anthropic"] = "stub"
    llm_model: str = "claude-opus-5"
    llm_effort: Literal["low", "medium", "high"] = "medium"
    llm_max_tokens: int = Field(default=8000, ge=256)
    llm_timeout_s: float = Field(default=60.0, gt=0)
    llm_fallbacks: Literal["off", "default"] = "off"  # server-side refusal fallbacks (beta)

    agent_max_iterations: int = Field(default=8, ge=1, le=32)
    agent_max_parallel_tools: int = Field(default=4, ge=1, le=16)
    agent_tool_timeout_s: float = Field(default=10.0, gt=0)
    agent_max_wall_clock_s: float = Field(default=60.0, gt=0)
    agent_max_message_chars: int = Field(default=4000, ge=1)
    agent_history_window: int = Field(default=20, ge=0)
    agent_max_result_chars: int = Field(default=6000, ge=200)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split(cls, value: object) -> object:
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @model_validator(mode="after")
    def _production_rules(self) -> ApiSettings:
        if self.is_production and "*" in self.cors_origins:
            raise ValueError("KPI_CORS_ORIGINS must not contain '*' in production")
        return self
