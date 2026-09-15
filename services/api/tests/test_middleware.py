from httpx import ASGITransport, AsyncClient

from kpi_api.app import create_app
from kpi_api.middleware.rate_limit import TokenBucket
from kpi_api.settings import ApiSettings
from kpi_core.repositories.memory import InMemoryAuditRepository, InMemoryChatRepository


async def test_correlation_header_echoed_and_adopted(client: AsyncClient) -> None:
    response = await client.get("/v1/sectors")
    assert len(response.headers["x-correlation-id"]) == 16
    response = await client.get("/v1/sectors", headers={"X-Correlation-Id": "client-trace-0001"})
    assert response.headers["x-correlation-id"] == "client-trace-0001"
    response = await client.get(
        "/v1/companies/ORBYY", headers={"X-Correlation-Id": "client-trace-0002"}
    )
    assert response.json()["trace_id"] == "client-trace-0002"
    response = await client.get("/v1/sectors", headers={"X-Correlation-Id": "bad id!"})
    assert response.headers["x-correlation-id"] != "bad id!"


def test_token_bucket_refills() -> None:
    bucket = TokenBucket(rate=10.0, burst=2)
    assert bucket.take(now=0.0)[0] and bucket.take(now=0.0)[0]
    allowed, wait = bucket.take(now=0.0)
    assert not allowed and 0 < wait <= 0.1
    assert bucket.take(now=0.2)[0]


async def test_rate_limit_returns_429_problem(repo) -> None:  # type: ignore[no-untyped-def]
    settings = ApiSettings(env="test", rate_limit_rps=1, rate_limit_burst=3, mcp_mode="inprocess")
    app = create_app(
        settings,
        repo=repo,
        audit_repo=InMemoryAuditRepository(),
        chat_repo=InMemoryChatRepository(),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        statuses = [(await client.get("/v1/sectors")).status_code for _ in range(5)]
        limited = await client.get("/v1/sectors")
        health = await client.get("/healthz")
    assert statuses[:3] == [200, 200, 200] and 429 in statuses[3:]
    assert limited.status_code == 429 and limited.headers["retry-after"]
    assert limited.headers["content-type"].startswith("application/problem+json")
    assert limited.json()["code"] == "rate_limited"
    assert health.status_code == 200  # exempt


async def test_body_limit_413(repo) -> None:  # type: ignore[no-untyped-def]
    settings = ApiSettings(
        env="test",
        max_body_bytes=1024,
        rate_limit_rps=1000,
        rate_limit_burst=1000,
        mcp_mode="inprocess",
    )
    app = create_app(
        settings,
        repo=repo,
        audit_repo=InMemoryAuditRepository(),
        chat_repo=InMemoryChatRepository(),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/sectors", content=b"x" * 2048, headers={"content-type": "text/plain"}
        )
    assert response.status_code == 413 and response.json()["code"] == "payload_too_large"


async def test_cors_allows_configured_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/v1/sectors",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_production_rejects_wildcard_cors() -> None:
    import pytest

    with pytest.raises(ValueError):
        ApiSettings(env="production", cors_origins="*")
    assert ApiSettings(cors_origins="http://a,http://b").cors_origins == ["http://a", "http://b"]
