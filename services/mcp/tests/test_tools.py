from fastmcp import Client


async def test_search_by_partial_name(client: Client) -> None:
    result = await client.call_tool("search_companies", {"query": "orbit"})
    assert not result.is_error
    data = result.structured_content
    assert data is not None
    assert {c["ticker"] for c in data["companies"]} == {"ORBY", "ORBF"} and data["total"] == 2
    assert data["sectors_available"] is None and data["trace_id"]


async def test_search_discovery_lists_sectors(client: Client) -> None:
    data = (await client.call_tool("search_companies", {})).structured_content
    assert data is not None
    assert data["total"] == 19 and len(data["companies"]) == 19  # default limit is 20
    assert "Software" in data["sectors_available"] and len(data["sectors_available"]) == 15


async def test_search_sector_and_limit(client: Client) -> None:
    data = (
        await client.call_tool("search_companies", {"sector": "software", "limit": 2})
    ).structured_content
    assert data is not None and data["total"] == 3 and len(data["companies"]) == 2


async def test_search_empty_is_success_with_suggestions(client: Client) -> None:
    result = await client.call_tool("search_companies", {"query": "Orbitly Analitycs"})
    assert not result.is_error
    data = result.structured_content
    assert (
        data is not None and data["companies"] == [] and data["suggestions"][0]["value"] == "ORBY"
    )
    assert "suggestions" in (data["note"] or "")


async def test_list_company_kpis_case_insensitive(client: Client) -> None:
    data = (await client.call_tool("list_company_kpis", {"ticker": "orby"})).structured_content
    assert data is not None and data["company"]["ticker"] == "ORBY" and len(data["kpis"]) == 5
    rev = next(k for k in data["kpis"] if k["slug"] == "total_revenue")
    assert rev["has_qtd"] and rev["first_period"] == "2023Q1" and rev["last_period"] == "2026Q2"


async def test_history_alias_and_order(client: Client) -> None:
    data = (
        await client.call_tool("get_kpi_history", {"ticker": "ORBY", "kpi": "revenue"})
    ).structured_content
    assert data is not None and data["count"] == 14
    periods = [p["period"] for p in data["points"]]
    assert periods == sorted(periods) and periods[0] == "2023Q1" and periods[-1] == "2026Q2"
    assert data["kpi"]["slug"] == "total_revenue" and data["points"][0]["unit"] == "$MM"


async def test_history_range_and_limit(client: Client) -> None:
    data = (
        await client.call_tool(
            "get_kpi_history",
            {"ticker": "ORBY", "kpi": "total_revenue", "from_period": "2025Q1", "limit": 2},
        )
    ).structured_content
    assert data is not None and [p["period"] for p in data["points"]] == ["2025Q1", "2025Q2"]
    assert data["truncated"] and data["requested_range"]["from_period"] == "2025Q1"


async def test_history_empty_range_and_gaps(client: Client) -> None:
    data = (
        await client.call_tool(
            "get_kpi_history",
            {
                "ticker": "ORBY",
                "kpi": "customer_churn",
                "from_period": "2019Q1",
                "to_period": "2019Q4",
            },
        )
    ).structured_content
    assert data is not None and data["points"] == [] and "2023Q1..2026Q2" in data["note"]
    sparse = (
        await client.call_tool("get_kpi_history", {"ticker": "SPRW", "kpi": "arr"})
    ).structured_content
    assert sparse is not None and sparse["count"] == 5 and "gaps" in sparse["note"]


async def test_qtd_latest_and_prior(client: Client) -> None:
    data = (
        await client.call_tool("get_kpi_qtd", {"ticker": "ORBY", "kpi": "total_revenue"})
    ).structured_content
    assert (
        data is not None and data["period"] == "2026Q3" and data["latest"]["as_of"] == "2026-09-15"
    )
    assert [s["as_of"] for s in data["snapshots"]] == [
        "2026-07-31",
        "2026-08-15",
        "2026-08-31",
        "2026-09-15",
    ]
    assert data["prior_quarter"]["period"] == "2026Q2"


async def test_qtd_missing_and_qtd_only(client: Client) -> None:
    data = (
        await client.call_tool("get_kpi_qtd", {"ticker": "GAPW", "kpi": "total_revenue"})
    ).structured_content
    assert data is not None and data["latest"] is None and "No QTD" in data["note"]
    data = (
        await client.call_tool("get_kpi_qtd", {"ticker": "FRSH", "kpi": "customers"})
    ).structured_content
    assert data is not None and len(data["snapshots"]) == 4 and data["prior_quarter"] is None
