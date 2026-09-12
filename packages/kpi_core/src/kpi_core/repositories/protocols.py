"""Storage interfaces. Services depend on these, never on SQLAlchemy directly."""

from __future__ import annotations

from typing import Protocol

from kpi_core.context import RequestContext
from kpi_core.models import (
    ChatMessage,
    Company,
    CompanyKpi,
    Conversation,
    KpiDefinition,
    KpiPoint,
    PeriodRange,
    QtdSnapshot,
    Sector,
    ToolCallAudit,
)


class KpiRepository(Protocol):
    async def list_sectors(self, ctx: RequestContext) -> list[Sector]: ...

    async def search_companies(
        self,
        ctx: RequestContext,
        *,
        query: str | None,
        sector: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Company], int]:
        """Ticker exact match first, then ticker/name substring (case-insensitive).

        Returns (page, total).
        """
        ...

    async def get_company(self, ctx: RequestContext, ticker: str) -> Company | None: ...

    async def list_companies(self, ctx: RequestContext) -> list[Company]: ...

    async def list_kpis(self, ctx: RequestContext) -> list[KpiDefinition]: ...

    async def list_company_kpis(self, ctx: RequestContext, ticker: str) -> list[CompanyKpi]: ...

    async def get_history(
        self,
        ctx: RequestContext,
        *,
        ticker: str,
        kpi_slug: str,
        from_period: str | None,
        to_period: str | None,
        limit: int,
    ) -> tuple[list[KpiPoint], int]:
        """Historical points ascending by period_start, capped at `limit`.

        Returns (points, total_in_range).
        """
        ...

    async def get_available_range(
        self, ctx: RequestContext, *, ticker: str, kpi_slug: str
    ) -> PeriodRange | None: ...

    async def get_qtd_snapshots(
        self, ctx: RequestContext, *, ticker: str, kpi_slug: str
    ) -> list[QtdSnapshot]:
        """All QTD snapshots ascending by as_of."""
        ...

    async def get_latest_historical(
        self, ctx: RequestContext, *, ticker: str, kpi_slug: str
    ) -> KpiPoint | None: ...


class AuditRepository(Protocol):
    async def record(self, audit: ToolCallAudit) -> ToolCallAudit: ...

    async def query(
        self,
        *,
        tenant_id: str,
        trace_id: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ToolCallAudit]: ...


class ChatRepository(Protocol):
    async def create_conversation(
        self, ctx: RequestContext, conversation_id: str
    ) -> Conversation: ...

    async def get_conversation(
        self, ctx: RequestContext, conversation_id: str
    ) -> Conversation | None: ...

    async def list_conversations(
        self, ctx: RequestContext, *, limit: int = 20
    ) -> list[Conversation]: ...

    async def append_message(self, ctx: RequestContext, message: ChatMessage) -> ChatMessage: ...
