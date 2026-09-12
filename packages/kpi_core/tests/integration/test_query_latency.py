"""Acceptance: local dataset queries under 500 ms (p95 over a mixed workload)."""

import statistics
import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kpi_core.context import RequestContext
from kpi_core.repositories.sqlalchemy_repo import SqlAlchemyKpiRepository
from kpi_core.services import companies, estimates, kpis

pytestmark = pytest.mark.integration

TICKERS = ["ORBY", "MMHM", "KSTL", "ORBF", "PNCR", "NRDV", "CPFD", "LUMO", "VOLT", "HRBL"]


async def test_p95_under_500ms(sql_sessions: async_sessionmaker[AsyncSession]) -> None:
    repo = SqlAlchemyKpiRepository(sql_sessions)
    ctx = RequestContext(trace_id="latency", caller="test")
    durations: list[float] = []
    for i in range(60):
        ticker = TICKERS[i % len(TICKERS)]
        for coro in (
            companies.search_companies(ctx, repo, query=ticker[:2]),
            kpis.list_company_kpis(ctx, repo, ticker),
            estimates.get_kpi_history(ctx, repo, ticker=ticker, kpi="revenue"),
            estimates.get_kpi_qtd(ctx, repo, ticker=ticker, kpi="revenue"),
        ):
            started = time.perf_counter()
            await coro
            durations.append((time.perf_counter() - started) * 1000)
    p95 = statistics.quantiles(durations, n=20)[18]
    print(
        f"\nquery latency: n={len(durations)} "
        f"p50={statistics.median(durations):.1f}ms p95={p95:.1f}ms"
    )
    assert p95 < 500
