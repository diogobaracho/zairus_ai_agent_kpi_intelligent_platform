"""Reject unknown keys, non-scalar values, control characters and oversized strings before the
tool (and pydantic) see them, so the client always receives our envelope."""

from __future__ import annotations

import re
from typing import Any

from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

from kpi_core.errors import ValidationError
from kpi_mcp.envelope import kpi_error_to_tool_error

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SCALARS = (str, int, float, bool, type(None))


class ArgSanitizingMiddleware(Middleware):
    def __init__(self, allowed: dict[str, set[str]], *, max_chars: int = 256) -> None:
        self.allowed = allowed
        self.max_chars = max_chars

    def clean(self, tool: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
        args = dict(arguments or {})
        allowed = self.allowed.get(tool)
        if allowed is not None:
            unknown = sorted(set(args) - allowed)
            if unknown:
                raise ValidationError(
                    f"Unknown argument(s) for {tool}: {', '.join(unknown)}",
                    recovery_hint=f"Use only: {', '.join(sorted(allowed))}.",
                )
        cleaned: dict[str, Any] = {}
        for key, value in args.items():
            if not isinstance(value, _SCALARS):
                raise ValidationError(
                    f"Argument '{key}' must be a string, number, boolean or null",
                    recovery_hint="Pass scalar values only.",
                )
            if isinstance(value, str):
                if _CONTROL_RE.search(value):
                    raise ValidationError(
                        f"Argument '{key}' contains control characters",
                        recovery_hint="Remove non-printable characters.",
                    )
                if len(value) > self.max_chars:
                    raise ValidationError(
                        f"Argument '{key}' is too long ({len(value)} chars, max {self.max_chars})",
                        recovery_hint=f"Shorten '{key}' to at most {self.max_chars} characters.",
                    )
                value = value.strip()
            cleaned[key] = value
        return cleaned

    async def on_call_tool(
        self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]
    ) -> Any:
        message = context.message
        try:
            cleaned = self.clean(message.name, message.arguments)
        except ValidationError as error:
            raise kpi_error_to_tool_error(error) from None
        updated = context.copy(message=message.model_copy(update={"arguments": cleaned}))
        return await call_next(updated)
