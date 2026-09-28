from __future__ import annotations

from typing import Protocol


class IdGenerator(Protocol):
    def new(self) -> str:
        """Identificador de nodo (UUIDv7 / ULID), nunca un serial autoincrement."""
        ...
