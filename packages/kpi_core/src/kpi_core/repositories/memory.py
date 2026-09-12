"""In-memory implementations: unit tests, the in-process MCP mode, and demos without Postgres.

Semantics are kept identical to the SQL repository and verified by `kpi_core.testing.contract`.
"""

from __future__ import annotations

import itertools
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

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
from kpi_core.seed.csv_loader import SeedRow, read_kpi_csv


class InMemoryKpiRepository:
    def __init__(self) -> None:
        self._companies: dict[str, Company] = {}
        self._kpis: dict[str, KpiDefinition] = {}
        self._historical: dict[tuple[str, str], dict[str, KpiPoint]] = defaultdict(dict)
        self._qtd: dict[tuple[str, str], dict[str, QtdSnapshot]] = defaultdict(dict)

    @classmethod
    def from_csv(cls, *paths: Path | str) -> InMemoryKpiRepository:
        repo = cls()
        for path in paths:
            repo.add_rows(read_kpi_csv(path))
        return repo

    def add_rows(self, rows: list[SeedRow]) -> None:
        for row in rows:
            self._companies.setdefault(
                row.ticker, Company(ticker=row.ticker, name=row.company_name, sector=row.sector)
            )
            self._kpis.setdefault(
                row.kpi_slug,
                KpiDefinition(
                    slug=row.kpi_slug,
                    name=row.kpi,
                    display_name=row.kpi_display_name,
                    unit=row.unit,
                    unit_kind=row.unit_kind,
                    scale=row.scale,
                    description=(
                        f"{row.kpi_display_name} in {row.unit}, estimated quarterly by ZairusData."
                    ),
                ),
            )
            key = (row.ticker, row.kpi_slug)
            if row.estimate_type == "historical":
                self._historical[key][row.period] = KpiPoint(
                    period=row.period,
                    period_start=row.period_start,
                    period_end=row.period_end,
                    value=row.value,
                    unit=row.unit,
                )
            else:
                assert row.as_of is not None
                self._qtd[key][row.as_of.isoformat()] = QtdSnapshot(
                    period=row.period, as_of=row.as_of, value=row.value, unit=row.unit
                )

    # -- companies / sectors ------------------------------------------------------------------
    async def list_sectors(self, ctx: RequestContext) -> list[Sector]:
        counts: dict[str, int] = defaultdict(int)
        for company in self._companies.values():
            counts[company.sector] += 1
        return [Sector(name=n, company_count=c) for n, c in sorted(counts.items())]

    async def search_companies(
        self,
        ctx: RequestContext,
        *,
        query: str | None,
        sector: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Company], int]:
        q = (query or "").strip().lower()
        s = (sector or "").strip().lower()
        matches: list[tuple[int, str, Company]] = []
        for company in self._companies.values():
            if s and company.sector.lower() != s:
                continue
            if q:
                if company.ticker.lower() == q:
                    rank = 0
                elif q in company.ticker.lower() or q in company.name.lower():
                    rank = 1
                else:
                    continue
            else:
                rank = 1
            matches.append((rank, company.name.lower(), company))
        matches.sort(key=lambda m: (m[0], m[1]))
        items = [m[2] for m in matches[offset : offset + limit]]
        return items, len(matches)

    async def get_company(self, ctx: RequestContext, ticker: str) -> Company | None:
        return self._companies.get(ticker.upper())

    async def list_companies(self, ctx: RequestContext) -> list[Company]:
        return sorted(self._companies.values(), key=lambda c: c.ticker)

    # -- kpis ---------------------------------------------------------------------------------
    async def list_kpis(self, ctx: RequestContext) -> list[KpiDefinition]:
        return sorted(self._kpis.values(), key=lambda k: k.slug)

    async def list_company_kpis(self, ctx: RequestContext, ticker: str) -> list[CompanyKpi]:
        ticker = ticker.upper()
        out: list[CompanyKpi] = []
        for slug, kpi in sorted(self._kpis.items()):
            hist = self._historical.get((ticker, slug), {})
            qtd = self._qtd.get((ticker, slug), {})
            if not hist and not qtd:
                continue
            periods = sorted(hist.values(), key=lambda p: p.period_start)
            latest_qtd = max(qtd.values(), key=lambda s: s.as_of) if qtd else None
            out.append(
                CompanyKpi(
                    **kpi.model_dump(),
                    first_period=periods[0].period if periods else None,
                    last_period=periods[-1].period if periods else None,
                    historical_count=len(periods),
                    has_qtd=bool(qtd),
                    latest_qtd_as_of=latest_qtd.as_of if latest_qtd else None,
                )
            )
        return out

    # -- estimates ----------------------------------------------------------------------------
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
        points = sorted(
            self._historical.get((ticker.upper(), kpi_slug), {}).values(),
            key=lambda p: p.period_start,
        )
        if from_period:
            points = [p for p in points if p.period >= from_period]
        if to_period:
            points = [p for p in points if p.period <= to_period]
        return points[:limit], len(points)

    async def get_available_range(
        self, ctx: RequestContext, *, ticker: str, kpi_slug: str
    ) -> PeriodRange | None:
        points = sorted(
            self._historical.get((ticker.upper(), kpi_slug), {}).values(),
            key=lambda p: p.period_start,
        )
        if not points:
            return None
        return PeriodRange(from_period=points[0].period, to_period=points[-1].period)

    async def get_qtd_snapshots(
        self, ctx: RequestContext, *, ticker: str, kpi_slug: str
    ) -> list[QtdSnapshot]:
        return sorted(self._qtd.get((ticker.upper(), kpi_slug), {}).values(), key=lambda s: s.as_of)

    async def get_latest_historical(
        self, ctx: RequestContext, *, ticker: str, kpi_slug: str
    ) -> KpiPoint | None:
        points = sorted(
            self._historical.get((ticker.upper(), kpi_slug), {}).values(),
            key=lambda p: p.period_start,
        )
        return points[-1] if points else None


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self.rows: list[ToolCallAudit] = []
        self._ids = itertools.count(1)

    async def record(self, audit: ToolCallAudit) -> ToolCallAudit:
        stored = audit.model_copy(
            update={"id": next(self._ids), "created_at": audit.created_at or datetime.now(UTC)}
        )
        self.rows.append(stored)
        return stored

    async def query(
        self,
        *,
        tenant_id: str,
        trace_id: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ToolCallAudit]:
        rows = [r for r in self.rows if r.tenant_id == tenant_id]
        if trace_id:
            rows = [r for r in rows if r.trace_id == trace_id]
        if tool_name:
            rows = [r for r in rows if r.tool_name == tool_name]
        if status:
            rows = [r for r in rows if r.status == status]
        rows.sort(
            key=lambda r: (r.created_at or datetime.min.replace(tzinfo=UTC), r.id or 0),
            reverse=True,
        )
        return rows[:limit]


class InMemoryChatRepository:
    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}
        self._messages: dict[str, list[ChatMessage]] = defaultdict(list)

    async def create_conversation(self, ctx: RequestContext, conversation_id: str) -> Conversation:
        now = datetime.now(UTC)
        conv = Conversation(
            id=conversation_id, tenant_id=ctx.tenant_id, created_at=now, updated_at=now
        )
        self._conversations[conversation_id] = conv
        return conv

    async def get_conversation(
        self, ctx: RequestContext, conversation_id: str
    ) -> Conversation | None:
        conv = self._conversations.get(conversation_id)
        if conv is None or conv.tenant_id != ctx.tenant_id:
            return None
        return conv.model_copy(update={"messages": list(self._messages[conversation_id])})

    async def list_conversations(
        self, ctx: RequestContext, *, limit: int = 20
    ) -> list[Conversation]:
        convs = [c for c in self._conversations.values() if c.tenant_id == ctx.tenant_id]
        convs.sort(key=lambda c: c.updated_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return convs[:limit]

    async def append_message(self, ctx: RequestContext, message: ChatMessage) -> ChatMessage:
        conv = self._conversations.get(message.conversation_id)
        if conv is None or conv.tenant_id != ctx.tenant_id:
            conv = await self.create_conversation(ctx, message.conversation_id)
        stored = message.model_copy(update={"created_at": message.created_at or datetime.now(UTC)})
        self._messages[message.conversation_id].append(stored)
        self._conversations[message.conversation_id] = conv.model_copy(
            update={"updated_at": stored.created_at, "title": conv.title or stored.content[:80]}
        )
        return stored
