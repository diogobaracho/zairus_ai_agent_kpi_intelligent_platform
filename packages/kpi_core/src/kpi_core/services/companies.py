"""Company and sector discovery."""

from __future__ import annotations

from kpi_core.context import RequestContext
from kpi_core.errors import CompanyNotFound, SectorNotFound
from kpi_core.fuzzy import Candidate, suggest
from kpi_core.models import Company, Page, Sector, Suggestion
from kpi_core.repositories.protocols import KpiRepository
from kpi_core.validation import clamp_limit, clamp_offset, normalize_query, normalize_ticker

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


async def list_sectors(ctx: RequestContext, repo: KpiRepository) -> list[Sector]:
    return await repo.list_sectors(ctx)


async def suggest_companies(
    ctx: RequestContext, repo: KpiRepository, query: str, *, limit: int = 5, cutoff: float = 55.0
) -> list[Suggestion]:
    companies = await repo.list_companies(ctx)
    candidates = [
        Candidate(value=c.ticker, label=f"{c.name} ({c.ticker}) - {c.sector}", keys=(c.name,))
        for c in companies
    ]
    return suggest(query, candidates, limit=limit, cutoff=cutoff)


async def suggest_sectors(
    ctx: RequestContext, repo: KpiRepository, query: str, *, limit: int = 5, cutoff: float = 55.0
) -> list[Suggestion]:
    sectors = await repo.list_sectors(ctx)
    candidates = [
        Candidate(value=s.name, label=f"{s.name} ({s.company_count} companies)") for s in sectors
    ]
    return suggest(query, candidates, limit=limit, cutoff=cutoff)


async def resolve_sector(ctx: RequestContext, repo: KpiRepository, sector: str) -> str:
    """Case-insensitive exact match on sector name; SectorNotFound with suggestions otherwise."""
    wanted = normalize_query(sector, field="sector")
    for s in await repo.list_sectors(ctx):
        if s.name.lower() == wanted.lower():
            return s.name
    raise SectorNotFound(
        f"No sector named '{sector}'",
        suggestions=await suggest_sectors(ctx, repo, wanted),
        recovery_hint="Use one of suggestions[].value as the sector, or call search_companies "
        "with no arguments to list all sectors.",
    )


async def search_companies(
    ctx: RequestContext,
    repo: KpiRepository,
    *,
    query: str | None = None,
    sector: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> Page[Company]:
    """Ticker or partial-name search, optional sector filter. Empty results carry suggestions."""
    q = normalize_query(query) or None
    limit_v = clamp_limit(limit, default=DEFAULT_LIMIT, maximum=MAX_LIMIT)
    offset_v = clamp_offset(offset)
    sector_v = await resolve_sector(ctx, repo, sector) if sector else None
    items, total = await repo.search_companies(
        ctx, query=q, sector=sector_v, limit=limit_v, offset=offset_v
    )
    suggestions = await suggest_companies(ctx, repo, q) if (q and total == 0) else []
    return Page(items=items, total=total, limit=limit_v, offset=offset_v, suggestions=suggestions)


async def get_company(ctx: RequestContext, repo: KpiRepository, ticker: str) -> Company:
    """Exact ticker lookup; CompanyNotFound with suggestions otherwise."""
    normalized = normalize_ticker(ticker)
    company = await repo.get_company(ctx, normalized)
    if company is None:
        raise CompanyNotFound(
            f"No company with ticker '{normalized}'",
            suggestions=await suggest_companies(ctx, repo, normalized),
            recovery_hint="Retry with one of suggestions[].value as the ticker, or call "
            "search_companies with the company name.",
        )
    return company


async def resolve_company(ctx: RequestContext, repo: KpiRepository, ticker_or_name: str) -> Company:
    """Ticker first; then a unique name match; otherwise CompanyNotFound with suggestions."""
    text = normalize_query(ticker_or_name, field="ticker")
    try:
        return await get_company(ctx, repo, text)
    except CompanyNotFound as not_found:
        items, total = await repo.search_companies(ctx, query=text, sector=None, limit=2, offset=0)
        if total == 1:
            return items[0]
        raise not_found from None
