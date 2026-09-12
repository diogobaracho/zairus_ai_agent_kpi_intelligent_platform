from pathlib import Path

import pytest

from kpi_core.seed.csv_loader import CsvFormatError, SeedRow, read_kpi_csv


def test_reads_sample(sample_csv_path: Path) -> None:
    rows = read_kpi_csv(sample_csv_path)
    assert len(rows) == 1062
    assert len({r.ticker for r in rows}) == 16 and len({r.sector for r in rows}) == 14
    qtd = [r for r in rows if r.estimate_type == "qtd"]
    assert len(qtd) == 236 and all(r.as_of is not None for r in qtd)
    rev = next(r for r in rows if r.kpi == "Total Revenue ($MM)")
    assert (rev.kpi_slug, rev.unit_kind, rev.scale) == ("total_revenue", "currency", 1_000_000)
    tpv = next(r for r in rows if r.kpi == "Total Payment Volume ($B)")
    assert (tpv.unit_kind, tpv.scale) == ("currency", 1_000_000_000)


def test_reads_edge_cases(edge_cases_csv_path: Path) -> None:
    rows = read_kpi_csv(edge_cases_csv_path)
    assert {r.ticker for r in rows} == {"GAPW", "SPRW", "FRSH"}


def test_row_validation_rules() -> None:
    base = dict(
        company_name="X",
        ticker="x",
        sector="S",
        kpi="Orders Fulfilled",
        period_start="2024-01-01",
        period_end="2024-03-31",
        period="2024Q1",
        estimate_type="Historical",
        value="1.5",
        unit="orders",
        as_of="",
    )
    row = SeedRow.model_validate(base)
    assert row.ticker == "X" and row.estimate_type == "historical" and row.as_of is None
    with pytest.raises(ValueError):
        SeedRow.model_validate({**base, "estimate_type": "qtd"})  # qtd needs as_of
    with pytest.raises(ValueError):
        SeedRow.model_validate({**base, "as_of": "2024-02-01"})  # historical must not have as_of
    with pytest.raises(ValueError):
        SeedRow.model_validate({**base, "period": "Q1-2024"})


def test_missing_columns(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("ticker,kpi\nORBY,x\n")
    with pytest.raises(CsvFormatError):
        read_kpi_csv(bad)
    bad.write_text(
        "company_name,ticker,sector,kpi,period_start,period_end,period,estimate_type,value,unit,as_of\n"
        "A,A,S,K,2024-01-01,2024-03-31,2024Q1,historical,notanumber,orders,\n"
    )
    with pytest.raises(CsvFormatError, match=r"bad\.csv:2"):
        read_kpi_csv(bad)
