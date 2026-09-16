"""Tool result models. Returning Pydantic models gives every tool an output schema the client
shows to the model, and the same JSON is rendered as text content."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from kpi_core.models import (
    Company,
    CompanyKpi,
    KpiDefinition,
    KpiPoint,
    PeriodRange,
    QtdSnapshot,
    Suggestion,
)


class _Result(BaseModel):
    model_config = ConfigDict(frozen=True)

    trace_id: str = Field(description="Correlation id; quote it when reporting a problem.")


class SearchCompaniesResult(_Result):
    companies: list[Company]
    total: int
    sector_filter: str | None = None
    suggestions: list[Suggestion] = Field(
        default_factory=list,
        description="Close matches when nothing matched; retry with suggestions[].value.",
    )
    sectors_available: list[str] | None = Field(
        default=None, description="All sector names; present only when called without arguments."
    )
    note: str | None = None


class CompanyKpisResult(_Result):
    company: Company
    kpis: list[CompanyKpi]


class KpiHistoryResult(_Result):
    company: Company
    kpi: KpiDefinition
    points: list[KpiPoint] = Field(description="Completed quarters, ascending by period.")
    count: int
    requested_range: PeriodRange | None = None
    available_range: PeriodRange | None = None
    truncated: bool = False
    note: str | None = None


class KpiQtdResult(_Result):
    company: Company
    kpi: KpiDefinition
    period: str | None = Field(
        description="Fiscal quarter of the current QTD estimate, e.g. 2026Q1."
    )
    latest: QtdSnapshot | None = Field(description="Most recent snapshot (highest as_of).")
    snapshots: list[QtdSnapshot] = Field(
        description="All snapshots for the quarter, ascending by as_of."
    )
    prior_quarter: KpiPoint | None = Field(
        description="Last completed quarter's historical estimate."
    )
    note: str | None = None
