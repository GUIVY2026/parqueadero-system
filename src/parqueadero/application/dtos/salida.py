from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RegistrarSalidaCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    sede_id: str
    usuario_id: str
    placa: str | None = Field(default=None)
    ticket_id: str | None = Field(default=None)
