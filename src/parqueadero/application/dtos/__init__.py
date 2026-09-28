"""DTOs de aplicación (Pydantic v2 permitido aquí; no en entidades de dominio)."""

from parqueadero.application.dtos.ingreso import RegistrarIngresoCommand
from parqueadero.application.dtos.salida import RegistrarSalidaCommand
from parqueadero.application.dtos.ticket import TicketDTO, ticket_a_dto

__all__ = [
    "RegistrarIngresoCommand",
    "RegistrarSalidaCommand",
    "TicketDTO",
    "ticket_a_dto",
]
