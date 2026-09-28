from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from parqueadero.domain.value_objects.ids import NodeId

OutboxStatus = Literal["pending", "sent", "acked", "failed"]
JsonScalar = str | int | bool | None
JsonObject = dict[str, JsonScalar]


@dataclass(frozen=True, slots=True)
class OutboxEvent:
    event_id: str
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: JsonObject
    occurred_at: datetime
    origin_node_id: NodeId
    status: OutboxStatus = "pending"


class OutboxWriter(Protocol):
    async def append(self, event: OutboxEvent) -> None: ...
