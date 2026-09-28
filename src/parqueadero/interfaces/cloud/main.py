from __future__ import annotations

from fastapi import FastAPI

from parqueadero.interfaces.cloud.api.routers.health import router as health_router
from parqueadero.interfaces.cloud.container import CloudContainer, build_container
from parqueadero.interfaces.http_errors import map_domain_errors


def create_app(container: CloudContainer | None = None) -> FastAPI:
    resolved = container if container is not None else build_container()
    app = FastAPI(
        title="Parqueadero Cloud",
        description="API corporativa y de sincronización (PostgreSQL).",
        version="0.1.0",
    )
    app.state.container = resolved
    map_domain_errors(app)
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
