from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from parqueadero.domain.entities.ticket import Ticket
from parqueadero.domain.entities.vehiculo import Vehiculo
from parqueadero.domain.ports.tickets import TicketRepository
from parqueadero.domain.ports.vehiculos import VehiculoRepository
from parqueadero.domain.value_objects.estado_ticket import EstadoTicket
from parqueadero.domain.value_objects.ids import (
    NodeId,
    SedeId,
    TarifaId,
    TicketId,
    UsuarioId,
    VehiculoId,
)
from parqueadero.domain.value_objects.money import Money
from parqueadero.domain.value_objects.placa import Placa
from parqueadero.domain.value_objects.tipo_vehiculo import TipoVehiculo


class Base(DeclarativeBase):
    """Base declarativa para la persistencia PostgreSQL."""


class TicketModel(Base):
    """Modelo ORM para la entidad Ticket."""

    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    sede_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    placa: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        index=True,
    )

    tipo_vehiculo: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    tarifa_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    hora_entrada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    hora_salida: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Money se almacena como cantidad entera de centavos.
    monto: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    estado: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    usuario_ingreso_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    usuario_salida_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    origin_node_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class VehiculoModel(Base):
    """Modelo ORM para la entidad Vehiculo."""

    __tablename__ = "vehiculos"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    placa: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        index=True,
    )

    tipo: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    sede_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    origin_node_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class PostgreSQLRepository(TicketRepository, VehiculoRepository):
    """
    Implementación de TicketRepository y VehiculoRepository
    sobre PostgreSQL.

    Este repositorio no resuelve conflictos de sincronización.
    El Sincronizador será responsable de interpretar version,
    updated_at y origin_node_id.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    # ================================================================
    # TicketRepository
    # ================================================================

    async def get(
        self,
        ticket_id: TicketId,
    ) -> Ticket | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(TicketModel).where(
                    TicketModel.id == str(ticket_id),
                )
            )

            model = result.scalar_one_or_none()

            if model is None:
                return None

            return self._ticket_from_model(model)

    async def get_abierto_por_placa_y_sede(
        self,
        placa: Placa,
        sede_id: SedeId,
    ) -> Ticket | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(TicketModel)
                .where(
                    TicketModel.placa == placa.valor,
                    TicketModel.sede_id == str(sede_id),
                    TicketModel.estado == EstadoTicket.ABIERTO.value,
                    TicketModel.deleted_at.is_(None),
                )
                .order_by(
                    TicketModel.hora_entrada.desc(),
                )
                .limit(1)
            )

            model = result.scalar_one_or_none()

            if model is None:
                return None

            return self._ticket_from_model(model)

    async def save(
        self,
        ticket: Ticket,
    ) -> None:
        values: dict[str, Any] = {
            "id": str(ticket.id),
            "sede_id": str(ticket.sede_id),
            "placa": ticket.placa.valor,
            "tipo_vehiculo": ticket.tipo_vehiculo.value,
            "tarifa_id": str(ticket.tarifa_id),
            "hora_entrada": ticket.hora_entrada,
            "hora_salida": ticket.hora_salida,
            "monto": (
                ticket.monto.centavos
                if ticket.monto is not None
                else None
            ),
            "estado": ticket.estado.value,
            "usuario_ingreso_id": str(ticket.usuario_ingreso_id),
            "usuario_salida_id": (
                str(ticket.usuario_salida_id)
                if ticket.usuario_salida_id is not None
                else None
            ),
            "version": ticket.version,
            "updated_at": ticket.updated_at,
            "origin_node_id": str(ticket.origin_node_id),
            "deleted_at": ticket.deleted_at,
        }

        async with self._session_factory() as session:
            async with session.begin():
                stmt = insert(TicketModel).values(**values)

                stmt = stmt.on_conflict_do_update(
                    index_elements=[TicketModel.id],
                    set_=values,
                )

                await session.execute(stmt)

    # ================================================================
    # VehiculoRepository
    # ================================================================

    async def get_por_placa_y_sede(
        self,
        placa: Placa,
        sede_id: SedeId,
    ) -> Vehiculo | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(VehiculoModel).where(
                    VehiculoModel.placa == placa.valor,
                    VehiculoModel.sede_id == str(sede_id),
                    VehiculoModel.deleted_at.is_(None),
                )
            )

            model = result.scalar_one_or_none()

            if model is None:
                return None

            return self._vehiculo_from_model(model)

    async def save(
        self,
        vehiculo: Vehiculo,
    ) -> None:
        values: dict[str, Any] = {
            "id": str(vehiculo.id),
            "placa": vehiculo.placa.valor,
            "tipo": vehiculo.tipo.value,
            "sede_id": str(vehiculo.sede_id),
            "version": vehiculo.version,
            "updated_at": vehiculo.updated_at,
            "origin_node_id": str(vehiculo.origin_node_id),
            "deleted_at": vehiculo.deleted_at,
        }

        async with self._session_factory() as session:
            async with session.begin():
                stmt = insert(VehiculoModel).values(**values)

                stmt = stmt.on_conflict_do_update(
                    index_elements=[VehiculoModel.id],
                    set_=values,
                )

                await session.execute(stmt)

    # ================================================================
    # Mappers: ORM -> Dominio
    # ================================================================

    @staticmethod
    def _ticket_from_model(
        model: TicketModel,
    ) -> Ticket:
        return Ticket(
            id=TicketId(model.id),
            sede_id=SedeId(model.sede_id),
            placa=Placa(model.placa),
            tipo_vehiculo=TipoVehiculo(model.tipo_vehiculo),
            tarifa_id=TarifaId(model.tarifa_id),
            hora_entrada=model.hora_entrada,
            hora_salida=model.hora_salida,
            monto=(
                Money(model.monto)
                if model.monto is not None
                else None
            ),
            estado=EstadoTicket(model.estado),
            usuario_ingreso_id=UsuarioId(
                model.usuario_ingreso_id,
            ),
            usuario_salida_id=(
                UsuarioId(model.usuario_salida_id)
                if model.usuario_salida_id is not None
                else None
            ),
            version=model.version,
            updated_at=model.updated_at,
            origin_node_id=NodeId(model.origin_node_id),
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _vehiculo_from_model(
        model: VehiculoModel,
    ) -> Vehiculo:
        return Vehiculo(
            id=VehiculoId(model.id),
            placa=Placa(model.placa),
            tipo=TipoVehiculo(model.tipo),
            sede_id=SedeId(model.sede_id),
            version=model.version,
            updated_at=model.updated_at,
            origin_node_id=NodeId(model.origin_node_id),
            deleted_at=model.deleted_at,
        )


async def create_postgresql_schema(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """
    Crea las tablas PostgreSQL.

    En producción se recomienda utilizar Alembic para las migraciones.
    """
    bind = session_factory.kw.get("bind")

    if bind is None:
        raise RuntimeError(
            "El session_factory no tiene un AsyncEngine asociado."
        )

    async with bind.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all,
        )