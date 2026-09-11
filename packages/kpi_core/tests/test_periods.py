import pytest

from kpi_core.errors import InvalidPeriod, InvalidPeriodRange
from kpi_core.periods import Period, missing_periods, period_span, validate_range


def test_parse_and_str() -> None:
    p = Period.parse(" 2024q3 ")
    assert (p.year, p.quarter, str(p)) == (2024, 3, "2024Q3")
    assert (p.start_date.isoformat(), p.end_date.isoformat()) == ("2024-07-01", "2024-09-30")


@pytest.mark.parametrize("bad", ["Q3 2024", "2024-Q3", "2024Q5", "24Q1", "", "abcd"])
def test_parse_rejects(bad: str) -> None:
    with pytest.raises(InvalidPeriod) as exc:
        Period.parse(bad)
    assert exc.value.code == "invalid_period" and "YYYYQn" in (exc.value.recovery_hint or "")


def test_next_prev_and_order() -> None:
    assert Period(2024, 4).next() == Period(2025, 1)
    assert Period(2025, 1).prev() == Period(2024, 4)
    assert Period(2024, 1) < Period(2024, 2) < Period(2025, 1)


def test_validate_range() -> None:
    assert validate_range(None, None) == (None, None)
    start, end = validate_range("2024Q1", "2024Q4")
    assert (str(start), str(end)) == ("2024Q1", "2024Q4")
    with pytest.raises(InvalidPeriodRange):
        validate_range("2025Q1", "2024Q4")


def test_span_and_gaps() -> None:
    assert [str(p) for p in period_span(Period(2024, 3), Period(2025, 1))] == [
        "2024Q3",
        "2024Q4",
        "2025Q1",
    ]
    assert missing_periods(["2022Q1", "2022Q3", "2023Q2"]) == ["2022Q2", "2022Q4", "2023Q1"]
    assert missing_periods(["2022Q1"]) == []
