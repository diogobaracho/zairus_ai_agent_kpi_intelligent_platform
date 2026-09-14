from httpx import AsyncClient


async def test_sectors(client: AsyncClient) -> None:
    body = (await client.get("/v1/sectors")).json()
    assert len(body["items"]) == 15
    assert next(s for s in body["items"] if s["name"] == "Software")["company_count"] == 3


async def test_search_by_partial_name_and_ticker(client: AsyncClient) -> None:
    body = (await client.get("/v1/companies", params={"q": "orbitl"})).json()
    assert body["items"][0]["ticker"] == "ORBY" and body["total"] == 1
    body = (await client.get("/v1/companies", params={"q": "orby"})).json()
    assert body["items"][0]["ticker"] == "ORBY"


async def test_search_by_sector_and_pagination(client: AsyncClient) -> None:
    body = (await client.get("/v1/companies", params={"sector": "software", "limit": 2})).json()
    assert body["total"] == 3 and len(body["items"]) == 2 and body["limit"] == 2
    body = (await client.get("/v1/companies", params={"limit": 5, "offset": 15})).json()
    assert body["total"] == 19 and len(body["items"]) == 4


async def test_search_empty_has_suggestions(client: AsyncClient) -> None:
    body = (await client.get("/v1/companies", params={"q": "Orbitly Analitycs"})).json()
    assert body["items"] == [] and body["suggestions"][0]["value"] == "ORBY"


async def test_get_company_and_kpis(client: AsyncClient) -> None:
    assert (await client.get("/v1/companies/orby")).json()["name"] == "Orbitly Analytics"
    body = (await client.get("/v1/companies/ORBY/kpis")).json()
    assert body["company"]["ticker"] == "ORBY" and len(body["items"]) == 5
    rev = next(k for k in body["items"] if k["slug"] == "total_revenue")
    assert rev["unit"] == "$MM" and rev["has_qtd"] and rev["latest_qtd_as_of"] == "2026-09-15"


async def test_kpi_catalog(client: AsyncClient) -> None:
    body = (await client.get("/v1/kpis")).json()
    assert {k["slug"] for k in body["items"]} >= {
        "total_revenue",
        "average_order_value",
        "customer_churn",
    }
