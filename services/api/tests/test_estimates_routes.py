from httpx import AsyncClient


async def test_history_default(client: AsyncClient) -> None:
    body = (await client.get("/v1/companies/ORBY/kpis/revenue/history")).json()
    assert body["count"] == 14 and body["points"][0]["period"] == "2023Q1"
    assert body["available_range"] == {"from_period": "2023Q1", "to_period": "2026Q2"}


async def test_history_range_limit_and_empty(client: AsyncClient) -> None:
    body = (
        await client.get(
            "/v1/companies/ORBY/kpis/total_revenue/history", params={"from_period": "2025Q1"}
        )
    ).json()
    assert [p["period"] for p in body["points"]] == [
        "2025Q1",
        "2025Q2",
        "2025Q3",
        "2025Q4",
        "2026Q1",
        "2026Q2",
    ]
    body = (
        await client.get("/v1/companies/ORBY/kpis/total_revenue/history", params={"limit": 2})
    ).json()
    assert body["count"] == 2 and body["truncated"]
    body = (
        await client.get(
            "/v1/companies/ORBY/kpis/customer_churn/history",
            params={"from_period": "2019Q1", "to_period": "2019Q4"},
        )
    ).json()
    assert body["points"] == [] and "2023Q1..2026Q2" in body["note"]


async def test_qtd(client: AsyncClient) -> None:
    body = (await client.get("/v1/companies/ORBY/kpis/Total%20Revenue%20(%24MM)/qtd")).json()
    assert body["period"] == "2026Q3" and body["latest"]["as_of"] == "2026-09-15"
    assert [s["as_of"] for s in body["snapshots"]] == [
        "2026-07-31",
        "2026-08-15",
        "2026-08-31",
        "2026-09-15",
    ]
    assert body["prior_quarter"]["period"] == "2026Q2"
    body = (await client.get("/v1/companies/GAPW/kpis/total_revenue/qtd")).json()
    assert body["latest"] is None and "No QTD" in body["note"]


async def test_company_estimates_bundle(client: AsyncClient) -> None:
    body = (await client.get("/v1/companies/ORBY/estimates")).json()
    assert len(body["series"]) == 5
    rev = next(s for s in body["series"] if s["kpi"]["slug"] == "total_revenue")
    assert (
        len(rev["history"]) == 14
        and rev["qtd_period"] == "2026Q3"
        and rev["qtd_latest"]["as_of"] == "2026-09-15"
    )
