from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from parqueadero.domain.value_objects.tipo_vehiculo import TipoVehiculo


class RegistrarIngresoCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    placa: str
    tipo_vehiculo: TipoVehiculo
    sede_id: str
    usuario_id: str
    tarifa_id: str | None = Field(default=None)
