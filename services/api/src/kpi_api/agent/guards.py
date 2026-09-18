"""Guards against LLM tool-calling failure modes (see docs/security.md)."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from kpi_api.agent.types import McpToolSpec, ToolOutcome

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_ARG_CHARS = 256


def sanitize_tool_args(args: Any, spec: McpToolSpec | None) -> tuple[dict[str, Any], list[str]]:
    """Keep only scalar arguments the tool declares; cap lengths; strip control characters.

    Returns (clean_args, dropped_keys). Dropped keys are counted as identity-smuggling attempts
    when they look like tenant/user fields.
    """
    if not isinstance(args, dict):
        return {}, []
    allowed = set(spec.input_schema.get("properties", {})) if spec else None
    clean: dict[str, Any] = {}
    dropped: list[str] = []
    for key, value in args.items():
        if allowed is not None and key not in allowed:
            dropped.append(str(key))
            continue
        if isinstance(value, str):
            value = _CONTROL_RE.sub("", value).strip()[:MAX_ARG_CHARS]
        elif isinstance(value, bool | int | float) or value is None:
            pass
        else:
            dropped.append(str(key))
            continue
        clean[str(key)] = value
    return clean, dropped


def truncate_result(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    cut = len(text) - max_chars
    return text[:max_chars] + f"\n[truncated {cut} chars; ask for a narrower range or fewer items]"


def canonical_call_key(name: str, args: dict[str, Any]) -> str:
    payload = json.dumps({"name": name, "args": args}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


class CallLedger:
    """Remembers outcomes per (tool, args) so the loop can refuse to repeat a failing call."""

    def __init__(self, *, max_identical_successes: int = 2) -> None:
        self._failed: set[str] = set()
        self._successes: dict[str, int] = {}
        self.max_identical_successes = max_identical_successes

    def verdict(self, name: str, args: dict[str, Any]) -> str | None:
        key = canonical_call_key(name, args)
        if key in self._failed:
            return "repeated_failing_call"
        if self._successes.get(key, 0) >= self.max_identical_successes:
            return "repeated_identical_call"
        return None

    def record(self, name: str, args: dict[str, Any], outcome: ToolOutcome) -> None:
        key = canonical_call_key(name, args)
        if outcome.status == "ok":
            self._successes[key] = self._successes.get(key, 0) + 1
        else:
            self._failed.add(key)


def preview(text: str, limit: int = 300) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"
