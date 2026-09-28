from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from parqueadero.domain.entities.ticket import Ticket
from parqueadero.domain.value_objects.estado_ticket import EstadoTicket
from parqueadero.domain.value_objects.tipo_vehiculo import TipoVehiculo


class TicketDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    sede_id: str
    placa: str
    tipo_vehiculo: TipoVehiculo
    tarifa_id: str
    hora_entrada: datetime
    hora_salida: datetime | None
    monto_centavos: int | None
    estado: EstadoTicket
    version: int


def ticket_a_dto(ticket: Ticket) -> TicketDTO:
    return TicketDTO(
        id=str(ticket.id),
        sede_id=str(ticket.sede_id),
        placa=ticket.placa.valor,
        tipo_vehiculo=ticket.tipo_vehiculo,
        tarifa_id=str(ticket.tarifa_id),
        hora_entrada=ticket.hora_entrada,
        hora_salida=ticket.hora_salida,
        monto_centavos=ticket.monto.centavos if ticket.monto is not None else None,
        estado=ticket.estado,
        version=ticket.version,
    )
