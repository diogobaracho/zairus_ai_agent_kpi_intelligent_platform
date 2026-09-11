"""Fiscal-quarter labels (`YYYYQn`) as a value object."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from kpi_core.errors import InvalidPeriod, InvalidPeriodRange

PERIOD_RE = re.compile(r"^(?P<year>\d{4})Q(?P<q>[1-4])$")
_QUARTER_BOUNDS = {
    1: ((1, 1), (3, 31)),
    2: ((4, 1), (6, 30)),
    3: ((7, 1), (9, 30)),
    4: ((10, 1), (12, 31)),
}


@dataclass(frozen=True, order=True, slots=True)
class Period:
    year: int
    quarter: int

    @classmethod
    def parse(cls, raw: str, *, field: str = "period") -> Period:
        text = (raw or "").strip().upper().replace(" ", "")
        match = PERIOD_RE.match(text)
        if not match:
            raise InvalidPeriod(
                f"{field} '{raw}' is not a valid fiscal quarter label",
                recovery_hint="Use the format YYYYQn, for example 2024Q3.",
            )
        return cls(int(match.group("year")), int(match.group("q")))

    def __str__(self) -> str:
        return f"{self.year}Q{self.quarter}"

    @property
    def start_date(self) -> date:
        return date(self.year, *_QUARTER_BOUNDS[self.quarter][0])

    @property
    def end_date(self) -> date:
        return date(self.year, *_QUARTER_BOUNDS[self.quarter][1])

    def next(self) -> Period:
        return (
            Period(self.year + 1, 1) if self.quarter == 4 else Period(self.year, self.quarter + 1)
        )

    def prev(self) -> Period:
        return (
            Period(self.year - 1, 4) if self.quarter == 1 else Period(self.year, self.quarter - 1)
        )


def validate_range(
    from_period: str | None, to_period: str | None
) -> tuple[Period | None, Period | None]:
    start = Period.parse(from_period, field="from_period") if from_period else None
    end = Period.parse(to_period, field="to_period") if to_period else None
    if start and end and start > end:
        raise InvalidPeriodRange(
            f"from_period {start} is after to_period {end}",
            recovery_hint="Swap the values or drop one bound.",
        )
    return start, end


def period_span(first: Period, last: Period) -> list[Period]:
    """Every quarter from `first` to `last` inclusive."""
    out: list[Period] = []
    cur = first
    while cur <= last:
        out.append(cur)
        cur = cur.next()
    return out


def missing_periods(present: list[str]) -> list[str]:
    """Quarters missing between the first and last present label (chronological gaps)."""
    if len(present) < 2:
        return []
    parsed = sorted(Period.parse(p) for p in present)
    have = set(parsed)
    return [str(p) for p in period_span(parsed[0], parsed[-1]) if p not in have]
