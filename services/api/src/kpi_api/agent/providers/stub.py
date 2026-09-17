"""Deterministic provider so the whole stack runs and is testable without an API key.

Scripted mode replays explicit turns (used by tests to simulate every failure mode).
Heuristic mode derives tool calls from the question and tool results, including the
error -> suggestion -> retry flow, and writes an answer that cites the data it received.
"""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from kpi_api.agent.providers.base import LLMProvider
from kpi_api.agent.types import (
    LLMEvent,
    StopReason,
    TextDelta,
    ToolUseComplete,
    ToolUseStart,
    TurnEnd,
    Usage,
)
from kpi_core.fuzzy import resolve_alias

_TICKER_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,5}\b")
_STOP_WORDS = {
    "QTD",
    "KPI",
    "KPIS",
    "US",
    "U",
    "S",
    "YOY",
    "QOQ",
    "I",
    "A",
    "THE",
    "IS",
    "OF",
    "MM",
}
_QTD_HINTS = (
    "qtd",
    "quarter to date",
    "quarter-to-date",
    "this quarter",
    "current quarter",
    "so far",
)
_HISTORY_HINTS = (
    "history",
    "historical",
    "trend",
    "over time",
    "last",
    "past",
    "quarters",
    "growth",
    "year",
)
_KPI_WORDS = [
    "total revenue", "recurring revenue", "revenue", "sales", "arr", "net retention", "nrr",
    "churn", "customers", "active users", "mau", "arpu", "gmv", "orders", "aov",
    "payment volume", "tpv", "shipments", "margin",
]  # fmt: skip


@dataclass
class StubTurn:
    text: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    stop_reason: StopReason | None = None
    parse_error: str | None = None


class StubLLMProvider(LLMProvider):
    name = "stub"

    def __init__(self, script: list[StubTurn] | None = None, *, model: str = "stub-1") -> None:
        self.script = list(script) if script is not None else None
        self.model = model
        self._counter = 0
        self.seen_messages: list[list[dict[str, Any]]] = []

    def _next_id(self) -> str:
        self._counter += 1
        return f"stub_tool_{self._counter}"

    async def stream_turn(
        self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AsyncIterator[LLMEvent]:
        self.seen_messages.append([dict(m) for m in messages])
        turn = self.script.pop(0) if self.script else heuristic_turn(messages)
        content: list[dict[str, Any]] = []
        if turn.text:
            for chunk in _chunks(turn.text):
                yield TextDelta(chunk)
            content.append({"type": "text", "text": turn.text})
        if turn.parse_error:
            yield ToolUseComplete(
                id=self._next_id(), name="unknown", input=None, parse_error=turn.parse_error
            )
        for call in turn.tool_calls:
            tool_id = self._next_id()
            yield ToolUseStart(tool_id, call["name"])
            yield ToolUseComplete(id=tool_id, name=call["name"], input=call.get("input", {}))
            content.append(
                {
                    "type": "tool_use",
                    "id": tool_id,
                    "name": call["name"],
                    "input": call.get("input", {}),
                }
            )
        stop: StopReason = turn.stop_reason or ("tool_use" if turn.tool_calls else "end_turn")
        yield TurnEnd(
            stop_reason=stop,
            usage=Usage(len(str(messages)) // 4, len(turn.text or "") // 4),
            assistant_content=content,
        )


def _chunks(text: str, size: int = 24) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


# --- heuristic mode --------------------------------------------------------------------------
def _last_user_text(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user" and isinstance(message.get("content"), str):
            return str(message["content"])
    return ""


def _last_tool_results(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    last = messages[-1] if messages else {}
    if last.get("role") != "user" or not isinstance(last.get("content"), list):
        return []
    return [b for b in last["content"] if isinstance(b, dict) and b.get("type") == "tool_result"]


def _last_tool_uses(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for message in reversed(messages):
        if message.get("role") == "assistant" and isinstance(message.get("content"), list):
            return [b for b in message["content"] if b.get("type") == "tool_use"]
    return []


def _extract_ticker(text: str) -> str | None:
    for token in _TICKER_RE.findall(text):
        if token not in _STOP_WORDS:
            return str(token)
    return None


def _extract_kpi(text: str) -> str | None:
    lowered = text.lower()
    for word in _KPI_WORDS:
        if word in lowered:
            return resolve_alias(word) or word
    return None


def _wants_qtd(text: str) -> bool:
    lowered = text.lower()
    return any(h in lowered for h in _QTD_HINTS)


def _wants_history(text: str) -> bool:
    lowered = text.lower()
    return any(h in lowered for h in _HISTORY_HINTS)


def heuristic_turn(messages: list[dict[str, Any]]) -> StubTurn:
    question = _last_user_text(messages)
    results = _last_tool_results(messages)
    if not results:
        return _first_turn(question)
    uses = _last_tool_uses(messages)
    retried = sum(1 for m in messages if m.get("role") == "assistant") >= 2
    for use, result in zip(uses, results, strict=False):
        payload = _payload(result)
        error = payload.get("error") if isinstance(payload, dict) else None
        if result.get("is_error") and error and not retried:
            retry = _retry_call(use, error)
            if retry:
                return StubTurn(tool_calls=[retry])
    return StubTurn(text=_answer(question, uses, results))


def _first_turn(question: str) -> StubTurn:
    ticker = _extract_ticker(question)
    kpi = _extract_kpi(question)
    if ticker and kpi:
        tool = "get_kpi_qtd" if _wants_qtd(question) else "get_kpi_history"
        return StubTurn(tool_calls=[{"name": tool, "input": {"ticker": ticker, "kpi": kpi}}])
    if ticker:
        return StubTurn(tool_calls=[{"name": "list_company_kpis", "input": {"ticker": ticker}}])
    tokens = re.findall(r"[A-Za-z][A-Za-z.]+", question)
    words = [
        w
        for i, w in enumerate(tokens)
        if w[0].isupper() and w.upper() not in _STOP_WORDS and (i > 0 or len(tokens) == 1)
    ]
    query = words[0] if words else None
    return StubTurn(
        tool_calls=[{"name": "search_companies", "input": {"query": query} if query else {}}]
    )


def _payload(result: dict[str, Any]) -> Any:
    content = result.get("content")
    if isinstance(content, list):
        content = "".join(str(b.get("text", "")) for b in content if isinstance(b, dict))
    try:
        return json.loads(str(content))
    except (TypeError, ValueError):
        return {}


def _retry_call(use: dict[str, Any], error: dict[str, Any]) -> dict[str, Any] | None:
    suggestions = error.get("suggestions") or []
    if not suggestions:
        return None
    value = suggestions[0].get("value")
    args = dict(use.get("input", {}))
    code = error.get("code")
    if code == "company_not_found" and "ticker" in args:
        args["ticker"] = value
    elif code == "kpi_not_found" and "kpi" in args:
        args["kpi"] = value
    elif code == "sector_not_found" and "sector" in args:
        args["sector"] = value
    else:
        return None
    return {"name": use["name"], "input": args}


def _fmt(value: Any, unit: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    text = f"{number:,.2f}" if unit in ("$", "$MM") else f"{number:,.0f}"
    return f"{text} {unit}".strip()


def _answer(question: str, uses: list[dict[str, Any]], results: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for use, result in zip(uses, results, strict=False):
        payload = _payload(result)
        if not isinstance(payload, dict):
            continue
        if result.get("is_error"):
            error = payload.get("error", {})
            hint = error.get("recovery_hint") or ""
            lines.append(
                f"I could not complete this: {error.get('message', 'tool error')}. {hint}".strip()
            )
            continue
        name = use.get("name")
        company = payload.get("company", {})
        kpi = payload.get("kpi", {})
        label = f"{company.get('ticker', '?')} {kpi.get('name', '')}".strip()
        if name == "get_kpi_qtd":
            latest = payload.get("latest")
            if latest:
                prior = payload.get("prior_quarter") or {}
                line = (
                    f"{label} QTD ({payload.get('period')}) as of {latest['as_of']}: "
                    f"{_fmt(latest['value'], latest['unit'])}"
                )
                if prior:
                    change = (
                        (float(latest["value"]) - float(prior["value"]))
                        / float(prior["value"])
                        * 100
                        if float(prior["value"])
                        else 0.0
                    )
                    line += (
                        f"; prior completed quarter {prior['period']}: "
                        f"{_fmt(prior['value'], prior['unit'])} ({change:+.1f}%)"
                    )
                lines.append(line + ".")
            else:
                lines.append(f"{label}: {payload.get('note') or 'no QTD estimate is published'}")
        elif name == "get_kpi_history":
            points = payload.get("points", [])
            if points:
                first, last = points[0], points[-1]
                change = (
                    (float(last["value"]) - float(first["value"])) / float(first["value"]) * 100
                    if float(first["value"])
                    else 0.0
                )
                lines.append(
                    f"{label} history: {first['period']} = "
                    f"{_fmt(first['value'], first['unit'])} ... {last['period']} = "
                    f"{_fmt(last['value'], last['unit'])} "
                    f"({payload.get('count')} quarters, {change:+.1f}% overall)."
                )
                if payload.get("note"):
                    lines.append(str(payload["note"]))
            else:
                lines.append(f"{label}: {payload.get('note') or 'no historical estimates'}")
        elif name == "list_company_kpis":
            names = ", ".join(k.get("name", "") for k in payload.get("kpis", []))
            lines.append(
                f"{company.get('name', '')} ({company.get('ticker', '')}) publishes: {names}."
            )
        elif name == "search_companies":
            companies = payload.get("companies", [])
            if companies:
                listed = "; ".join(
                    f"{c['name']} ({c['ticker']}, {c['sector']})" for c in companies[:10]
                )
                lines.append(f"Found {payload.get('total')} companies: {listed}.")
            else:
                sugg = ", ".join(s.get("value", "") for s in payload.get("suggestions", []))
                lines.append(f"No company matched. Closest tickers: {sugg}.")
    return "\n".join(lines) or "I could not find data for that question."
