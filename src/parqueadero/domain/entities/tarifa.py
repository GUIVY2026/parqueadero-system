from __future__ import annotations

from dataclasses import dataclass

from parqueadero.domain.exceptions import DatosInvalidos
from parqueadero.domain.value_objects.ids import SedeId, TarifaId
from parqueadero.domain.value_objects.money import Money
from parqueadero.domain.value_objects.tipo_vehiculo import TipoVehiculo


@dataclass(frozen=True, slots=True)
class Tarifa:
    """Catálogo de cobro por tipo de vehículo. El cálculo vive en el dominio."""

    id: TarifaId
    sede_id: SedeId
    tipo_vehiculo: TipoVehiculo
    precio_fraccion: Money
    minutos_fraccion: int
    tope_diario: Money | None = None

    def __post_init__(self) -> None:
        if self.minutos_fraccion <= 0:
            raise DatosInvalidos("Los minutos de fracción deben ser mayores que cero")
