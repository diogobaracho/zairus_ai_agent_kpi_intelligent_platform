from kpi_core.fuzzy import Candidate, kpi_display_name, kpi_slug, resolve_alias, suggest


def test_kpi_slug_and_display() -> None:
    assert kpi_slug("Total Revenue ($MM)") == "total_revenue"
    assert kpi_slug("Average Order Value ($)") == "average_order_value"
    assert kpi_slug("Net Revenue Retention (%)") == "net_revenue_retention"
    assert kpi_slug("Avg. Revenue per User ($)") == "avg_revenue_per_user"
    assert kpi_slug("Paying Customers") == "paying_customers"
    assert kpi_slug("Orders Fulfilled") == "orders_fulfilled"
    assert kpi_display_name("Total Revenue ($MM)") == "Total Revenue"


def test_aliases() -> None:
    assert resolve_alias("Revenue") == "total_revenue"
    assert resolve_alias("NRR") == "net_revenue_retention"
    assert resolve_alias("churn rate") == "customer_churn"
    assert resolve_alias("  GMV ") == "gross_merchandise_volume"
    assert resolve_alias("nonsense") is None


KPIS = [
    Candidate("total_revenue", "Total Revenue ($MM)", ("Total Revenue",)),
    Candidate("average_order_value", "Average Order Value ($)", ("AOV",)),
    Candidate("orders_fulfilled", "Orders Fulfilled"),
    Candidate("paying_customers", "Paying Customers"),
    Candidate("net_revenue_retention", "Net Revenue Retention (%)"),
]


def test_suggest_typo() -> None:
    out = suggest("Totl Revenu", KPIS)
    assert out[0].value == "total_revenue" and out[0].score >= 80


def test_suggest_orders_and_limits() -> None:
    out = suggest("revenue", KPIS, limit=2)
    assert len(out) == 2 and {s.value for s in out} <= {
        "total_revenue",
        "net_revenue_retention",
    }
    assert out[0].score >= out[1].score


def test_suggest_cutoff_and_empty() -> None:
    assert suggest("zzzzzz", KPIS, cutoff=90) == []
    assert suggest("", KPIS) == []
    assert suggest("x", []) == []


def test_suggest_companies_by_name() -> None:
    cands = [
        Candidate("ORBY", "Orbitly Analytics (ORBY)", ("Orbitly Analytics",)),
        Candidate("ORBF", "Orbital Freight (ORBF)", ("Orbital Freight",)),
    ]
    assert suggest("Orbitly Analitics", cands)[0].value == "ORBY"
    assert suggest("ORBYY", cands)[0].value == "ORBY"
