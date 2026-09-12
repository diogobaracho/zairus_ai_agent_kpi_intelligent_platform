"""ORM rows. Column names mirror docs/data-model.md; constraints live in the migration."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import BigInteger, Date, DateTime, Double, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CompanyRow(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sector: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    estimates: Mapped[list[KpiEstimateRow]] = relationship(back_populates="company")


class KpiRow(Base):
    __tablename__ = "kpis"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    unit_kind: Mapped[str] = mapped_column(Text, nullable=False)
    scale: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


class KpiEstimateRow(Base):
    __tablename__ = "kpi_estimates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    kpi_id: Mapped[int] = mapped_column(ForeignKey("kpis.id", ondelete="CASCADE"), nullable=False)
    period: Mapped[str] = mapped_column(String(6), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    estimate_type: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[float] = mapped_column(Double, nullable=False)
    as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped[CompanyRow] = relationship(back_populates="estimates")
    kpi: Mapped[KpiRow] = relationship()


class ToolCallAuditRow(Base):
    __tablename__ = "tool_call_audit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, default="default")
    trace_id: Mapped[str] = mapped_column(Text, nullable=False)
    session_id: Mapped[str | None] = mapped_column(Text)
    conversation_id: Mapped[str | None] = mapped_column(Text)
    tool_name: Mapped[str] = mapped_column(Text, nullable=False)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    result_summary: Mapped[str | None] = mapped_column(Text)
    caller: Mapped[str] = mapped_column(Text, nullable=False, default="mcp")
    transport: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChatConversationRow(Base):
    __tablename__ = "chat_conversations"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, default="default")
    title: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChatMessageRow(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    usage: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    trace_id: Mapped[str] = mapped_column(Text, nullable=False)
    stopped_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
