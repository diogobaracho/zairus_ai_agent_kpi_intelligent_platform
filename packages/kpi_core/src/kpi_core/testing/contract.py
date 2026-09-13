"""Repository contract: the same assertions run against the in-memory and SQL repositories.

Subclass and provide a `repo` fixture (async) seeded with data/kpi_sample.csv and
data/demo_edge_cases.csv.
"""

from __future__ import annotations

import pytest

from kpi_core.context import RequestContext
from kpi_core.repositories.protocols import KpiRepository

CTX = RequestContext(trace_id="contract-test", caller="test")


class KpiRepositoryContract:
    @pytest.fixture
    async def repo(self) -> KpiRepository:  # pragma: no cover - overridden
        raise NotImplementedError

    async def test_sectors_count_and_software(self, repo: KpiRepository) -> None:
        sectors = await repo.list_sectors(CTX)
        by_name = {s.name: s.company_count for s in sectors}
        assert by_name["Software"] == 3  # 2 sample + SPRW edge case
        assert len(sectors) == 15
        assert sectors == sorted(sectors, key=lambda s: s.name)

    async def test_search_exact_ticker_ranks_first(self, repo: KpiRepository) -> None:
        items, total = await repo.search_companies(
            CTX, query="orby", sector=None, limit=5, offset=0
        )
        assert items[0].ticker == "ORBY"
        assert total >= 1

    async def test_search_partial_name_case_insensitive(self, repo: KpiRepository) -> None:
        items, total = await repo.search_companies(
            CTX, query="ORBIT", sector=None, limit=10, offset=0
        )
        tickers = {c.ticker for c in items}
        assert {"ORBY", "ORBF"} <= tickers
        assert total == len(items)

    async def test_search_sector_filter(self, repo: KpiRepository) -> None:
        items, total = await repo.search_companies(
            CTX, query=None, sector="software", limit=10, offset=0
        )
        assert total == 3
        assert all(c.sector == "Software" for c in items)

    async def test_search_pagination(self, repo: KpiRepository) -> None:
        page1, total = await repo.search_companies(CTX, query=None, sector=None, limit=5, offset=0)
        page2, _ = await repo.search_companies(CTX, query=None, sector=None, limit=5, offset=5)
        assert total == 19
        assert len(page1) == 5 and len(page2) == 5
        assert {c.ticker for c in page1}.isdisjoint({c.ticker for c in page2})

    async def test_search_no_match(self, repo: KpiRepository) -> None:
        items, total = await repo.search_companies(
            CTX, query="zzzz", sector=None, limit=5, offset=0
        )
        assert items == [] and total == 0

    async def test_get_company(self, repo: KpiRepository) -> None:
        company = await repo.get_company(CTX, "ORBY")
        assert company is not None and company.name == "Orbitly Analytics"
        assert await repo.get_company(CTX, "NOPE") is None

    async def test_kpi_catalog(self, repo: KpiRepository) -> None:
        kpis = await repo.list_kpis(CTX)
        assert [k.slug for k in kpis] == sorted(k.slug for k in kpis)
        revenue = next(k for k in kpis if k.slug == "total_revenue")
        assert (
            revenue.unit == "$MM" and revenue.unit_kind == "currency" and revenue.scale == 1_000_000
        )

    async def test_company_kpis_coverage(self, repo: KpiRepository) -> None:
        kpis = await repo.list_company_kpis(CTX, "ORBY")
        assert len(kpis) == 5
        rev = next(k for k in kpis if k.slug == "total_revenue")
        assert (rev.first_period, rev.last_period, rev.historical_count) == ("2023Q1", "2026Q2", 14)
        assert rev.has_qtd and str(rev.latest_qtd_as_of) == "2026-09-15"
        nrr = next(k for k in kpis if k.slug == "net_revenue_retention")
        assert (nrr.unit, nrr.unit_kind) == ("%", "percent")

    async def test_company_kpis_edge_cases(self, repo: KpiRepository) -> None:
        assert {k.slug for k in await repo.list_company_kpis(CTX, "GAPW")} == {
            "total_revenue",
            "paying_customers",
        }
        frsh = await repo.list_company_kpis(CTX, "FRSH")
        assert len(frsh) == 1 and frsh[0].historical_count == 0 and frsh[0].has_qtd

    async def test_history_ascending_and_range(self, repo: KpiRepository) -> None:
        points, total = await repo.get_history(
            CTX, ticker="ORBY", kpi_slug="total_revenue", from_period=None, to_period=None, limit=64
        )
        assert total == 14 and [p.period for p in points][:2] == ["2023Q1", "2023Q2"]
        assert points == sorted(points, key=lambda p: p.period_start)
        sub, sub_total = await repo.get_history(
            CTX,
            ticker="orby",
            kpi_slug="total_revenue",
            from_period="2025Q1",
            to_period="2025Q4",
            limit=64,
        )
        assert sub_total == 4 and [p.period for p in sub] == [
            "2025Q1",
            "2025Q2",
            "2025Q3",
            "2025Q4",
        ]
        limited, limited_total = await repo.get_history(
            CTX, ticker="ORBY", kpi_slug="total_revenue", from_period=None, to_period=None, limit=3
        )
        assert len(limited) == 3 and limited_total == 14

    async def test_history_empty(self, repo: KpiRepository) -> None:
        points, total = await repo.get_history(
            CTX,
            ticker="ORBY",
            kpi_slug="total_revenue",
            from_period="2019Q1",
            to_period="2019Q4",
            limit=64,
        )
        assert points == [] and total == 0
        assert (
            await repo.get_available_range(CTX, ticker="FRSH", kpi_slug="paying_customers") is None
        )

    async def test_available_range(self, repo: KpiRepository) -> None:
        rng = await repo.get_available_range(CTX, ticker="ORBY", kpi_slug="total_revenue")
        assert rng is not None and (rng.from_period, rng.to_period) == ("2023Q1", "2026Q2")

    async def test_qtd_snapshots_ascending(self, repo: KpiRepository) -> None:
        snaps = await repo.get_qtd_snapshots(CTX, ticker="ORBY", kpi_slug="total_revenue")
        assert [str(s.as_of) for s in snaps] == [
            "2026-07-31",
            "2026-08-15",
            "2026-08-31",
            "2026-09-15",
        ]
        assert all(s.period == "2026Q3" for s in snaps)
        assert await repo.get_qtd_snapshots(CTX, ticker="GAPW", kpi_slug="total_revenue") == []

    async def test_latest_historical(self, repo: KpiRepository) -> None:
        latest = await repo.get_latest_historical(CTX, ticker="ORBY", kpi_slug="total_revenue")
        assert latest is not None and latest.period == "2026Q2"
        assert (
            await repo.get_latest_historical(CTX, ticker="FRSH", kpi_slug="paying_customers")
            is None
        )
