from kpi_core.context import (
    Principal,
    RequestContext,
    bind_context,
    current_context,
    reset_context,
    system_context,
)
from kpi_core.settings import KpiSettings, get_settings


def test_settings_defaults_and_sync_url(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("KPI_LOG_LEVEL", "debug")
    s = KpiSettings()
    assert s.log_level == "DEBUG" and s.sync_database_url.startswith("postgresql+psycopg://")
    assert not s.is_production
    get_settings.cache_clear()
    assert get_settings() is get_settings()


def test_context_binding() -> None:
    assert current_context() is None
    ctx = system_context("cli")
    assert ctx.caller == "cli" and ctx.principal == Principal() and len(ctx.trace_id) == 16
    token = bind_context(ctx)
    assert current_context() is ctx
    reset_context(token)
    assert current_context() is None
    assert RequestContext(trace_id="t").tenant_id == "default"
