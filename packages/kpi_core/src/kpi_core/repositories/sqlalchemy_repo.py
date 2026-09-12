"""Postgres implementations over SQLAlchemy 2.x async. ORM `select()` only; no raw SQL."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kpi_core.context import RequestContext
from kpi_core.db.orm import (
    ChatConversationRow,
    ChatMessageRow,
    CompanyRow,
    KpiEstimateRow,
    KpiRow,
    ToolCallAuditRow,
)
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

SessionMaker = async_sessionmaker[AsyncSession]


def _company(row: CompanyRow) -> Company:
    return Company(ticker=row.ticker, name=row.name, sector=row.sector)


def _kpi(row: KpiRow) -> KpiDefinition:
    return KpiDefinition(
        slug=row.slug,
        name=row.name,
        display_name=row.display_name,
        unit=row.unit,
        unit_kind="currency" if row.unit_kind == "currency" else "count",
        scale=row.scale,
        description=row.description,
    )


class SqlAlchemyKpiRepository:
    def __init__(self, sessions: SessionMaker) -> None:
        self._sessions = sessions

    async def list_sectors(self, ctx: RequestContext) -> list[Sector]:
        stmt = (
            select(CompanyRow.sector, func.count(CompanyRow.id))
            .group_by(CompanyRow.sector)
            .order_by(CompanyRow.sector)
        )
        async with self._sessions() as session:
            rows = (await session.execute(stmt)).all()
        return [Sector(name=name, company_count=int(count)) for name, count in rows]

    async def search_companies(
        self,
        ctx: RequestContext,
        *,
        query: str | None,
        sector: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Company], int]:
        conditions = []
        if sector:
            conditions.append(func.lower(CompanyRow.sector) == sector.lower())
        rank = case((func.lower(CompanyRow.ticker) == (query or "").lower(), 0), else_=1)
        if query:
            pattern = f"%{query.lower()}%"
            conditions.append(
                or_(
                    func.lower(CompanyRow.ticker) == query.lower(),
                    func.lower(CompanyRow.ticker).like(pattern),
                    func.lower(CompanyRow.name).like(pattern),
                )
            )
        base = select(CompanyRow).where(*conditions)
        count_stmt = select(func.count()).select_from(base.subquery())
        page_stmt = base.order_by(rank, func.lower(CompanyRow.name)).limit(limit).offset(offset)
        async with self._sessions() as session:
            total = int((await session.execute(count_stmt)).scalar_one())
            rows = (await session.execute(page_stmt)).scalars().all()
        return [_company(r) for r in rows], total

    async def get_company(self, ctx: RequestContext, ticker: str) -> Company | None:
        async with self._sessions() as session:
            row = (
                await session.execute(select(CompanyRow).where(CompanyRow.ticker == ticker.upper()))
            ).scalar_one_or_none()
        return _company(row) if row else None

    async def list_companies(self, ctx: RequestContext) -> list[Company]:
        async with self._sessions() as session:
            rows = (
                (await session.execute(select(CompanyRow).order_by(CompanyRow.ticker)))
                .scalars()
                .all()
            )
        return [_company(r) for r in rows]

    async def list_kpis(self, ctx: RequestContext) -> list[KpiDefinition]:
        async with self._sessions() as session:
            rows = (await session.execute(select(KpiRow).order_by(KpiRow.slug))).scalars().all()
        return [_kpi(r) for r in rows]

    async def list_company_kpis(self, ctx: RequestContext, ticker: str) -> list[CompanyKpi]:
        hist = KpiEstimateRow.estimate_type == "historical"
        qtd = KpiEstimateRow.estimate_type == "qtd"
        stmt = (
            select(
                KpiRow,
                func.min(case((hist, KpiEstimateRow.period_start))),
                func.max(case((hist, KpiEstimateRow.period_start))),
                func.min(case((hist, KpiEstimateRow.period))),
                func.max(case((hist, KpiEstimateRow.period))),
                func.count(case((hist, KpiEstimateRow.id))),
                func.max(case((qtd, KpiEstimateRow.as_of))),
            )
            .join(KpiEstimateRow, KpiEstimateRow.kpi_id == KpiRow.id)
            .join(CompanyRow, CompanyRow.id == KpiEstimateRow.company_id)
            .where(CompanyRow.ticker == ticker.upper())
            .group_by(KpiRow.id)
            .order_by(KpiRow.slug)
        )
        async with self._sessions() as session:
            rows = (await session.execute(stmt)).all()
        out: list[CompanyKpi] = []
        for (
            kpi_row,
            _first_start,
            _last_start,
            first_period,
            last_period,
            count,
            latest_qtd,
        ) in rows:
            out.append(
                CompanyKpi(
                    **_kpi(kpi_row).model_dump(),
                    first_period=first_period,
                    last_period=last_period,
                    historical_count=int(count),
                    has_qtd=latest_qtd is not None,
                    latest_qtd_as_of=latest_qtd,
                )
            )
        return out

    def _estimates_stmt(self, ticker: str, kpi_slug: str, estimate_type: str):  # type: ignore[no-untyped-def]
        return (
            select(KpiEstimateRow, KpiRow.unit)
            .join(CompanyRow, CompanyRow.id == KpiEstimateRow.company_id)
            .join(KpiRow, KpiRow.id == KpiEstimateRow.kpi_id)
            .where(
                CompanyRow.ticker == ticker.upper(),
                KpiRow.slug == kpi_slug,
                KpiEstimateRow.estimate_type == estimate_type,
            )
        )

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
        base = self._estimates_stmt(ticker, kpi_slug, "historical")
        if from_period:
            base = base.where(KpiEstimateRow.period >= from_period)
        if to_period:
            base = base.where(KpiEstimateRow.period <= to_period)
        count_stmt = select(func.count()).select_from(base.subquery())
        page_stmt = base.order_by(KpiEstimateRow.period_start).limit(limit)
        async with self._sessions() as session:
            total = int((await session.execute(count_stmt)).scalar_one())
            rows = (await session.execute(page_stmt)).all()
        points = [
            KpiPoint(
                period=e.period,
                period_start=e.period_start,
                period_end=e.period_end,
                value=e.value,
                unit=unit,
            )
            for e, unit in rows
        ]
        return points, total

    async def get_available_range(
        self, ctx: RequestContext, *, ticker: str, kpi_slug: str
    ) -> PeriodRange | None:
        base = self._estimates_stmt(ticker, kpi_slug, "historical")
        first = base.order_by(KpiEstimateRow.period_start.asc()).limit(1)
        last = base.order_by(KpiEstimateRow.period_start.desc()).limit(1)
        async with self._sessions() as session:
            first_row = (await session.execute(first)).first()
            last_row = (await session.execute(last)).first()
        if first_row is None or last_row is None:
            return None
        return PeriodRange(from_period=first_row[0].period, to_period=last_row[0].period)

    async def get_qtd_snapshots(
        self, ctx: RequestContext, *, ticker: str, kpi_slug: str
    ) -> list[QtdSnapshot]:
        stmt = self._estimates_stmt(ticker, kpi_slug, "qtd").order_by(KpiEstimateRow.as_of.asc())
        async with self._sessions() as session:
            rows = (await session.execute(stmt)).all()
        return [
            QtdSnapshot(period=e.period, as_of=e.as_of, value=e.value, unit=unit)
            for e, unit in rows
            if e.as_of is not None
        ]

    async def get_latest_historical(
        self, ctx: RequestContext, *, ticker: str, kpi_slug: str
    ) -> KpiPoint | None:
        stmt = (
            self._estimates_stmt(ticker, kpi_slug, "historical")
            .order_by(KpiEstimateRow.period_start.desc())
            .limit(1)
        )
        async with self._sessions() as session:
            row = (await session.execute(stmt)).first()
        if row is None:
            return None
        e, unit = row
        return KpiPoint(
            period=e.period,
            period_start=e.period_start,
            period_end=e.period_end,
            value=e.value,
            unit=unit,
        )


def _audit(row: ToolCallAuditRow) -> ToolCallAudit:
    return ToolCallAudit(
        id=row.id,
        tenant_id=row.tenant_id,
        trace_id=row.trace_id,
        session_id=row.session_id,
        conversation_id=row.conversation_id,
        tool_name=row.tool_name,
        arguments=row.arguments,
        status=row.status,
        duration_ms=row.duration_ms,
        error=row.error,
        result_summary=row.result_summary,
        caller=row.caller,
        transport=row.transport,
        created_at=row.created_at,
    )


class SqlAlchemyAuditRepository:
    def __init__(self, sessions: SessionMaker) -> None:
        self._sessions = sessions

    async def record(self, audit: ToolCallAudit) -> ToolCallAudit:
        row = ToolCallAuditRow(**audit.model_dump(exclude={"id", "created_at"}))
        async with self._sessions() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _audit(row)

    async def query(
        self,
        *,
        tenant_id: str,
        trace_id: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ToolCallAudit]:
        stmt = select(ToolCallAuditRow).where(ToolCallAuditRow.tenant_id == tenant_id)
        if trace_id:
            stmt = stmt.where(ToolCallAuditRow.trace_id == trace_id)
        if tool_name:
            stmt = stmt.where(ToolCallAuditRow.tool_name == tool_name)
        if status:
            stmt = stmt.where(ToolCallAuditRow.status == status)
        stmt = stmt.order_by(ToolCallAuditRow.created_at.desc(), ToolCallAuditRow.id.desc()).limit(
            limit
        )
        async with self._sessions() as session:
            rows = (await session.execute(stmt)).scalars().all()
        return [_audit(r) for r in rows]


def _message(row: ChatMessageRow) -> ChatMessage:
    return ChatMessage(
        id=row.id,
        conversation_id=row.conversation_id,
        seq=row.seq,
        role=row.role,
        content=row.content,
        steps=row.steps,
        usage=row.usage,
        trace_id=row.trace_id,
        stopped_reason=row.stopped_reason,
        created_at=row.created_at,
    )


def _conversation(row: ChatConversationRow, messages: list[ChatMessage]) -> Conversation:
    return Conversation(
        id=row.id,
        tenant_id=row.tenant_id,
        title=row.title,
        created_at=row.created_at,
        updated_at=row.updated_at,
        messages=messages,
    )


class SqlAlchemyChatRepository:
    def __init__(self, sessions: SessionMaker) -> None:
        self._sessions = sessions

    async def create_conversation(self, ctx: RequestContext, conversation_id: str) -> Conversation:
        row = ChatConversationRow(id=conversation_id, tenant_id=ctx.tenant_id)
        async with self._sessions() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _conversation(row, [])

    async def get_conversation(
        self, ctx: RequestContext, conversation_id: str
    ) -> Conversation | None:
        async with self._sessions() as session:
            row = (
                await session.execute(
                    select(ChatConversationRow).where(
                        ChatConversationRow.id == conversation_id,
                        ChatConversationRow.tenant_id == ctx.tenant_id,
                    )
                )
            ).scalar_one_or_none()
            if row is None:
                return None
            messages = (
                (
                    await session.execute(
                        select(ChatMessageRow)
                        .where(ChatMessageRow.conversation_id == conversation_id)
                        .order_by(ChatMessageRow.seq)
                    )
                )
                .scalars()
                .all()
            )
        return _conversation(row, [_message(m) for m in messages])

    async def list_conversations(
        self, ctx: RequestContext, *, limit: int = 20
    ) -> list[Conversation]:
        stmt = (
            select(ChatConversationRow)
            .where(ChatConversationRow.tenant_id == ctx.tenant_id)
            .order_by(ChatConversationRow.updated_at.desc())
            .limit(limit)
        )
        async with self._sessions() as session:
            rows = (await session.execute(stmt)).scalars().all()
        return [_conversation(r, []) for r in rows]

    async def append_message(self, ctx: RequestContext, message: ChatMessage) -> ChatMessage:
        async with self._sessions() as session:
            conv = (
                await session.execute(
                    select(ChatConversationRow).where(
                        ChatConversationRow.id == message.conversation_id
                    )
                )
            ).scalar_one_or_none()
            if conv is None:
                conv = ChatConversationRow(id=message.conversation_id, tenant_id=ctx.tenant_id)
                session.add(conv)
            row = ChatMessageRow(**message.model_dump(exclude={"created_at"}))
            session.add(row)
            conv.updated_at = datetime.now(UTC)
            if not conv.title:
                conv.title = message.content[:80]
            await session.commit()
            await session.refresh(row)
        return _message(row)
