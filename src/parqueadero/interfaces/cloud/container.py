from __future__ import annotations

from dataclasses import dataclass

from parqueadero.domain.ports.clock import Clock
from parqueadero.domain.ports.ids import IdGenerator
from parqueadero.infrastructure.clock import SystemClock
from parqueadero.infrastructure.ids import Uuid7Generator
from parqueadero.interfaces.cloud.settings import CloudSettings


@dataclass(frozen=True, slots=True)
class CloudContainer:
    settings: CloudSettings
    clock: Clock
    ids: IdGenerator


def build_container(settings: CloudSettings | None = None) -> CloudContainer:
    resolved = settings if settings is not None else CloudSettings()
    return CloudContainer(
        settings=resolved,
        clock=SystemClock(),
        ids=Uuid7Generator(),
    )
