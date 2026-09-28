from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from parqueadero.domain.value_objects.ids import NodeId, SedeId, VehiculoId
from parqueadero.domain.value_objects.money import Money
from parqueadero.domain.value_objects.placa import Placa
from parqueadero.domain.value_objects.tiempo import exigir_utc
from parqueadero.domain.value_objects.tipo_vehiculo import TipoVehiculo


@dataclass(slots=True)
class Vehiculo:
    id: VehiculoId
    placa: Placa
    tipo: TipoVehiculo
    sede_id: SedeId
    version: int
    updated_at: datetime
    origin_node_id: NodeId
    deleted_at: datetime | None = None

    @classmethod
    def registrar(
        cls,
        *,
        vehiculo_id: VehiculoId,
        placa: Placa,
        tipo: TipoVehiculo,
        sede_id: SedeId,
        ahora: datetime,
        origin_node_id: NodeId,
    ) -> Vehiculo:
        return cls(
            id=vehiculo_id,
            placa=placa,
            tipo=tipo,
            sede_id=sede_id,
            version=1,
            updated_at=exigir_utc(ahora),
            origin_node_id=origin_node_id,
            deleted_at=None,
        )

    def actualizar_tipo(self, tipo: TipoVehiculo, ahora: datetime) -> None:
        if self.tipo == tipo:
            return
        self.tipo = tipo
        self.version += 1
        self.updated_at = exigir_utc(ahora)
