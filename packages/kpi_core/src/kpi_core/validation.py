"""Input normalisation and sanitisation shared by both adapters."""

from __future__ import annotations

import re

from kpi_core.errors import InvalidTicker, ValidationError

TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,9}$")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WS_RE = re.compile(r"\s+")

MAX_QUERY_LEN = 64
MAX_KPI_LEN = 80
MAX_TICKER_LEN = 10


def sanitize_text(raw: str | None, *, max_len: int, field: str = "value") -> str:
    """Strip control characters, collapse whitespace, cap length (raises when too long)."""
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raise ValidationError(f"{field} must be a string")
    text = _WS_RE.sub(" ", _CONTROL_RE.sub("", raw)).strip()
    if len(text) > max_len:
        raise ValidationError(
            f"{field} is too long ({len(text)} chars, max {max_len})",
            recovery_hint=f"Shorten {field} to at most {max_len} characters.",
        )
    return text


def normalize_ticker(raw: str | None) -> str:
    text = sanitize_text(raw, max_len=MAX_QUERY_LEN, field="ticker").upper()
    if not TICKER_RE.match(text):
        raise InvalidTicker(
            f"ticker '{raw}' is not a valid ticker symbol",
            recovery_hint="Tickers are 1-10 characters: letters, digits, '.', '-'. "
            "Call search_companies with the company name if you are unsure.",
        )
    return text


def normalize_query(raw: str | None, *, field: str = "query") -> str:
    return sanitize_text(raw, max_len=MAX_QUERY_LEN, field=field)


def normalize_kpi_query(raw: str | None) -> str:
    text = sanitize_text(raw, max_len=MAX_KPI_LEN, field="kpi")
    if not text:
        raise ValidationError("kpi must not be empty", recovery_hint="Pass a KPI slug or name.")
    return text


def clamp_limit(limit: int | None, *, default: int, maximum: int) -> int:
    if limit is None:
        return default
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValidationError("limit must be a positive integer")
    if limit > maximum:
        raise ValidationError(
            f"limit {limit} exceeds the maximum of {maximum}",
            recovery_hint=f"Use limit <= {maximum}.",
        )
    return limit


def clamp_offset(offset: int | None) -> int:
    if offset is None:
        return 0
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValidationError("offset must be a non-negative integer")
    return offset
