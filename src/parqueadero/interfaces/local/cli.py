from __future__ import annotations

import uvicorn

from parqueadero.interfaces.local.container import build_container
from parqueadero.interfaces.local.main import create_app


def main() -> None:
    container = build_container()
    uvicorn.run(
        create_app(container),
        host=container.settings.host,
        port=container.settings.port,
    )
