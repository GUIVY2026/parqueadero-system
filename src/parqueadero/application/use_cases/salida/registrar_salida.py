from __future__ import annotations

from parqueadero.application.dtos.salida import RegistrarSalidaCommand
from parqueadero.application.dtos.ticket import TicketDTO, ticket_a_dto
from parqueadero.domain.exceptions import DatosInvalidos, RecursoNoEncontrado
from parqueadero.domain.ports.clock import Clock
from parqueadero.domain.ports.ids import IdGenerator
from parqueadero.domain.ports.outbox import OutboxEvent, OutboxWriter
from parqueadero.domain.ports.tarifas import TarifaRepository
from parqueadero.domain.ports.tickets import TicketRepository
from parqueadero.domain.services.calculadora_cobro import CalculadoraCobro
from parqueadero.domain.value_objects.ids import NodeId, SedeId, TicketId, UsuarioId
from parqueadero.domain.value_objects.placa import Placa


class RegistrarSalida:
    def __init__(
        self,
        *,
        tickets: TicketRepository,
        tarifas: TarifaRepository,
        outbox: OutboxWriter,
        clock: Clock,
        ids: IdGenerator,
        origin_node_id: NodeId,
        calculadora: CalculadoraCobro | None = None,
    ) -> None:
        self._tickets = tickets
        self._tarifas = tarifas
        self._outbox = outbox
        self._clock = clock
        self._ids = ids
        self._origin_node_id = origin_node_id
        self._calculadora = calculadora if calculadora is not None else CalculadoraCobro()

    async def execute(self, command: RegistrarSalidaCommand) -> TicketDTO:
        ticket = await self._buscar_ticket(command)
        tarifa = await self._tarifas.get(ticket.tarifa_id)
        if tarifa is None:
            raise RecursoNoEncontrado("No se encontró la tarifa del ticket")

        ahora = self._clock.now()
        monto = self._calculadora.calcular(tarifa, ticket.hora_entrada, ahora)
        ticket.cerrar(
            hora_salida=ahora,
            monto=monto,
            usuario_salida_id=UsuarioId(command.usuario_id),
            ahora=ahora,
        )
        await self._tickets.save(ticket)
        await self._outbox.append(
            OutboxEvent(
                event_id=self._ids.new(),
                aggregate_type="ticket",
                aggregate_id=str(ticket.id),
                event_type="ticket.cerrado",
                payload={
                    "placa": ticket.placa.valor,
                    "sede_id": str(ticket.sede_id),
                    "monto_centavos": monto.centavos,
                },
                occurred_at=ahora,
                origin_node_id=self._origin_node_id,
            )
        )
        return ticket_a_dto(ticket)

    async def _buscar_ticket(self, command: RegistrarSalidaCommand):
        if command.ticket_id is not None:
            ticket = await self._tickets.get(TicketId(command.ticket_id))
            if ticket is None:
                raise RecursoNoEncontrado("Ticket no encontrado")
            return ticket
        if command.placa is None:
            raise DatosInvalidos("Debe indicar placa o ticket_id para registrar la salida")
        ticket = await self._tickets.get_abierto_por_placa_y_sede(
            Placa(command.placa),
            SedeId(command.sede_id),
        )
        if ticket is None:
            raise RecursoNoEncontrado("No hay ticket abierto para esa placa en la sede")
        return ticket
