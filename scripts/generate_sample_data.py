#!/usr/bin/env python3
"""Generate the synthetic KPI dataset in data/.

Every company, ticker and number here is fictional. The generator is deterministic (fixed seed),
so re-running it produces byte-identical CSVs and the tests can rely on exact counts.

    python3 scripts/generate_sample_data.py          # rewrites both CSVs in data/
    python3 scripts/generate_sample_data.py --check  # exits 1 if the committed files are stale

Shape of the data:
- historical quarters 2023Q1..2026Q2 (14 per KPI), one row per quarter, no `as_of`;
- quarter-to-date (QTD) estimates for 2026Q3, four snapshots with an `as_of` date each;
- "flow" KPIs (revenue, volume, orders) accumulate through the quarter, "stock" KPIs (ARR,
  customers, ratios) are full-quarter estimates that converge as the quarter progresses.
"""

from __future__ import annotations

import argparse
import csv
import io
import random
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HEADER = [
    "company_name", "ticker", "sector", "kpi", "period_start", "period_end",
    "period", "estimate_type", "value", "unit", "as_of",
]  # fmt: skip

HISTORY = [(y, q) for y in range(2023, 2027) for q in range(1, 5)][:14]  # 2023Q1..2026Q2
QTD_PERIOD = (2026, 3)
QTD_AS_OF = [date(2026, 7, 31), date(2026, 8, 15), date(2026, 8, 31), date(2026, 9, 15)]
QTD_PROGRESS = [0.33, 0.50, 0.67, 0.83]


@dataclass(frozen=True)
class Kpi:
    name: str
    unit: str
    flow: bool  # accumulates through the quarter (QTD is partial) vs. point-in-time estimate
    decimals: int = 2
    bounds: tuple[float, float] | None = None  # for ratios


REVENUE = Kpi("Total Revenue ($MM)", "$MM", flow=True)
ARR = Kpi("Annual Recurring Revenue ($MM)", "$MM", flow=False)
NRR = Kpi("Net Revenue Retention (%)", "%", flow=False, decimals=1, bounds=(95.0, 135.0))
CHURN = Kpi("Customer Churn (%)", "%", flow=False, decimals=2, bounds=(0.5, 6.0))
CUSTOMERS = Kpi("Paying Customers", "customers", flow=False, decimals=0)
MAU = Kpi("Monthly Active Users", "users", flow=False, decimals=0)
ARPU = Kpi("Average Revenue per User ($)", "$", flow=False)
GMV = Kpi("Gross Merchandise Volume ($MM)", "$MM", flow=True)
ORDERS = Kpi("Orders Fulfilled", "orders", flow=True, decimals=0)
AOV = Kpi("Average Order Value ($)", "$", flow=False)
TPV = Kpi("Total Payment Volume ($B)", "$B", flow=True, decimals=3)
DEVICES = Kpi("Devices Shipped", "devices", flow=True, decimals=0)
MARGIN = Kpi("Gross Margin (%)", "%", flow=False, decimals=1, bounds=(20.0, 85.0))


@dataclass(frozen=True)
class Company:
    name: str
    ticker: str
    sector: str
    kpis: dict[Kpi, float]  # KPI -> starting value (2023Q1)
    growth: float  # quarter-over-quarter drift
    seasonality: float = 0.0  # Q4 bump for consumer businesses


COMPANIES = [
    Company("Orbitly Analytics", "ORBY", "Software",
            {REVENUE: 212.0, ARR: 790.0, NRR: 118.0, CUSTOMERS: 4_180, CHURN: 1.9}, 0.045),
    Company("Cobalt Workspace", "CBLT", "Software",
            {REVENUE: 138.0, ARR: 520.0, CUSTOMERS: 12_400, CHURN: 2.6}, 0.032),
    Company("Quillmark Media", "QMRK", "Digital Media",
            {REVENUE: 96.0, MAU: 41_000_000, ARPU: 2.35}, 0.018, 0.10),
    Company("Kestrel Security", "KSTL", "Cybersecurity",
            {REVENUE: 174.0, ARR: 655.0, NRR: 124.0, CUSTOMERS: 2_950}, 0.051),
    Company("Sentinel Grid", "SNTL", "Cybersecurity",
            {REVENUE: 61.0, ARR: 230.0, CHURN: 1.4}, 0.038),
    Company("Pinecrest Payments", "PNCR", "Payments",
            {REVENUE: 305.0, TPV: 38.5, CUSTOMERS: 88_000, MARGIN: 47.0}, 0.029, 0.06),
    Company("Fernway Insurance", "FRNW", "Insurtech",
            {REVENUE: 83.0, CUSTOMERS: 610_000, CHURN: 3.8, MARGIN: 31.0}, 0.027),
    Company("Lumora Health", "LUMO", "Digital Health",
            {REVENUE: 57.0, MAU: 3_200_000, CUSTOMERS: 540_000, ARPU: 11.9}, 0.041),
    Company("Brightleaf Learning", "BLFL", "Education",
            {REVENUE: 44.0, MAU: 9_800_000, ARPU: 4.1, CHURN: 4.9}, 0.022, -0.05),
    Company("Nordvik Games", "NRDV", "Gaming",
            {REVENUE: 121.0, MAU: 27_500_000, ARPU: 1.45}, 0.015, 0.14),
    Company("Maple & Mortar Home", "MMHM", "Marketplaces",
            {REVENUE: 162.0, GMV: 1_240.0, ORDERS: 5_600_000, AOV: 221.0}, 0.024, 0.18),
    Company("Copperfield Foods", "CPFD", "Food Delivery",
            {REVENUE: 233.0, GMV: 1_910.0, ORDERS: 61_000_000, AOV: 31.4}, 0.028, 0.05),
    Company("Harborline Travel", "HRBL", "Travel",
            {REVENUE: 188.0, GMV: 2_450.0, AOV: 612.0}, 0.021, 0.12),
    Company("Orbital Freight", "ORBF", "Logistics",
            {REVENUE: 402.0, ORDERS: 18_300_000, MARGIN: 23.5}, 0.017),
    Company("Voltaic Mobility", "VOLT", "Electric Mobility",
            {REVENUE: 515.0, DEVICES: 21_400, AOV: 24_300.0, MARGIN: 21.0}, 0.036, 0.08),
    Company("Aerolume Devices", "ARLM", "Consumer Hardware",
            {REVENUE: 267.0, DEVICES: 1_150_000, MARGIN: 38.0}, 0.012, 0.35),
]  # fmt: skip


def quarter_bounds(year: int, quarter: int) -> tuple[date, date]:
    start = date(year, 3 * quarter - 2, 1)
    end_month = 3 * quarter
    end_day = 31 if end_month in (3, 12) else 30
    return start, date(year, end_month, end_day)


def fmt(value: float, decimals: int) -> str:
    return f"{value:.{decimals}f}" if decimals else f"{round(value)}"


def row(
    company: str, ticker: str, sector: str, kpi: Kpi, year: int, quarter: int,
    estimate_type: str, value: float, as_of: date | None = None,
) -> list[str]:  # fmt: skip
    start, end = quarter_bounds(year, quarter)
    return [
        company, ticker, sector, kpi.name, start.isoformat(), end.isoformat(),
        f"{year}Q{quarter}", estimate_type, fmt(value, kpi.decimals), kpi.unit,
        as_of.isoformat() if as_of else "",
    ]  # fmt: skip


def series(rng: random.Random, kpi: Kpi, start: float, growth: float, season: float) -> list[float]:
    values: list[float] = []
    level = start
    for _, quarter in [*HISTORY, QTD_PERIOD]:
        if kpi.bounds:
            lo, hi = kpi.bounds
            level = min(hi, max(lo, level + rng.gauss(0, (hi - lo) * 0.015)))
            values.append(level)
            continue
        level *= 1 + growth + rng.gauss(0, 0.012)
        bump = season if (kpi.flow and quarter == 4) else 0.0
        values.append(level * (1 + bump))
    return values


def sample_rows() -> list[list[str]]:
    rng = random.Random(20260910)  # noqa: S311 - synthetic data, not security
    rows: list[list[str]] = []
    for c in COMPANIES:
        for kpi, start in c.kpis.items():
            values = series(rng, kpi, start, c.growth, c.seasonality)
            for (year, quarter), value in zip(HISTORY, values, strict=False):
                rows.append(
                    row(c.name, c.ticker, c.sector, kpi, year, quarter, "historical", value)
                )
            full_quarter = values[-1]
            for as_of, progress in zip(QTD_AS_OF, QTD_PROGRESS, strict=True):
                noise = 1 + rng.gauss(0, 0.02 * (1 - progress))
                value = full_quarter * noise * (progress if kpi.flow else 1.0)
                rows.append(row(c.name, c.ticker, c.sector, kpi, *QTD_PERIOD, "qtd", value, as_of))
    return rows


def edge_case_rows() -> list[list[str]]:
    """Three hand-shaped companies that exercise the empty/partial paths of every tool."""
    rows: list[list[str]] = []
    # History but no QTD at all -> get_kpi_qtd returns no_qtd_estimate with a recovery hint.
    for i, (year, quarter) in enumerate(HISTORY[4:]):
        rows.append(row("Gapwise Robotics", "GAPW", "Industrial Tech", REVENUE, year, quarter,
                        "historical", 64.0 + 2.5 * i))  # fmt: skip
        rows.append(row("Gapwise Robotics", "GAPW", "Industrial Tech", CUSTOMERS, year, quarter,
                        "historical", 820 + 35 * i))  # fmt: skip
    # Sparse, irregular history plus two QTD snapshots.
    for i, (year, quarter) in enumerate([(2023, 1), (2023, 3), (2024, 2), (2025, 1), (2026, 2)]):
        rows.append(row("Sparrow Bio Software", "SPRW", "Software", ARR, year, quarter,
                        "historical", 48.0 + 5.5 * i))  # fmt: skip
    for as_of, value in zip(QTD_AS_OF[:2], (70.2, 71.6), strict=True):
        rows.append(row("Sparrow Bio Software", "SPRW", "Software", ARR, *QTD_PERIOD, "qtd",
                        value, as_of))  # fmt: skip
    # Newly listed: QTD only, no history -> get_kpi_history returns no_data.
    for as_of, value in zip(QTD_AS_OF, (1_900, 2_650, 3_300, 4_050), strict=True):
        rows.append(row("Freshlist Labs", "FRSH", "Marketplaces", CUSTOMERS, *QTD_PERIOD, "qtd",
                        value, as_of))  # fmt: skip
    return rows


def render(rows: list[list[str]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(rows)
    return buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if committed CSVs are stale")
    args = parser.parse_args()
    outputs = {
        DATA / "kpi_sample.csv": render(sample_rows()),
        DATA / "demo_edge_cases.csv": render(edge_case_rows()),
    }
    stale = False
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                print(f"stale: {path.relative_to(ROOT)}", file=sys.stderr)
                stale = True
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({content.count(chr(10)) - 1} rows)")
    return 1 if stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
