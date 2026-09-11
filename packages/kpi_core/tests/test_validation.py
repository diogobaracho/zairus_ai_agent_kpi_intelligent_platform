import pytest

from kpi_core.errors import InvalidTicker, ValidationError
from kpi_core.validation import (
    clamp_limit,
    clamp_offset,
    normalize_kpi_query,
    normalize_query,
    normalize_ticker,
    sanitize_text,
)


def test_sanitize_text_strips_controls_and_whitespace() -> None:
    assert sanitize_text("  a\x00b   c\n", max_len=10) == "ab c"
    assert sanitize_text(None, max_len=10) == ""
    with pytest.raises(ValidationError):
        sanitize_text("x" * 11, max_len=10)
    with pytest.raises(ValidationError):
        sanitize_text(123, max_len=10)  # type: ignore[arg-type]


def test_normalize_ticker() -> None:
    assert normalize_ticker(" orby ") == "ORBY"
    assert normalize_ticker("brk.b") == "BRK.B"
    for bad in ["", "-abc", "a b", "a" * 11]:
        with pytest.raises((InvalidTicker, ValidationError)):
            normalize_ticker(bad)


def test_normalize_queries() -> None:
    assert normalize_query("  Orbitly  ") == "Orbitly"
    assert normalize_kpi_query("Total Revenue") == "Total Revenue"
    with pytest.raises(ValidationError):
        normalize_kpi_query("   ")


def test_clamps() -> None:
    assert clamp_limit(None, default=20, maximum=100) == 20
    assert clamp_limit(50, default=20, maximum=100) == 50
    with pytest.raises(ValidationError):
        clamp_limit(101, default=20, maximum=100)
    with pytest.raises(ValidationError):
        clamp_limit(0, default=20, maximum=100)
    with pytest.raises(ValidationError):
        clamp_limit(True, default=20, maximum=100)
    assert clamp_offset(None) == 0 and clamp_offset(7) == 7
    with pytest.raises(ValidationError):
        clamp_offset(-1)
