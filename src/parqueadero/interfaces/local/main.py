from __future__ import annotations

from fastapi import FastAPI

from parqueadero.interfaces.http_errors import map_domain_errors
from parqueadero.interfaces.local.api.routers.health import router as health_router
from parqueadero.interfaces.local.container import LocalContainer, build_container


def create_app(container: LocalContainer | None = None) -> FastAPI:
    resolved = container if container is not None else build_container()
    app = FastAPI(
        title="Parqueadero Local",
        description="API de taquilla offline-first (SQLite).",
        version="0.1.0",
    )
    app.state.container = resolved
    map_domain_errors(app)
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
