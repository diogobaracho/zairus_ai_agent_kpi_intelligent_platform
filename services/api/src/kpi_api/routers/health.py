from __future__ import annotations

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from kpi_api import __version__
from kpi_api.schemas.common import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def healthz(request: Request) -> HealthResponse:
    return HealthResponse(
        status="ok", service=request.app.state.settings.service_name, version=__version__
    )


@router.get("/readyz", response_model=ReadyResponse, responses={503: {"description": "not ready"}})
async def readyz(request: Request) -> ReadyResponse | JSONResponse:
    state = request.app.state
    checks: dict[str, str] = {}
    try:
        await state.ping_db()
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"fail: {type(exc).__name__}"
    checks["mcp"] = await _check_mcp(state.settings)
    checks["llm_provider"] = state.settings.llm_provider
    ready = checks["db"] == "ok"
    mcp_ok = checks["mcp"] in ("ok", "inprocess")
    body = ReadyResponse(status="ok" if ready and mcp_ok else "degraded", checks=checks)
    if not ready:
        return JSONResponse(body.model_dump(), status_code=503)
    return body


async def _check_mcp(settings: object) -> str:
    mode = getattr(settings, "mcp_mode", "http")
    if mode == "inprocess":
        return "inprocess"
    url = str(getattr(settings, "mcp_url", "")).rsplit("/mcp", 1)[0] + "/healthz"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
        return "ok" if response.status_code == 200 else f"fail: HTTP {response.status_code}"
    except httpx.HTTPError as exc:
        return f"fail: {type(exc).__name__}"
