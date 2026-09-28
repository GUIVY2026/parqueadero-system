from __future__ import annotations

from uuid_utils import uuid7


class Uuid7Generator:
    def new(self) -> str:
        return str(uuid7())
