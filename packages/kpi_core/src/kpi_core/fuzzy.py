"""Suggestions for near-misses: tickers, company names, KPI names, sectors.

Runs in-process with rapidfuzz over small candidate lists so the in-memory and SQL repositories
produce identical suggestions. An alias table maps everyday words ("revenue", "arr", "churn") to KPI
slugs before fuzzy matching.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz, process
from rapidfuzz.utils import default_process

from kpi_core.models import Suggestion

_UNIT_SUFFIX_RE = re.compile(r"\s*\([^)]*\)\s*$")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def kpi_slug(name: str) -> str:
    """Slug for a KPI name.

    "Total Revenue ($MM)" -> total_revenue; "Net Revenue Retention (%)" -> net_revenue_retention
    (dots removed, non-alphanumerics collapsed to underscores).
    """
    base = _UNIT_SUFFIX_RE.sub("", name).lower().replace(".", "")
    return _NON_ALNUM_RE.sub("_", base).strip("_")


def kpi_display_name(name: str) -> str:
    return _UNIT_SUFFIX_RE.sub("", name).strip()


KPI_ALIASES: dict[str, str] = {
    "revenue": "total_revenue",
    "revenues": "total_revenue",
    "total revenue": "total_revenue",
    "sales": "total_revenue",
    "top line": "total_revenue",
    "arr": "annual_recurring_revenue",
    "recurring revenue": "annual_recurring_revenue",
    "nrr": "net_revenue_retention",
    "ndr": "net_revenue_retention",
    "retention": "net_revenue_retention",
    "net retention": "net_revenue_retention",
    "churn": "customer_churn",
    "churn rate": "customer_churn",
    "customers": "paying_customers",
    "clients": "paying_customers",
    "paid customers": "paying_customers",
    "mau": "monthly_active_users",
    "users": "monthly_active_users",
    "active users": "monthly_active_users",
    "arpu": "average_revenue_per_user",
    "gmv": "gross_merchandise_volume",
    "orders": "orders_fulfilled",
    "aov": "average_order_value",
    "basket size": "average_order_value",
    "tpv": "total_payment_volume",
    "payment volume": "total_payment_volume",
    "shipments": "devices_shipped",
    "units shipped": "devices_shipped",
    "margin": "gross_margin",
}


def normalize_key(text: str) -> str:
    return str(default_process(text))


def resolve_alias(query: str) -> str | None:
    return KPI_ALIASES.get(normalize_key(query))


@dataclass(frozen=True)
class Candidate:
    value: str
    label: str
    keys: tuple[str, ...] = field(default_factory=tuple)

    def all_keys(self) -> tuple[str, ...]:
        return (self.value, self.label, *self.keys)


def suggest(
    query: str,
    candidates: list[Candidate],
    *,
    limit: int = 5,
    cutoff: float = 55.0,
) -> list[Suggestion]:
    """Best-scoring candidates for `query`, deduplicated by value, sorted by score desc."""
    q = normalize_key(query)
    if not q or not candidates:
        return []
    keyed: dict[str, Candidate] = {}
    for cand in candidates:
        for key in cand.all_keys():
            nk = normalize_key(key)
            if nk and nk not in keyed:
                keyed[nk] = cand
    matches = process.extract(q, list(keyed.keys()), scorer=fuzz.WRatio, limit=len(keyed))
    best: dict[str, Suggestion] = {}
    for key, score, _ in matches:
        if score < cutoff:
            continue
        cand = keyed[key]
        if cand.value not in best or best[cand.value].score < score:
            best[cand.value] = Suggestion(
                value=cand.value, label=cand.label, score=round(float(score), 1)
            )
    return sorted(best.values(), key=lambda s: (-s.score, s.value))[:limit]
