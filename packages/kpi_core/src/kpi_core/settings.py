"""Configuration: one validated object with working defaults everywhere.

Rule: every default must produce a working system with no external accounts. Services subclass
`KpiSettings` to add their own keys. The `KPI_` prefix keeps our variables distinguishable from
the ambient environment in a container.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class KpiSettings(BaseSettings):
    """Settings shared by every service."""

    model_config = SettingsConfigDict(
        env_prefix="KPI_", env_file=".env", env_file_encoding="utf-8", extra="ignore", frozen=True
    )

    env: Environment = Environment.LOCAL
    log_level: str = "INFO"
    service_name: str = "kpi"
    database_url: str = "postgresql+asyncpg://kpi:kpi@localhost:5432/kpi"
    correlation_header: str = "X-Correlation-Id"
    default_tenant_id: str = "default"
    fuzzy_cutoff: float = Field(default=55.0, ge=0, le=100)
    fuzzy_limit: int = Field(default=5, ge=1, le=20)
    max_page_size: int = Field(default=100, ge=1, le=1000)
    candidate_cache_ttl_s: float = Field(default=60.0, ge=0)

    @field_validator("log_level")
    @classmethod
    def _upper(cls, value: str) -> str:
        return value.upper()

    @property
    def sync_database_url(self) -> str:
        """The same database over a sync driver, for Alembic."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)

    @property
    def is_production(self) -> bool:
        return self.env == Environment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> KpiSettings:
    """Read once, cache; `get_settings.cache_clear()` in tests."""
    return KpiSettings()
