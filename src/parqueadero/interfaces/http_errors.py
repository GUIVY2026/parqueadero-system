from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from parqueadero.domain.exceptions import ConflictoDeDominio, ErrorDeDominio, RecursoNoEncontrado


def map_domain_errors(app: FastAPI) -> None:
    @app.exception_handler(RecursoNoEncontrado)
    async def not_found(_request: Request, exc: RecursoNoEncontrado) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictoDeDominio)
    async def conflict(_request: Request, exc: ConflictoDeDominio) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ErrorDeDominio)
    async def unprocessable(_request: Request, exc: ErrorDeDominio) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
