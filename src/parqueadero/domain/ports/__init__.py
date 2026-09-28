"""Puertos (Protocol) que el dominio y la aplicación exigen a infraestructura."""

from parqueadero.domain.ports.clock import Clock
from parqueadero.domain.ports.ids import IdGenerator
from parqueadero.domain.ports.outbox import OutboxEvent, OutboxWriter
from parqueadero.domain.ports.tarifas import TarifaRepository
from parqueadero.domain.ports.tickets import TicketRepository
from parqueadero.domain.ports.vehiculos import VehiculoRepository

__all__ = [
    "Clock",
    "IdGenerator",
    "OutboxEvent",
    "OutboxWriter",
    "TarifaRepository",
    "TicketRepository",
    "VehiculoRepository",
]
