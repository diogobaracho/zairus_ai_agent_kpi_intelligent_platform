"""Structured JSON logging with the trace id on every line.

Stdlib `logging` + python-json-logger: uvicorn, SQLAlchemy, FastMCP and the Anthropic SDK all
log through stdlib, so one root handler captures everything. `log_event()` is the single call
site for discrete, queryable events (`tool_call`, `http_request`, `llm_turn`, `agent_run`).
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from pythonjsonlogger import json as pyjsonlogger

from kpi_core.obs.correlation import get_trace_id

_EVENT_LOGGER = "kpi.events"
_HANDLER_MARKER = "_kpi_json_handler"
_SECRET_KEYS = ("api_key", "password", "secret", "token", "authorization")


class _TraceFilter(logging.Filter):
    def __init__(self, service: str) -> None:
        super().__init__()
        self.service = service

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id() or "-"
        record.service = self.service
        return True


def redact(fields: dict[str, Any]) -> dict[str, Any]:
    """Mask values whose key looks like a secret. Applied to every event's fields."""
    out: dict[str, Any] = {}
    for key, value in fields.items():
        if any(marker in key.lower() for marker in _SECRET_KEYS):
            out[key] = "***"
        elif isinstance(value, dict):
            out[key] = redact(value)
        else:
            out[key] = value
    return out


def configure_logging(service: str, level: str = "INFO") -> None:
    """Idempotent; safe to call repeatedly. Logs go to stderr so stdio MCP stays clean."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    if any(getattr(h, _HANDLER_MARKER, False) for h in root.handlers):
        return
    handler = logging.StreamHandler(sys.stderr)
    setattr(handler, _HANDLER_MARKER, True)
    handler.addFilter(_TraceFilter(service))
    handler.setFormatter(
        pyjsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(trace_id)s %(service)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
        )
    )
    root.addHandler(handler)
    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    root.info("logging configured", extra={"level_name": level.upper()})


def log_event(name: str, **fields: Any) -> None:
    """Emit one structured, queryable event line."""
    logging.getLogger(_EVENT_LOGGER).info(name, extra={"event": name, **redact(fields)})
