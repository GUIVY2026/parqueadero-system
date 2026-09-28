from __future__ import annotations

from typing import Protocol

from parqueadero.domain.entities.vehiculo import Vehiculo
from parqueadero.domain.value_objects.ids import SedeId
from parqueadero.domain.value_objects.placa import Placa


class VehiculoRepository(Protocol):
    async def get_por_placa_y_sede(self, placa: Placa, sede_id: SedeId) -> Vehiculo | None: ...

    async def save(self, vehiculo: Vehiculo) -> None: ...
