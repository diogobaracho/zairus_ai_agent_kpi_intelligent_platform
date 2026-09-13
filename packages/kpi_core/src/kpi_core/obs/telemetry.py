"""Optional OpenTelemetry wiring.

No-op unless OTEL_SDK_DISABLED is false and the `kpi-core[otel]` extras are installed.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def telemetry_enabled() -> bool:
    return os.environ.get("OTEL_SDK_DISABLED", "true").lower() not in ("1", "true", "yes")


def configure_telemetry(
    service_name: str, app: Any | None = None, engine: Any | None = None
) -> bool:
    """Instrument FastAPI/SQLAlchemy/httpx when enabled. Returns True if tracing was configured."""
    if not telemetry_enabled():
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning("OTEL enabled but opentelemetry extras are not installed (kpi-core[otel])")
        return False
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
        except ImportError:
            logger.warning("fastapi instrumentation not installed")
    if engine is not None:
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

            SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
        except ImportError:
            logger.warning("sqlalchemy instrumentation not installed")
    logger.info("telemetry configured", extra={"service": service_name})
    return True
