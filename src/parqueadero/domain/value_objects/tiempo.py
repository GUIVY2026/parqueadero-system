from __future__ import annotations

from datetime import UTC, datetime

from parqueadero.domain.exceptions import DatosInvalidos


def exigir_utc(momento: datetime) -> datetime:
    if momento.tzinfo is None:
        raise DatosInvalidos("La marca de tiempo debe ser timezone-aware (UTC)")
    return momento.astimezone(UTC)
