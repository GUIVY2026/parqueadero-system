from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from parqueadero.domain.exceptions import DatosInvalidos, TicketYaCerrado
from parqueadero.domain.value_objects.estado_ticket import EstadoTicket
from parqueadero.domain.value_objects.ids import NodeId, SedeId, TarifaId, TicketId, UsuarioId
from parqueadero.domain.value_objects.money import Money
from parqueadero.domain.value_objects.placa import Placa
from parqueadero.domain.value_objects.tiempo import exigir_utc
from parqueadero.domain.value_objects.tipo_vehiculo import TipoVehiculo


@dataclass(slots=True)
class Ticket:
    id: TicketId
    sede_id: SedeId
    placa: Placa
    tipo_vehiculo: TipoVehiculo
    tarifa_id: TarifaId
    hora_entrada: datetime
    hora_salida: datetime | None
    monto: Money | None
    estado: EstadoTicket
    usuario_ingreso_id: UsuarioId
    usuario_salida_id: UsuarioId | None
    version: int
    updated_at: datetime
    origin_node_id: NodeId
    deleted_at: datetime | None = None

    @classmethod
    def abrir(
        cls,
        *,
        ticket_id: TicketId,
        sede_id: SedeId,
        placa: Placa,
        tipo_vehiculo: TipoVehiculo,
        tarifa_id: TarifaId,
        hora_entrada: datetime,
        usuario_ingreso_id: UsuarioId,
        origin_node_id: NodeId,
        ahora: datetime,
    ) -> Ticket:
        entrada = exigir_utc(hora_entrada)
        return cls(
            id=ticket_id,
            sede_id=sede_id,
            placa=placa,
            tipo_vehiculo=tipo_vehiculo,
            tarifa_id=tarifa_id,
            hora_entrada=entrada,
            hora_salida=None,
            monto=None,
            estado=EstadoTicket.ABIERTO,
            usuario_ingreso_id=usuario_ingreso_id,
            usuario_salida_id=None,
            version=1,
            updated_at=exigir_utc(ahora),
            origin_node_id=origin_node_id,
            deleted_at=None,
        )

    @property
    def esta_abierto(self) -> bool:
        return self.estado is EstadoTicket.ABIERTO

    def cerrar(
        self,
        *,
        hora_salida: datetime,
        monto: Money,
        usuario_salida_id: UsuarioId,
        ahora: datetime,
    ) -> None:
        if not self.esta_abierto:
            raise TicketYaCerrado("El ticket ya está cerrado")
        salida = exigir_utc(hora_salida)
        if salida < self.hora_entrada:
            raise DatosInvalidos("La hora de salida no puede ser anterior a la de entrada")
        self.hora_salida = salida
        self.monto = monto
        self.estado = EstadoTicket.CERRADO
        self.usuario_salida_id = usuario_salida_id
        self.version += 1
        self.updated_at = exigir_utc(ahora)
