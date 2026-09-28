from __future__ import annotations

from typing import Protocol

from parqueadero.domain.entities.ticket import Ticket
from parqueadero.domain.value_objects.ids import SedeId, TicketId
from parqueadero.domain.value_objects.placa import Placa


class TicketRepository(Protocol):
    async def get(self, ticket_id: TicketId) -> Ticket | None: ...

    async def get_abierto_por_placa_y_sede(self, placa: Placa, sede_id: SedeId) -> Ticket | None: ...

    async def save(self, ticket: Ticket) -> None: ...
