from __future__ import annotations

import re
from dataclasses import dataclass

from parqueadero.domain.exceptions import DatosInvalidos

_PLACA_RE = re.compile(r"^[A-Z0-9]{5,8}$")


@dataclass(frozen=True, slots=True)
class Placa:
    """Placa normalizada: mayúsculas, sin espacios ni guiones."""

    valor: str

    def __post_init__(self) -> None:
        normalizada = self.valor.upper().replace(" ", "").replace("-", "")
        if not _PLACA_RE.fullmatch(normalizada):
            raise DatosInvalidos("Placa inválida: use 5 a 8 caracteres alfanuméricos")
        object.__setattr__(self, "valor", normalizada)

    def __str__(self) -> str:
        return self.valor
