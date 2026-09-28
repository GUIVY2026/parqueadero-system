from __future__ import annotations

from datetime import datetime

from parqueadero.application.dtos.ingreso import RegistrarIngresoCommand
from parqueadero.application.dtos.ticket import TicketDTO, ticket_a_dto
from parqueadero.domain.entities.tarifa import Tarifa
from parqueadero.domain.entities.ticket import Ticket
from parqueadero.domain.entities.vehiculo import Vehiculo
from parqueadero.domain.exceptions import RecursoNoEncontrado, VehiculoYaEnPatio
from parqueadero.domain.ports.clock import Clock
from parqueadero.domain.ports.ids import IdGenerator
from parqueadero.domain.ports.outbox import OutboxEvent, OutboxWriter
from parqueadero.domain.ports.tarifas import TarifaRepository
from parqueadero.domain.ports.tickets import TicketRepository
from parqueadero.domain.ports.vehiculos import VehiculoRepository
from parqueadero.domain.value_objects.ids import (
    NodeId,
    SedeId,
    TarifaId,
    TicketId,
    UsuarioId,
    VehiculoId,
)
from parqueadero.domain.value_objects.placa import Placa


class RegistrarIngreso:
    def __init__(
        self,
        *,
        tickets: TicketRepository,
        vehiculos: VehiculoRepository,
        tarifas: TarifaRepository,
        outbox: OutboxWriter,
        clock: Clock,
        ids: IdGenerator,
        origin_node_id: NodeId,
    ) -> None:
        self._tickets = tickets
        self._vehiculos = vehiculos
        self._tarifas = tarifas
        self._outbox = outbox
        self._clock = clock
        self._ids = ids
        self._origin_node_id = origin_node_id

    async def execute(self, command: RegistrarIngresoCommand) -> TicketDTO:
        placa = Placa(command.placa)
        sede_id = SedeId(command.sede_id)
        abierto = await self._tickets.get_abierto_por_placa_y_sede(placa, sede_id)
        if abierto is not None:
            raise VehiculoYaEnPatio("Ya hay un vehículo activo con esa placa en la sede")

        tarifa = await self._resolver_tarifa(command, sede_id)
        ahora = self._clock.now()
        vehiculo = await self._asegurar_vehiculo(placa, command, sede_id, ahora)
        ticket = Ticket.abrir(
            ticket_id=TicketId(self._ids.new()),
            sede_id=sede_id,
            placa=placa,
            tipo_vehiculo=command.tipo_vehiculo,
            tarifa_id=tarifa.id,
            hora_entrada=ahora,
            usuario_ingreso_id=UsuarioId(command.usuario_id),
            origin_node_id=self._origin_node_id,
            ahora=ahora,
        )
        await self._vehiculos.save(vehiculo)
        await self._tickets.save(ticket)
        await self._outbox.append(
            OutboxEvent(
                event_id=self._ids.new(),
                aggregate_type="ticket",
                aggregate_id=str(ticket.id),
                event_type="ticket.abierto",
                payload={
                    "placa": placa.valor,
                    "sede_id": str(sede_id),
                    "tipo_vehiculo": str(command.tipo_vehiculo),
                    "tarifa_id": str(tarifa.id),
                },
                occurred_at=ahora,
                origin_node_id=self._origin_node_id,
            )
        )
        return ticket_a_dto(ticket)

    async def _resolver_tarifa(self, command: RegistrarIngresoCommand, sede_id: SedeId) -> Tarifa:
        if command.tarifa_id is not None:
            tarifa = await self._tarifas.get(TarifaId(command.tarifa_id))
        else:
            tarifa = await self._tarifas.get_vigente(sede_id, command.tipo_vehiculo)
        if tarifa is None:
            raise RecursoNoEncontrado("No hay tarifa vigente para el tipo de vehículo")
        return tarifa

    async def _asegurar_vehiculo(
        self,
        placa: Placa,
        command: RegistrarIngresoCommand,
        sede_id: SedeId,
        ahora: datetime,
    ) -> Vehiculo:
        existente = await self._vehiculos.get_por_placa_y_sede(placa, sede_id)
        if existente is None:
            return Vehiculo.registrar(
                vehiculo_id=VehiculoId(self._ids.new()),
                placa=placa,
                tipo=command.tipo_vehiculo,
                sede_id=sede_id,
                ahora=ahora,
                origin_node_id=self._origin_node_id,
            )
        existente.actualizar_tipo(command.tipo_vehiculo, ahora)
        return existente
