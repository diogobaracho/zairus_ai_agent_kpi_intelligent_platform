#!/usr/bin/env python3
"""P95 latency check for the acceptance targets: API < 1 s, MCP tool < 2 s.

Runs against a live stack: `uv run python scripts/perf_smoke.py [--api URL] [--mcp URL] [-n 100]`.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

API_PATHS = [
    "/v1/sectors",
    "/v1/companies?q=orbitly",
    "/v1/companies?sector=Software",
    "/v1/companies/ORBY/kpis",
    "/v1/companies/ORBY/kpis/total_revenue/history",
    "/v1/companies/ORBY/kpis/total_revenue/qtd",
    "/v1/companies/MMHM/estimates",
]
TOOL_CALLS = [
    ("search_companies", {"query": "orbit"}),
    ("list_company_kpis", {"ticker": "ORBY"}),
    ("get_kpi_history", {"ticker": "ORBY", "kpi": "revenue"}),
    ("get_kpi_qtd", {"ticker": "ORBY", "kpi": "total_revenue"}),
]


def p95(values: list[float]) -> float:
    return statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values)


async def measure_api(base: str, n: int) -> list[float]:
    durations: list[float] = []
    async with httpx.AsyncClient(base_url=base, timeout=10) as client:
        for i in range(n):
            path = API_PATHS[i % len(API_PATHS)]
            started = time.perf_counter()
            response = await client.get(path)
            durations.append((time.perf_counter() - started) * 1000)
            response.raise_for_status()
            await asyncio.sleep(0.25)  # stay under the per-IP rate limit
    return durations


async def measure_mcp(url: str, n: int) -> list[float]:
    durations: list[float] = []
    async with Client(StreamableHttpTransport(url=url)) as client:
        for i in range(n):
            name, args = TOOL_CALLS[i % len(TOOL_CALLS)]
            started = time.perf_counter()
            await client.call_tool(name, args)
            durations.append((time.perf_counter() - started) * 1000)
            await asyncio.sleep(0.05)
    return durations


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8080")
    parser.add_argument("--mcp", default="http://localhost:8090/mcp")
    parser.add_argument("-n", type=int, default=60)
    args = parser.parse_args()
    api = await measure_api(args.api, args.n)
    mcp = await measure_mcp(args.mcp, args.n)
    api_p95, mcp_p95 = p95(api), p95(mcp)
    api_p50, mcp_p50 = statistics.median(api), statistics.median(mcp)
    print(f"api:  n={len(api)} p50={api_p50:.1f}ms p95={api_p95:.1f}ms (target < 1000)")
    print(f"mcp:  n={len(mcp)} p50={mcp_p50:.1f}ms p95={mcp_p95:.1f}ms (target < 2000)")
    ok = api_p95 < 1000 and mcp_p95 < 2000
    print("PERF OK" if ok else "PERF FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
