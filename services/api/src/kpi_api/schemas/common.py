from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from kpi_core.models import Company, CompanyKpi, KpiDefinition, Sector, Suggestion


class _Model(BaseModel):
    model_config = ConfigDict(frozen=True)


class HealthResponse(_Model):
    status: str
    service: str
    version: str


class ReadyResponse(_Model):
    status: str
    checks: dict[str, str]


class SectorList(_Model):
    items: list[Sector]


class CompanyPage(_Model):
    items: list[Company]
    total: int
    limit: int
    offset: int
    suggestions: list[Suggestion]


class CompanyKpiList(_Model):
    company: Company
    items: list[CompanyKpi]


class KpiList(_Model):
    items: list[KpiDefinition]
