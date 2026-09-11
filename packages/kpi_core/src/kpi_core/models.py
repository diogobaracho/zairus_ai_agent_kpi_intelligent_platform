"""Domain models shared by both protocol adapters (REST and MCP).

All models are immutable Pydantic v2 models. Values use public identifiers only (ticker, KPI slug,
period label); no database ids leak into the API surface.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

EstimateType = Literal["historical", "qtd"]
UnitKind = Literal["currency", "count"]
AuditStatus = Literal["ok", "error", "timeout", "rejected"]
ChatRole = Literal["user", "assistant"]


class _Model(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Suggestion(_Model):
    value: str
    label: str
    score: float = Field(ge=0, le=100)


class Company(_Model):
    ticker: str
    name: str
    sector: str


class Sector(_Model):
    name: str
    company_count: int


class KpiDefinition(_Model):
    slug: str
    name: str
    display_name: str
    unit: str
    unit_kind: UnitKind
    scale: int = 1
    description: str = ""


class CompanyKpi(KpiDefinition):
    first_period: str | None = None
    last_period: str | None = None
    historical_count: int = 0
    has_qtd: bool = False
    latest_qtd_as_of: date | None = None


class KpiPoint(_Model):
    period: str
    period_start: date
    period_end: date
    value: float
    unit: str


class QtdSnapshot(_Model):
    period: str
    as_of: date
    value: float
    unit: str


class PeriodRange(_Model):
    from_period: str | None = None
    to_period: str | None = None


class KpiHistory(_Model):
    company: Company
    kpi: KpiDefinition
    points: list[KpiPoint]
    count: int
    requested_range: PeriodRange | None = None
    available_range: PeriodRange | None = None
    truncated: bool = False
    note: str | None = None


class KpiQtd(_Model):
    company: Company
    kpi: KpiDefinition
    period: str | None
    latest: QtdSnapshot | None
    snapshots: list[QtdSnapshot]
    prior_quarter: KpiPoint | None = None
    note: str | None = None


class KpiSeries(_Model):
    kpi: KpiDefinition
    history: list[KpiPoint]
    qtd_period: str | None = None
    qtd_latest: QtdSnapshot | None = None


class CompanyEstimates(_Model):
    company: Company
    series: list[KpiSeries]


class Page[T](BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[T]
    total: int
    limit: int
    offset: int
    suggestions: list[Suggestion] = Field(default_factory=list)


class ToolCallAudit(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int | None = None
    tenant_id: str = "default"
    trace_id: str
    session_id: str | None = None
    conversation_id: str | None = None
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    status: AuditStatus
    duration_ms: int = 0
    error: dict[str, Any] | None = None
    result_summary: str | None = None
    caller: str = "mcp"
    transport: str | None = None
    created_at: datetime | None = None


class ChatMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    conversation_id: str
    seq: int
    role: ChatRole
    content: str
    steps: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, Any] | None = None
    trace_id: str
    stopped_reason: str | None = None
    created_at: datetime | None = None


class Conversation(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    tenant_id: str = "default"
    title: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    messages: list[ChatMessage] = Field(default_factory=list)


class SeedReport(_Model):
    companies: int
    kpis: int
    estimates: int
    inserted: int
    updated: int
