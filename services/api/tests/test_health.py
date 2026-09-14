from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from kpi_api.app import create_app
from kpi_api.settings import ApiSettings


async def test_healthz(client: AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok" and response.json()["service"] == "kpi-api"


async def test_readyz_ok_inprocess(client: AsyncClient) -> None:
    response = await client.get("/readyz")
    assert response.status_code == 200
    body = response.json()
    assert body["checks"] == {"db": "ok", "mcp": "inprocess", "llm_provider": "stub"}


async def test_readyz_db_failure_is_503(repo, settings: ApiSettings) -> None:  # type: ignore[no-untyped-def]
    async def broken() -> None:
        raise ConnectionError("db down")

    from kpi_core.repositories.memory import InMemoryAuditRepository, InMemoryChatRepository

    app: FastAPI = create_app(
        settings,
        repo=repo,
        audit_repo=InMemoryAuditRepository(),
        chat_repo=InMemoryChatRepository(),
        ping_db=broken,
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/readyz")
    assert response.status_code == 503 and response.json()["checks"]["db"].startswith("fail")


async def test_readyz_mcp_http_unreachable_is_degraded(repo, settings: ApiSettings) -> None:  # type: ignore[no-untyped-def]
    from kpi_core.repositories.memory import InMemoryAuditRepository, InMemoryChatRepository

    http_settings = settings.model_copy(
        update={"mcp_mode": "http", "mcp_url": "http://127.0.0.1:1/mcp"}
    )
    app = create_app(
        http_settings,
        repo=repo,
        audit_repo=InMemoryAuditRepository(),
        chat_repo=InMemoryChatRepository(),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded" and response.json()["checks"]["mcp"].startswith(
        "fail"
    )
