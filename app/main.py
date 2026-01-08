from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.core.telemetry import configure_tracing
from app.core.errors import unhandled_exception_handler
from app.api.routers.health import router as health_router
from app.api.routers.rca import router as rca_router

configure_logging(settings.log_level)
log = get_logger("app")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Enterprise Claude Code RCA API (Starter)",
        version="0.2.0",
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # OpenTelemetry (optional, driven by env)
    configure_tracing(app, service_name=settings.otel_service_name)

    # Routers
    app.include_router(health_router)
    app.include_router(rca_router)

    # Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    return app

app = create_app()
