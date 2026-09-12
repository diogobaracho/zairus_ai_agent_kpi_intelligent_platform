"""Initial schema: companies, kpis, kpi_estimates, tool_call_audit, chat tables.

Revision ID: 0001
Revises: None
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "companies",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("ticker", sa.String(10), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("sector", sa.Text, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("ticker", name="uq_companies_ticker"),
        sa.CheckConstraint(r"ticker ~ '^[A-Z0-9][A-Z0-9.\-]{0,9}$'", name="ck_companies_ticker"),
    )
    op.create_index("ix_companies_sector", "companies", ["sector"])
    op.execute("CREATE INDEX ix_companies_lower_name ON companies (lower(name))")
    op.execute(
        "CREATE INDEX ix_companies_name_trgm ON companies USING gin (lower(name) gin_trgm_ops)"
    )

    op.create_table(
        "kpis",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("slug", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("display_name", sa.Text, nullable=False),
        sa.Column("unit", sa.Text, nullable=False),
        sa.Column("unit_kind", sa.Text, nullable=False),
        sa.Column("scale", sa.Integer, nullable=False, server_default="1"),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint("slug", name="uq_kpis_slug"),
        sa.UniqueConstraint("name", name="uq_kpis_name"),
        sa.CheckConstraint("unit_kind IN ('currency','count')", name="ck_kpis_unit_kind"),
    )

    op.create_table(
        "kpi_estimates",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "company_id",
            sa.BigInteger,
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "kpi_id", sa.BigInteger, sa.ForeignKey("kpis.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("period", sa.String(6), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("estimate_type", sa.Text, nullable=False),
        sa.Column("value", sa.Double, nullable=False),
        sa.Column("as_of", sa.Date, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(r"period ~ '^\d{4}Q[1-4]$'", name="ck_estimates_period"),
        sa.CheckConstraint("estimate_type IN ('historical','qtd')", name="ck_estimates_type"),
        sa.CheckConstraint(
            "(estimate_type = 'historical' AND as_of IS NULL) "
            "OR (estimate_type = 'qtd' AND as_of IS NOT NULL)",
            name="ck_estimates_as_of",
        ),
        sa.CheckConstraint("period_start < period_end", name="ck_estimates_dates"),
    )
    # NULLS NOT DISTINCT (PG15+) makes the natural key unique even for historical rows (as_of NULL).
    op.execute(
        "ALTER TABLE kpi_estimates ADD CONSTRAINT uq_estimates_key "
        "UNIQUE NULLS NOT DISTINCT (company_id, kpi_id, period, estimate_type, as_of)"
    )
    op.create_index(
        "ix_estimates_lookup",
        "kpi_estimates",
        ["company_id", "kpi_id", "estimate_type", "period_start"],
    )
    op.execute(
        "CREATE INDEX ix_estimates_qtd ON kpi_estimates (company_id, kpi_id, as_of DESC) "
        "WHERE estimate_type = 'qtd'"
    )

    op.create_table(
        "tool_call_audit",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("tenant_id", sa.Text, nullable=False, server_default="default"),
        sa.Column("trace_id", sa.Text, nullable=False),
        sa.Column("session_id", sa.Text),
        sa.Column("conversation_id", sa.Text),
        sa.Column("tool_name", sa.Text, nullable=False),
        sa.Column("arguments", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("duration_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error", postgresql.JSONB),
        sa.Column("result_summary", sa.Text),
        sa.Column("caller", sa.Text, nullable=False, server_default="mcp"),
        sa.Column("transport", sa.Text),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("status IN ('ok','error','timeout','rejected')", name="ck_audit_status"),
    )
    op.create_index("ix_audit_trace", "tool_call_audit", ["trace_id"])
    op.execute("CREATE INDEX ix_audit_created ON tool_call_audit (created_at DESC)")
    op.execute(
        "CREATE INDEX ix_audit_tool_status ON tool_call_audit (tool_name, status, created_at DESC)"
    )

    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("tenant_id", sa.Text, nullable=False, server_default="default"),
        sa.Column("title", sa.Text),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Text,
            sa.ForeignKey("chat_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("role", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("steps", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("usage", postgresql.JSONB),
        sa.Column("trace_id", sa.Text, nullable=False),
        sa.Column("stopped_reason", sa.Text),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("conversation_id", "seq", name="uq_chat_messages_seq"),
        sa.CheckConstraint("role IN ('user','assistant')", name="ck_chat_role"),
    )
    op.create_index("ix_chat_messages_conv", "chat_messages", ["conversation_id", "seq"])
    op.create_index("ix_chat_messages_trace", "chat_messages", ["trace_id"])


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_conversations")
    op.drop_table("tool_call_audit")
    op.drop_table("kpi_estimates")
    op.drop_table("kpis")
    op.drop_table("companies")
