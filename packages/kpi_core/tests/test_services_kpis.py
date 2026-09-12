import pytest

from kpi_core.context import RequestContext
from kpi_core.errors import CompanyNotFound, KpiNotFound
from kpi_core.repositories.memory import InMemoryKpiRepository
from kpi_core.services import kpis


async def test_catalog_and_company_kpis(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    catalog = await kpis.list_kpi_catalog(ctx, memory_repo)
    assert {k.slug for k in catalog} == {
        "annual_recurring_revenue",
        "average_order_value",
        "average_revenue_per_user",
        "customer_churn",
        "devices_shipped",
        "gross_margin",
        "gross_merchandise_volume",
        "monthly_active_users",
        "net_revenue_retention",
        "orders_fulfilled",
        "paying_customers",
        "total_payment_volume",
        "total_revenue",
    }
    mine = await kpis.list_company_kpis(ctx, memory_repo, "orby")
    assert len(mine) == 5 and all(k.has_qtd for k in mine)
    with pytest.raises(CompanyNotFound):
        await kpis.list_company_kpis(ctx, memory_repo, "ORBYY")


@pytest.mark.parametrize(
    "query,slug",
    [
        ("total_revenue", "total_revenue"),
        ("Total Revenue ($MM)", "total_revenue"),
        ("total revenue", "total_revenue"),
        ("Revenue", "total_revenue"),
        ("AOV", "average_order_value"),
        ("NRR", "net_revenue_retention"),
        ("churn", "customer_churn"),
        ("Orders Fulfilled", "orders_fulfilled"),
    ],
)
async def test_resolve_kpi_paths(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository, query: str, slug: str
) -> None:
    assert (await kpis.resolve_kpi(ctx, memory_repo, query)).slug == slug


async def test_resolve_kpi_typo_suggests(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    with pytest.raises(KpiNotFound) as exc:
        await kpis.resolve_kpi(ctx, memory_repo, "Totl Revenue")
    assert exc.value.suggestions[0].value == "total_revenue"
    assert "list_company_kpis" in (exc.value.recovery_hint or "")


async def test_resolve_kpi_not_published_for_company(
    ctx: RequestContext, memory_repo: InMemoryKpiRepository
) -> None:
    with pytest.raises(KpiNotFound) as exc:
        await kpis.resolve_kpi(ctx, memory_repo, "arr", ticker="GAPW")
    err = exc.value
    assert err.extra["reason"] == "not_published_for_company"
    assert {s.value for s in err.suggestions} == {"total_revenue", "paying_customers"}
