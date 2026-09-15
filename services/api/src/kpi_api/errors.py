"""Exception handlers: every error becomes RFC 9457 application/problem+json with a trace id."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from kpi_core.errors import KpiError
from kpi_core.obs.correlation import get_trace_id

logger = logging.getLogger(__name__)
PROBLEM = "application/problem+json"


def trace_id_for(request: Request) -> str | None:
    """ContextVar first; scope state as a fallback for handlers that run outside our middleware
    (Starlette's ServerErrorMiddleware is outermost, so the ContextVar is already reset there)."""
    return get_trace_id() or request.scope.get("state", {}).get("trace_id")


def problem_response(error: KpiError, request: Request) -> JSONResponse:
    body = error.to_problem(instance=request.url.path, trace_id=trace_id_for(request))
    headers = {}
    if error.code == "rate_limited" and "retry_after_seconds" in error.extra:
        headers["Retry-After"] = str(int(error.extra["retry_after_seconds"]))
    return JSONResponse(body, status_code=error.status, media_type=PROBLEM, headers=headers)


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(KpiError)
    async def _kpi_error(request: Request, exc: KpiError) -> JSONResponse:
        return problem_response(exc, request)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "loc": [str(part) for part in e.get("loc", [])],
                "msg": e.get("msg"),
                "type": e.get("type"),
            }
            for e in exc.errors()
        ]
        body = {
            "type": "/docs/reference/error-codes#validation_error",
            "title": "Request failed validation",
            "status": 400,
            "detail": "; ".join(f"{'.'.join(e['loc'])}: {e['msg']}" for e in errors)
            or "invalid request",
            "code": "validation_error",
            "errors": errors,
            "instance": request.url.path,
            "trace_id": trace_id_for(request),
        }
        return JSONResponse(body, status_code=400, media_type=PROBLEM)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "not_found", 405: "method_not_allowed", 413: "payload_too_large"}.get(
            exc.status_code, "http_error"
        )
        body = {
            "type": f"/docs/reference/error-codes#{code}",
            "title": str(exc.detail),
            "status": exc.status_code,
            "detail": str(exc.detail),
            "code": code,
            "instance": request.url.path,
            "trace_id": trace_id_for(request),
        }
        return JSONResponse(
            body, status_code=exc.status_code, media_type=PROBLEM, headers=exc.headers
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", extra={"path": request.url.path})
        body = {
            "type": "/docs/reference/error-codes#internal_error",
            "title": "Internal error",
            "status": 500,
            "detail": "An unexpected error occurred. Quote the trace_id when reporting it.",
            "code": "internal_error",
            "instance": request.url.path,
            "trace_id": trace_id_for(request),
        }
        return JSONResponse(body, status_code=500, media_type=PROBLEM)
