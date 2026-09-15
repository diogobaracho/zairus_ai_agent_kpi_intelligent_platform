from httpx import AsyncClient

PROBLEM = "application/problem+json"


async def test_company_not_found_with_suggestions(client: AsyncClient) -> None:
    response = await client.get("/v1/companies/ORBYY")
    assert response.status_code == 404 and response.headers["content-type"].startswith(PROBLEM)
    body = response.json()
    assert body["code"] == "company_not_found" and body["suggestions"][0]["value"] == "ORBY"
    assert body["instance"] == "/v1/companies/ORBYY" and body["trace_id"]
    assert body["type"].endswith("#company_not_found") and "recovery_hint" in body


async def test_kpi_not_found_with_suggestions(client: AsyncClient) -> None:
    body = (await client.get("/v1/companies/ORBY/kpis/Totl%20Revenue/history")).json()
    assert body["status"] == 404 and body["code"] == "kpi_not_found"
    assert body["suggestions"][0]["value"] == "total_revenue"


async def test_kpi_not_published_for_company(client: AsyncClient) -> None:
    body = (await client.get("/v1/companies/GAPW/kpis/arr/qtd")).json()
    assert body["code"] == "kpi_not_found" and body["reason"] == "not_published_for_company"
    assert {s["value"] for s in body["suggestions"]} == {"total_revenue", "paying_customers"}


async def test_sector_not_found(client: AsyncClient) -> None:
    body = (await client.get("/v1/companies", params={"sector": "Sofware"})).json()
    assert body["code"] == "sector_not_found" and body["suggestions"][0]["value"] == "Software"


async def test_invalid_period_and_range(client: AsyncClient) -> None:
    body = (
        await client.get(
            "/v1/companies/ORBY/kpis/revenue/history", params={"from_period": "Q3 2024"}
        )
    ).json()
    assert (
        body["status"] == 400
        and body["code"] == "invalid_period"
        and "YYYYQn" in body["recovery_hint"]
    )
    body = (
        await client.get(
            "/v1/companies/ORBY/kpis/revenue/history",
            params={"from_period": "2025Q1", "to_period": "2024Q1"},
        )
    ).json()
    assert body["code"] == "invalid_period_range"


async def test_invalid_ticker(client: AsyncClient) -> None:
    body = (await client.get("/v1/companies/not%20a%20ticker!")).json()
    assert body["status"] == 400 and body["code"] == "invalid_ticker"


async def test_query_validation_is_problem(client: AsyncClient) -> None:
    response = await client.get("/v1/companies", params={"limit": 999})
    assert response.status_code == 400 and response.headers["content-type"].startswith(PROBLEM)
    body = response.json()
    assert body["code"] == "validation_error" and body["errors"][0]["loc"] == ["query", "limit"]


async def test_unknown_route_is_problem(client: AsyncClient) -> None:
    response = await client.get("/v1/nope")
    assert response.status_code == 404 and response.json()["code"] == "not_found"
    assert response.headers["content-type"].startswith(PROBLEM)


async def test_unhandled_exception_is_masked(client: AsyncClient, app) -> None:  # type: ignore[no-untyped-def]
    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("secret internals")

    from httpx import ASGITransport
    from httpx import AsyncClient as _Client

    async with _Client(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as c:
        response = await c.get("/boom")
    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "internal_error" and "secret" not in body["detail"] and body["trace_id"]
