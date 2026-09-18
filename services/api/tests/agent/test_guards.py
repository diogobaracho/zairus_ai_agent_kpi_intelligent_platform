from kpi_api.agent.guards import (
    CallLedger,
    canonical_call_key,
    preview,
    sanitize_tool_args,
    truncate_result,
)
from kpi_api.agent.types import McpToolSpec, ToolOutcome

SPEC = McpToolSpec(
    "get_kpi_qtd", "d", {"properties": {"ticker": {"type": "string"}, "kpi": {"type": "string"}}}
)


def test_sanitize_drops_unknown_and_non_scalars() -> None:
    clean, dropped = sanitize_tool_args(
        {"ticker": " orby\x00 ", "kpi": "revenue", "tenant_id": "x", "list": [1]}, SPEC
    )
    assert clean == {"ticker": "orby", "kpi": "revenue"} and set(dropped) == {"tenant_id", "list"}
    assert sanitize_tool_args("nope", SPEC) == ({}, [])
    long_value = "a" * 500
    assert len(sanitize_tool_args({"ticker": long_value}, SPEC)[0]["ticker"]) == 256
    assert sanitize_tool_args({"anything": 1}, None)[0] == {"anything": 1}


def test_truncate_and_preview() -> None:
    assert truncate_result("short", 10) == "short"
    out = truncate_result("x" * 100, 10)
    assert out.startswith("x" * 10) and "[truncated 90 chars" in out
    assert preview("  a   b  \n c ", 4) == "a b…" and preview("abc", 3) == "abc"


def test_ledger_flags_repeats() -> None:
    ledger = CallLedger(max_identical_successes=2)
    args = {"ticker": "ORBYY", "kpi": "revenue"}
    assert ledger.verdict("get_kpi_qtd", args) is None
    ledger.record("get_kpi_qtd", args, ToolOutcome.failed("company_not_found", "no"))
    assert ledger.verdict("get_kpi_qtd", args) == "repeated_failing_call"
    ok = {"ticker": "ORBY", "kpi": "revenue"}
    for _ in range(2):
        assert ledger.verdict("get_kpi_qtd", ok) is None
        ledger.record("get_kpi_qtd", ok, ToolOutcome(status="ok", text="{}"))
    assert ledger.verdict("get_kpi_qtd", ok) == "repeated_identical_call"
    assert canonical_call_key("t", {"b": 1, "a": 2}) == canonical_call_key("t", {"a": 2, "b": 1})
