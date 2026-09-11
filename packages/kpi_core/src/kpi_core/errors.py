"""The error hierarchy and its two serialisations.

`KpiError` subclasses are the supported way to produce a client-facing failure. REST renders
`to_problem()` (RFC 9457); MCP renders `to_tool_envelope()`. Anything that is not a `KpiError`
reaching an adapter is a bug and is reported as `internal_error` with details masked.

`code` is a stable machine-readable contract (docs/reference/error-codes.md); `title` is
human-readable and may be reworded; `suggestions` and `recovery_hint` are what let an LLM
recover from a wrong ticker or a misspelled KPI in one retry.
"""

from __future__ import annotations

from typing import Any

from kpi_core.models import Suggestion


class KpiError(Exception):
    status: int = 500
    code: str = "internal_error"
    title: str = "Internal error"
    retryable: bool = False

    def __init__(
        self,
        detail: str,
        *,
        suggestions: list[Suggestion] | None = None,
        recovery_hint: str | None = None,
        **extra: Any,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.suggestions = suggestions or []
        self.recovery_hint = recovery_hint
        self.extra = extra

    def _suggestions_json(self) -> list[dict[str, Any]]:
        return [s.model_dump() for s in self.suggestions]

    def to_problem(
        self, *, instance: str | None = None, trace_id: str | None = None
    ) -> dict[str, Any]:
        problem: dict[str, Any] = {
            "type": f"/docs/reference/error-codes#{self.code}",
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "code": self.code,
        }
        if self.suggestions:
            problem["suggestions"] = self._suggestions_json()
        if self.recovery_hint:
            problem["recovery_hint"] = self.recovery_hint
        if instance is not None:
            problem["instance"] = instance
        if trace_id is not None:
            problem["trace_id"] = trace_id
        problem.update(self.extra)
        return problem

    def to_tool_envelope(self, *, trace_id: str | None = None) -> dict[str, Any]:
        error: dict[str, Any] = {
            "code": self.code,
            "message": self.detail,
            "suggestions": self._suggestions_json(),
            "recovery_hint": self.recovery_hint,
            "retryable": self.retryable,
            "trace_id": trace_id,
        }
        error.update(self.extra)
        return {"error": error}


class ValidationError(KpiError):
    status = 400
    code = "validation_error"
    title = "Request failed validation"
    retryable = True


class InvalidTicker(ValidationError):
    code = "invalid_ticker"
    title = "Invalid ticker"


class InvalidPeriod(ValidationError):
    code = "invalid_period"
    title = "Invalid period"


class InvalidPeriodRange(ValidationError):
    code = "invalid_period_range"
    title = "Invalid period range"


class NotFound(KpiError):
    status = 404
    code = "not_found"
    title = "Not found"
    retryable = True


class CompanyNotFound(NotFound):
    code = "company_not_found"
    title = "Company not found"


class KpiNotFound(NotFound):
    code = "kpi_not_found"
    title = "KPI not found"


class SectorNotFound(NotFound):
    code = "sector_not_found"
    title = "Sector not found"


class ConversationNotFound(NotFound):
    code = "conversation_not_found"
    title = "Conversation not found"
    retryable = False


class PayloadTooLarge(KpiError):
    status = 413
    code = "payload_too_large"
    title = "Payload too large"


class AgentBudgetExceeded(KpiError):
    status = 422
    code = "agent_budget_exceeded"
    title = "Agent budget exceeded"


class RateLimited(KpiError):
    status = 429
    code = "rate_limited"
    title = "Too many requests"
    retryable = True


class UpstreamUnavailable(KpiError):
    status = 503
    code = "upstream_unavailable"
    title = "Upstream unavailable"
    retryable = True


class ToolTimeout(KpiError):
    status = 504
    code = "tool_timeout"
    title = "Tool call timed out"
    retryable = True
