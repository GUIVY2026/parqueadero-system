from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Final

import httpx
from sqlalchemy import DateTime, Integer, String, Text, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


logger = logging.getLogger(__name__)


# ============================================================================
# Configuración
# ============================================================================

_DEFAULT_BATCH_SIZE: Final[int] = 50
_DEFAULT_MAX_RETRIES: Final[int] = 5
_DEFAULT_INITIAL_BACKOFF: Final[float] = 1.0
_DEFAULT_MAX_BACKOFF: Final[float] = 30.0


@dataclass(frozen=True, slots=True)
class PublisherConfig:
    """
    Configuración del publicador de outbox.

    La URL apunta al endpoint de la API que recibe eventos de sincronización.
    """

    api_url: str

    batch_size: int = _DEFAULT_BATCH_SIZE
    max_retries: int = _DEFAULT_MAX_RETRIES
    initial_backoff: float = _DEFAULT_INITIAL_BACKOFF
    max_backoff: float = _DEFAULT_MAX_BACKOFF
    request_timeout: float = 15.0

    def __post_init__(self) -> None:
        if self.batch_size <= 0:
            raise ValueError("batch_size debe ser mayor que cero")

        if self.max_retries < 0:
            raise ValueError("max_retries no puede ser negativo")

        if self.initial_backoff <= 0:
            raise ValueError("initial_backoff debe ser mayor que cero")

        if self.max_backoff <= 0:
            raise ValueError("max_backoff debe ser mayor que cero")

        if self.request_timeout <= 0:
            raise ValueError("request_timeout debe ser mayor que cero")


# ============================================================================
# Modelo ORM de la Outbox
# ============================================================================


class Base(DeclarativeBase):
    """Base declarativa de la infraestructura de sincronización."""


class OutboxModel(Base):
    """
    Registro local de un evento pendiente de publicar.

    Se asume una tabla con la siguiente semántica:

        id              -> identificador único del evento
        event_type      -> tipo/nombre del evento
        payload         -> JSON serializado
        created_at      -> fecha de creación local
        processed_at    -> fecha de confirmación de publicación
        attempts        -> número de intentos realizados
        last_error      -> último error de publicación

    `processed_at IS NULL` significa que el evento sigue pendiente.
    """

    __tablename__ = "outbox"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )

    payload: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


# ============================================================================
# DTO interno
# ============================================================================


@dataclass(frozen=True, slots=True)
class OutboxEvent:
    """
    Representación inmutable de un evento que será enviado a la API.

    Este DTO evita exponer objetos ORM fuera de la infraestructura.
    """

    id: str
    event_type: str
    payload: dict[str, Any]
    created_at: datetime
    attempts: int


# ============================================================================
# Publisher
# ============================================================================


class OutboxPublisher:
    """
    Publicador asíncrono de eventos locales hacia la API en la nube.

    Responsabilidades:

    - leer eventos pendientes de SQLite;
    - publicarlos mediante HTTP;
    - aplicar reintentos con backoff exponencial;
    - marcar como procesados únicamente los eventos confirmados por la API.

    No contiene reglas de negocio ni conoce entidades del dominio.
    Su única responsabilidad es transportar eventos de infraestructura.

    Importante:

    La API debe tratar `X-Idempotency-Key` como identificador único del evento.
    Esto evita duplicados cuando:

        1. SQLite envía el evento;
        2. la API lo procesa;
        3. la respuesta se pierde por un fallo de red;
        4. el publisher vuelve a intentarlo.

    En ese escenario el evento puede ser enviado físicamente más de una vez,
    pero la API debe procesarlo de forma idempotente.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        config: PublisherConfig,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._config = config
        self._http_client = http_client

    async def publish_pending(self) -> int:
        """
        Publica un lote de eventos pendientes.

        Returns:
            Número de eventos confirmados por la API.
        """
        events = await self._load_pending_events()

        if not events:
            return 0

        published = 0

        owns_client = self._http_client is None

        client: httpx.AsyncClient

        if owns_client:
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    self._config.request_timeout,
                ),
            )
        else:
            client = self._http_client

        try:
            for event in events:
                success = await self._publish_with_retry(
                    client,
                    event,
                )

                if success:
                    await self._mark_as_processed(event.id)
                    published += 1

        finally:
            if owns_client:
                await client.aclose()

        return published

    async def run_forever(
        self,
        *,
        interval: float = 2.0,
        stop_event: asyncio.Event | None = None,
    ) -> None:
        """
        Ejecuta continuamente el publicador.

        El loop termina cuando `stop_event` se establece.

        Ejemplo:

            stop_event = asyncio.Event()

            await publisher.run_forever(
                interval=2.0,
                stop_event=stop_event,
            )
        """
        if interval <= 0:
            raise ValueError("interval debe ser mayor que cero")

        while stop_event is None or not stop_event.is_set():
            try:
                published = await self.publish_pending()

                if published:
                    logger.info(
                        "Outbox: %d evento(s) publicado(s)",
                        published,
                    )

            except asyncio.CancelledError:
                raise

            except Exception:
                logger.exception(
                    "Error inesperado ejecutando el publisher de outbox"
                )

            if stop_event is None:
                await asyncio.sleep(interval)
                continue

            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=interval,
                )
            except asyncio.TimeoutError:
                pass

    # ------------------------------------------------------------------------
    # Lectura de eventos
    # ------------------------------------------------------------------------

    async def _load_pending_events(self) -> list[OutboxEvent]:
        """
        Obtiene los eventos pendientes ordenados FIFO.

        No se mantiene una sesión abierta durante la comunicación HTTP.
        Esto es importante para no mantener una transacción SQLite abierta
        mientras esperamos a una API remota.
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(OutboxModel)
                .where(
                    OutboxModel.processed_at.is_(None),
                )
                .order_by(
                    OutboxModel.created_at.asc(),
                    OutboxModel.id.asc(),
                )
                .limit(self._config.batch_size)
            )

            models = result.scalars().all()

            events: list[OutboxEvent] = []

            for model in models:
                try:
                    payload = json.loads(model.payload)
                except json.JSONDecodeError as exc:
                    await self._mark_as_failed(
                        model.id,
                        f"Payload JSON inválido: {exc}",
                    )
                    continue

                if not isinstance(payload, dict):
                    await self._mark_as_failed(
                        model.id,
                        "El payload del evento debe ser un objeto JSON",
                    )
                    continue

                events.append(
                    OutboxEvent(
                        id=model.id,
                        event_type=model.event_type,
                        payload=payload,
                        created_at=model.created_at,
                        attempts=model.attempts,
                    )
                )

            return events

    # ------------------------------------------------------------------------
    # Publicación
    # ------------------------------------------------------------------------

    async def _publish_with_retry(
        self,
        client: httpx.AsyncClient,
        event: OutboxEvent,
    ) -> bool:
        """
        Publica un evento aplicando backoff exponencial.

        Los errores de transporte y las respuestas HTTP 5xx son reintentables.

        Las respuestas HTTP 4xx no se reintentan automáticamente porque
        normalmente representan un problema con el evento o con la petición.
        """

        for attempt in range(
            self._config.max_retries + 1,
        ):
            await self._increment_attempt(event.id)

            try:
                response = await client.post(
                    self._config.api_url,
                    json={
                        "event_id": event.id,
                        "event_type": event.event_type,
                        "payload": event.payload,
                        "created_at": event.created_at.isoformat(),
                    },
                    headers={
                        # Fundamental para garantizar idempotencia en la API.
                        "X-Idempotency-Key": event.id,
                        "X-Event-Type": event.event_type,
                    },
                )

                if 200 <= response.status_code < 300:
                    logger.debug(
                        "Evento %s confirmado por la API",
                        event.id,
                    )
                    return True

                if 400 <= response.status_code < 500:
                    error = (
                        f"HTTP {response.status_code}: "
                        f"{response.text[:1000]}"
                    )

                    await self._mark_as_failed(
                        event.id,
                        error,
                    )

                    logger.error(
                        "Evento %s rechazado por la API: %s",
                        event.id,
                        error,
                    )

                    return False

                error = (
                    f"HTTP {response.status_code}: "
                    f"{response.text[:1000]}"
                )

                await self._record_error(
                    event.id,
                    error,
                )

                if attempt >= self._config.max_retries:
                    logger.error(
                        "Evento %s agotó sus reintentos: %s",
                        event.id,
                        error,
                    )
                    return False

                await self._sleep_before_retry(attempt)

            except (
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
                httpx.NetworkError,
            ) as exc:
                error = f"{type(exc).__name__}: {exc}"

                await self._record_error(
                    event.id,
                    error,
                )

                if attempt >= self._config.max_retries:
                    logger.error(
                        "Evento %s agotó sus reintentos por error de red: %s",
                        event.id,
                        error,
                    )
                    return False

                logger.warning(
                    "Fallo de red publicando evento %s. "
                    "Reintento %d/%d",
                    event.id,
                    attempt + 1,
                    self._config.max_retries,
                )

                await self._sleep_before_retry(attempt)

            except httpx.HTTPError as exc:
                error = f"{type(exc).__name__}: {exc}"

                await self._record_error(
                    event.id,
                    error,
                )

                if attempt >= self._config.max_retries:
                    logger.error(
                        "Evento %s agotó sus reintentos: %s",
                        event.id,
                        error,
                    )
                    return False

                await self._sleep_before_retry(attempt)

        return False

    async def _sleep_before_retry(
        self,
        attempt: int,
    ) -> None:
        """
        Backoff exponencial:

            intento 0 -> 1s
            intento 1 -> 2s
            intento 2 -> 4s
            intento 3 -> 8s
            ...

        Limitado por max_backoff.
        """
        delay = min(
            self._config.initial_backoff * (2**attempt),
            self._config.max_backoff,
        )

        await asyncio.sleep(delay)

    # ------------------------------------------------------------------------
    # Estado de la Outbox
    # ------------------------------------------------------------------------

    async def _increment_attempt(
        self,
        event_id: str,
    ) -> None:
        """
        Incrementa el contador de intentos.

        Se ejecuta en una transacción independiente para que el intento
        quede registrado incluso si posteriormente falla la petición HTTP.
        """
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(OutboxModel)
                    .where(
                        OutboxModel.id == event_id,
                        OutboxModel.processed_at.is_(None),
                    )
                    .values(
                        attempts=OutboxModel.attempts + 1,
                    )
                )

    async def _record_error(
        self,
        event_id: str,
        error: str,
    ) -> None:
        """
        Guarda el último error sin marcar el evento como procesado.
        """
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(OutboxModel)
                    .where(
                        OutboxModel.id == event_id,
                        OutboxModel.processed_at.is_(None),
                    )
                    .values(
                        last_error=error[:4000],
                    )
                )

    async def _mark_as_failed(
        self,
        event_id: str,
        error: str,
    ) -> None:
        """
        Registra un error permanente de publicación.

        El evento continúa pendiente porque `processed_at` permanece NULL.
        Esto permite inspeccionarlo y reprocesarlo posteriormente.
        """
        await self._record_error(
            event_id,
            error,
        )

    async def _mark_as_processed(
        self,
        event_id: str,
    ) -> None:
        """
        Marca un evento como procesado únicamente después de recibir
        confirmación HTTP 2xx de la API.
        """
        processed_at = datetime.now(timezone.utc)

        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(OutboxModel)
                    .where(
                        OutboxModel.id == event_id,
                        OutboxModel.processed_at.is_(None),
                    )
                    .values(
                        processed_at=processed_at,
                        last_error=None,
                    )
                )