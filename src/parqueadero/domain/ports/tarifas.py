from __future__ import annotations

from typing import Protocol

from parqueadero.domain.entities.tarifa import Tarifa
from parqueadero.domain.value_objects.ids import SedeId, TarifaId
from parqueadero.domain.value_objects.tipo_vehiculo import TipoVehiculo


class TarifaRepository(Protocol):
    async def get(self, tarifa_id: TarifaId) -> Tarifa | None: ...

    async def get_vigente(self, sede_id: SedeId, tipo_vehiculo: TipoVehiculo) -> Tarifa | None: ...
