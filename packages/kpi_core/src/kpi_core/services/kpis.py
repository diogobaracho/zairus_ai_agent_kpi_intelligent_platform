"""KPI catalogue and resolution (slug, canonical name, alias, fuzzy)."""

from __future__ import annotations

from kpi_core.context import RequestContext
from kpi_core.errors import KpiNotFound
from kpi_core.fuzzy import Candidate, normalize_key, resolve_alias, suggest
from kpi_core.models import CompanyKpi, KpiDefinition, Suggestion
from kpi_core.repositories.protocols import KpiRepository
from kpi_core.services.companies import get_company
from kpi_core.validation import normalize_kpi_query


async def list_kpi_catalog(ctx: RequestContext, repo: KpiRepository) -> list[KpiDefinition]:
    return await repo.list_kpis(ctx)


async def list_company_kpis(
    ctx: RequestContext, repo: KpiRepository, ticker: str
) -> list[CompanyKpi]:
    company = await get_company(ctx, repo, ticker)
    return await repo.list_company_kpis(ctx, company.ticker)


def _candidates(kpis: list[KpiDefinition]) -> list[Candidate]:
    return [
        Candidate(value=k.slug, label=f"{k.name}", keys=(k.display_name, k.slug.replace("_", " ")))
        for k in kpis
    ]


async def suggest_kpis(
    ctx: RequestContext,
    repo: KpiRepository,
    query: str,
    *,
    kpis: list[KpiDefinition] | None = None,
    limit: int = 5,
    cutoff: float = 55.0,
) -> list[Suggestion]:
    pool = kpis if kpis is not None else await repo.list_kpis(ctx)
    return suggest(query, _candidates(pool), limit=limit, cutoff=cutoff)


def _match(kpis: list[KpiDefinition], query: str) -> KpiDefinition | None:
    key = normalize_key(query)
    for k in kpis:
        if key in (normalize_key(k.slug), normalize_key(k.name), normalize_key(k.display_name)):
            return k
    alias = resolve_alias(query)
    if alias:
        for k in kpis:
            if k.slug == alias:
                return k
    return None


async def resolve_kpi(
    ctx: RequestContext, repo: KpiRepository, kpi_query: str, *, ticker: str | None = None
) -> KpiDefinition:
    """Resolve a KPI by slug, name, display name or alias.

    With `ticker`, the KPI must also be published for that company; otherwise `KpiNotFound`
    lists the company's KPIs as suggestions (the "exists globally but not here" case).
    """
    text = normalize_kpi_query(kpi_query)
    catalog = await repo.list_kpis(ctx)
    found = _match(catalog, text)
    if found is None:
        raise KpiNotFound(
            f"No KPI matching '{text}'",
            suggestions=await suggest_kpis(ctx, repo, text, kpis=catalog),
            recovery_hint="Retry with kpi set to suggestions[0].value, or call list_company_kpis "
            "to see the exact KPI names.",
        )
    if ticker is not None:
        company_kpis = await repo.list_company_kpis(ctx, ticker)
        if all(k.slug != found.slug for k in company_kpis):
            raise KpiNotFound(
                f"KPI '{found.name}' is not published for {ticker}",
                suggestions=[
                    Suggestion(value=k.slug, label=k.name, score=100.0) for k in company_kpis
                ],
                recovery_hint=f"{ticker} publishes only the KPIs in suggestions[]; "
                "pick one of them "
                "or call list_company_kpis.",
                reason="not_published_for_company",
            )
    return found
