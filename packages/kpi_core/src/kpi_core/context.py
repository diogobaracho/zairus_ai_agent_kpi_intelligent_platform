"""Request context: who is asking, on behalf of which tenant, under which trace id.

Built server-side by the adapter (REST middleware, MCP middleware, CLI). The LLM never supplies
any of these values: tool schemas have no such parameters and unknown keys are dropped.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Literal

Caller = Literal["rest", "mcp", "agent", "cli", "test"]


@dataclass(frozen=True, slots=True)
class Principal:
    kind: Literal["anonymous", "service", "user"] = "anonymous"
    id: str = "anonymous"


@dataclass(frozen=True, slots=True)
class RequestContext:
    trace_id: str
    tenant_id: str = "default"
    principal: Principal = field(default_factory=Principal)
    caller: Caller = "rest"
    session_id: str | None = None


_current: ContextVar[RequestContext | None] = ContextVar("kpi_request_context", default=None)


def new_trace_id() -> str:
    """Short enough to read aloud, random enough not to collide."""
    return uuid.uuid4().hex[:16]


def system_context(caller: Caller = "cli", tenant_id: str = "default") -> RequestContext:
    return RequestContext(trace_id=new_trace_id(), tenant_id=tenant_id, caller=caller)


def current_context() -> RequestContext | None:
    return _current.get()


def bind_context(ctx: RequestContext) -> Token[RequestContext | None]:
    return _current.set(ctx)


def reset_context(token: Token[RequestContext | None]) -> None:
    _current.reset(token)
