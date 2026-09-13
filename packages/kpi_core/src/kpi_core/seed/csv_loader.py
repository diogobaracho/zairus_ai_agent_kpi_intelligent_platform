"""Parse the ZairusData KPI CSV into validated rows (pure; reused by the in-memory repository)."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from kpi_core.errors import InvalidPeriod
from kpi_core.fuzzy import kpi_display_name, kpi_slug
from kpi_core.models import EstimateType, UnitKind
from kpi_core.periods import Period

REQUIRED_COLUMNS = (
    "company_name", "ticker", "sector", "kpi", "period_start", "period_end",
    "period", "estimate_type", "value", "unit", "as_of",
)  # fmt: skip

_UNIT_KINDS: dict[str, tuple[UnitKind, int]] = {
    "$": ("currency", 1),
    "$MM": ("currency", 1_000_000),
    "$M": ("currency", 1_000_000),
    "$B": ("currency", 1_000_000_000),
    "%": ("percent", 1),
}


def unit_metadata(unit: str) -> tuple[UnitKind, int]:
    return _UNIT_KINDS.get(unit, ("count", 1))


class SeedRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", str_strip_whitespace=True)

    company_name: str = Field(min_length=1)
    ticker: str = Field(min_length=1, max_length=10)
    sector: str = Field(min_length=1)
    kpi: str = Field(min_length=1)
    period_start: date
    period_end: date
    period: str
    estimate_type: EstimateType
    value: float
    unit: str = Field(min_length=1)
    as_of: date | None = None

    @field_validator("ticker")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()

    @field_validator("estimate_type", mode="before")
    @classmethod
    def _lower(cls, v: str) -> str:
        return str(v).strip().lower()

    @field_validator("as_of", mode="before")
    @classmethod
    def _empty_as_none(cls, v: object) -> object:
        return None if v in ("", None) else v

    @field_validator("period")
    @classmethod
    def _period(cls, v: str) -> str:
        try:
            return str(Period.parse(v))
        except InvalidPeriod as exc:  # pydantic only converts ValueError into a validation error
            raise ValueError(exc.detail) from exc

    @model_validator(mode="after")
    def _consistency(self) -> SeedRow:
        if self.estimate_type == "historical" and self.as_of is not None:
            raise ValueError("historical rows must not carry as_of")
        if self.estimate_type == "qtd" and self.as_of is None:
            raise ValueError("qtd rows must carry as_of")
        if self.period_start >= self.period_end:
            raise ValueError("period_start must be before period_end")
        return self

    @property
    def kpi_slug(self) -> str:
        return kpi_slug(self.kpi)

    @property
    def kpi_display_name(self) -> str:
        return kpi_display_name(self.kpi)

    @property
    def unit_kind(self) -> UnitKind:
        return unit_metadata(self.unit)[0]

    @property
    def scale(self) -> int:
        return unit_metadata(self.unit)[1]


class CsvFormatError(ValueError):
    pass


def read_kpi_csv(path: Path | str) -> list[SeedRow]:
    """Read and validate every row; raises CsvFormatError naming the first bad row."""
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise CsvFormatError(f"{path.name}: missing columns {missing}")
        rows: list[SeedRow] = []
        for lineno, raw in enumerate(reader, start=2):
            try:
                rows.append(SeedRow.model_validate(raw))
            except ValueError as exc:
                raise CsvFormatError(f"{path.name}:{lineno}: {exc}") from exc
    return rows
