import pytest

from kpi_core.context import RequestContext
from kpi_core.errors import CompanyNotFound, InvalidTicker, SectorNotFound, ValidationError
from kpi_core.repositories.memory import InMemoryKpiRepository
from kpi_core.services import companies


async def test_list_sectors(ctx: RequestContext, memory_repo: InMemoryKpiRepository) -> None:
    sectors = await companies.list_sectors(ctx, memory_repo)
    assert len(sectors) == 15 and sum(s.company_count for s in sectors) == 19


async def test_search_by_ticker_and_partial_name(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    page = await companies.search_companies(ctx, memory_repo, query="orbitl")
    assert page.items[0].ticker == "ORBY" and page.total == 1 and page.suggestions == []
    page = await companies.search_companies(ctx, memory_repo, query="ORBY")
    assert page.items[0].ticker == "ORBY"


async def test_search_by_sector(ctx: RequestContext, memory_repo: InMemoryKpiRepository) -> None:
    page = await companies.search_companies(ctx, memory_repo, sector="software")
    assert page.total == 3 and all(c.sector == "Software" for c in page.items)


async def test_search_unknown_sector_suggests(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    with pytest.raises(SectorNotFound) as exc:
        await companies.search_companies(ctx, memory_repo, sector="Sofware")
    assert exc.value.suggestions[0].value == "Software"


async def test_search_empty_result_has_suggestions(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    page = await companies.search_companies(ctx, memory_repo, query="Orbitly Analitycs")
    assert page.items == [] and page.total == 0
    assert page.suggestions[0].value == "ORBY"


async def test_search_limit_validation(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    with pytest.raises(ValidationError):
        await companies.search_companies(ctx, memory_repo, limit=999)
    page = await companies.search_companies(ctx, memory_repo, limit=5, offset=15)
    assert len(page.items) == 4 and page.total == 19


async def test_get_company_not_found_suggests(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    with pytest.raises(CompanyNotFound) as exc:
        await companies.get_company(ctx, memory_repo, "ORBYY")
    err = exc.value
    assert err.code == "company_not_found" and err.suggestions[0].value == "ORBY"
    assert "search_companies" in (err.recovery_hint or "")


async def test_get_company_invalid_ticker(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    with pytest.raises(InvalidTicker):
        await companies.get_company(ctx, memory_repo, "not a ticker!")


async def test_resolve_company_by_unique_name(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    company = await companies.resolve_company(ctx, memory_repo, "Orbitly")
    assert company.ticker == "ORBY"
    with pytest.raises(CompanyNotFound):
        await companies.resolve_company(ctx, memory_repo, "Orbit")  # ambiguous: ORBY + ORBF
