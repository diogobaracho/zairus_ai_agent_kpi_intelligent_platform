"""The four tools. Each validates transport input, calls one kpi_core service through
`run_tool` (KpiError -> envelope) and returns a Pydantic result model.

Descriptions say *when* to use a tool, because that is what an LLM reads to choose.
"""

from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from kpi_core.context import RequestContext, current_context, system_context
from kpi_core.repositories.protocols import KpiRepository
from kpi_core.services import companies, estimates, kpis
from kpi_mcp.envelope import run_tool
from kpi_mcp.schemas import CompanyKpisResult, KpiHistoryResult, KpiQtdResult, SearchCompaniesResult
from kpi_mcp.settings import McpSettings

READ_ONLY = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False)

TickerArg = Annotated[
    str,
    Field(
        description=(
            "Ticker symbol, e.g. ORBY. Case-insensitive. Unsure? Call search_companies first."
        ),
        min_length=1,
        max_length=10,
    ),
]
KpiArg = Annotated[
    str,
    Field(
        description=(
            "KPI slug as returned by list_company_kpis (e.g. total_revenue, "
            "annual_recurring_revenue, customer_churn), its full name, or an everyday "
            "alias such as 'revenue', 'ARR', 'NRR' or 'churn'."
        ),
        min_length=1,
        max_length=80,
    ),
]
PeriodArg = Annotated[
    str | None,
    Field(
        description="Fiscal quarter label in the form YYYYQn, e.g. 2024Q3.",
        max_length=8,
    ),
]


def _ctx() -> RequestContext:
    return current_context() or system_context("mcp")


def register_tools(mcp: FastMCP, repo: KpiRepository, settings: McpSettings) -> dict[str, set[str]]:
    """Register the tools on `mcp`; return {tool_name: allowed argument names} for the sanitiser."""

    @mcp.tool(name="search_companies", annotations=READ_ONLY, tags={"kpi", "discovery"})
    async def search_companies(
        query: Annotated[
            str | None,
            Field(
                description="Ticker or part of a company name, e.g. 'ORBY' or 'analytics'. "
                "Omit to list every company.",
                max_length=64,
            ),
        ] = None,
        sector: Annotated[
            str | None,
            Field(
                description="Restrict to one sector, e.g. 'Software'. Case-insensitive.",
                max_length=64,
            ),
        ] = None,
        limit: Annotated[int, Field(description="Maximum companies to return.", ge=1, le=100)] = 20,
    ) -> SearchCompaniesResult:
        """Find companies by ticker, partial name or sector, or discover what exists.

        Use this first whenever you are not sure of a ticker. Call it with no arguments to list
        every company and every sector. An empty result is not an error: it includes
        `suggestions` (closest tickers) so you can retry with `suggestions[0].value`.
        """
        ctx = _ctx()
        page = await run_tool(
            companies.search_companies(ctx, repo, query=query, sector=sector, limit=limit, offset=0)
        )
        sectors = None
        if not query and not sector:
            sectors = [s.name for s in await companies.list_sectors(ctx, repo)]
        note = None
        if page.total == 0:
            note = "No company matched. Retry with one of suggestions[].value as the ticker."
        return SearchCompaniesResult(
            trace_id=ctx.trace_id,
            companies=page.items,
            total=page.total,
            sector_filter=sector,
            suggestions=page.suggestions,
            sectors_available=sectors,
            note=note,
        )

    @mcp.tool(name="list_company_kpis", annotations=READ_ONLY, tags={"kpi", "discovery"})
    async def list_company_kpis(ticker: TickerArg) -> CompanyKpisResult:
        """List the KPIs published for one company, with units and the periods covered.

        Use it to learn the exact KPI slugs/names for a ticker before asking for history or
        QTD, or when a KPI call failed with `kpi_not_found`. `has_qtd` tells you whether a
        current quarter-to-date estimate exists; `first_period`/`last_period` bound the history.
        """
        ctx = _ctx()
        company = await run_tool(companies.get_company(ctx, repo, ticker))
        items = await run_tool(kpis.list_company_kpis(ctx, repo, company.ticker))
        return CompanyKpisResult(trace_id=ctx.trace_id, company=company, kpis=items)

    @mcp.tool(name="get_kpi_history", annotations=READ_ONLY, tags={"kpi", "estimates"})
    async def get_kpi_history(
        ticker: TickerArg,
        kpi: KpiArg,
        from_period: PeriodArg = None,
        to_period: PeriodArg = None,
        limit: Annotated[
            int,
            Field(
                description="Maximum quarters to return (oldest first within the range).",
                ge=1,
                le=64,
            ),
        ] = 64,
    ) -> KpiHistoryResult:
        """Historical (completed-quarter) estimates for one KPI of one company, oldest first.

        Use it for trends, year-over-year comparisons and any question about past quarters.
        Do not use it for the current quarter: that is `get_kpi_qtd`. An empty `points` list with
        a `note` means no data in the requested range; `available_range` tells you what exists.
        Errors carry `suggestions` and a `recovery_hint` you should follow once before giving up.
        """
        ctx = _ctx()
        history = await run_tool(
            estimates.get_kpi_history(
                ctx,
                repo,
                ticker=ticker,
                kpi=kpi,
                from_period=from_period,
                to_period=to_period,
                limit=min(limit, settings.mcp_max_history_points),
            )
        )
        return KpiHistoryResult(trace_id=ctx.trace_id, **history.model_dump())

    @mcp.tool(name="get_kpi_qtd", annotations=READ_ONLY, tags={"kpi", "estimates"})
    async def get_kpi_qtd(ticker: TickerArg, kpi: KpiArg) -> KpiQtdResult:
        """Current quarter-to-date (QTD) estimate for one KPI of one company.

        Use it for "this quarter", "so far", "current" or "QTD" questions. `latest` is the most
        recent snapshot (cite its `as_of` date); `snapshots` shows how the estimate moved during
        the quarter; `prior_quarter` is the last completed quarter for comparison. `latest` is
        null with a `note` when no QTD estimate is published.
        """
        ctx = _ctx()
        qtd = await run_tool(estimates.get_kpi_qtd(ctx, repo, ticker=ticker, kpi=kpi))
        return KpiQtdResult(trace_id=ctx.trace_id, **qtd.model_dump())

    return {
        "search_companies": {"query", "sector", "limit"},
        "list_company_kpis": {"ticker"},
        "get_kpi_history": {"ticker", "kpi", "from_period", "to_period", "limit"},
        "get_kpi_qtd": {"ticker", "kpi"},
    }
