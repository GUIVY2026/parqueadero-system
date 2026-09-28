from __future__ import annotations

from dataclasses import dataclass

from parqueadero.domain.ports.clock import Clock
from parqueadero.domain.ports.ids import IdGenerator
from parqueadero.infrastructure.clock import SystemClock
from parqueadero.infrastructure.ids import Uuid7Generator
from parqueadero.interfaces.local.settings import LocalSettings


@dataclass(frozen=True, slots=True)
class LocalContainer:
    settings: LocalSettings
    clock: Clock
    ids: IdGenerator


def build_container(settings: LocalSettings | None = None) -> LocalContainer:
    resolved = settings if settings is not None else LocalSettings()
    return LocalContainer(
        settings=resolved,
        clock=SystemClock(),
        ids=Uuid7Generator(),
    )
