import json

from fastmcp import Client


async def _error(client: Client, tool: str, args: dict) -> dict:  # type: ignore[type-arg]
    result = await client.call_tool(tool, args, raise_on_error=False)
    assert result.is_error, f"expected error from {tool}{args}"
    text = result.content[0].text  # type: ignore[union-attr]
    return json.loads(text)["error"]


async def test_unknown_company_suggests(client: Client) -> None:
    err = await _error(client, "get_kpi_qtd", {"ticker": "ORBYY", "kpi": "revenue"})
    assert err["code"] == "company_not_found" and err["suggestions"][0]["value"] == "ORBY"
    assert (
        err["retryable"] is True and "search_companies" in err["recovery_hint"] and err["trace_id"]
    )


async def test_misspelled_kpi_suggests(client: Client) -> None:
    err = await _error(client, "get_kpi_history", {"ticker": "ORBY", "kpi": "Totl Revenue"})
    assert err["code"] == "kpi_not_found" and err["suggestions"][0]["value"] == "total_revenue"
    assert "list_company_kpis" in err["recovery_hint"]


async def test_kpi_not_published_for_company(client: Client) -> None:
    err = await _error(client, "get_kpi_qtd", {"ticker": "GAPW", "kpi": "arr"})
    assert err["code"] == "kpi_not_found" and err["reason"] == "not_published_for_company"
    assert {s["value"] for s in err["suggestions"]} == {"total_revenue", "paying_customers"}


async def test_invalid_period_and_range(client: Client) -> None:
    err = await _error(
        client, "get_kpi_history", {"ticker": "ORBY", "kpi": "revenue", "from_period": "Q3 2024"}
    )
    assert err["code"] == "invalid_period" and "YYYYQn" in err["recovery_hint"]
    err = await _error(
        client,
        "get_kpi_history",
        {"ticker": "ORBY", "kpi": "revenue", "from_period": "2025Q1", "to_period": "2024Q1"},
    )
    assert err["code"] == "invalid_period_range"


async def test_unknown_sector_suggests(client: Client) -> None:
    err = await _error(client, "search_companies", {"sector": "Sofware"})
    assert err["code"] == "sector_not_found" and err["suggestions"][0]["value"] == "Software"


async def test_invalid_ticker_format(client: Client) -> None:
    err = await _error(client, "list_company_kpis", {"ticker": "$$$"})
    assert err["code"] == "invalid_ticker"


async def test_unexpected_exception_is_masked(repo, audit_repo, settings) -> None:  # type: ignore[no-untyped-def]
    from kpi_mcp.server import create_server

    class Broken:
        def __getattr__(self, name: str):  # type: ignore[no-untyped-def]
            async def boom(*_: object, **__: object) -> None:
                raise RuntimeError("secret internals")

            return boom

    server = create_server(Broken(), audit_repo, settings)  # type: ignore[arg-type]
    async with Client(server) as client:
        result = await client.call_tool(
            "list_company_kpis", {"ticker": "ORBY"}, raise_on_error=False
        )
    assert result.is_error and "secret" not in result.content[0].text  # type: ignore[union-attr]
    assert audit_repo.rows[-1].status == "error"
    assert audit_repo.rows[-1].error is not None
    assert audit_repo.rows[-1].error["code"] == "internal_error"
    assert "secret" not in audit_repo.rows[-1].error["message"]
