from __future__ import annotations

from dataclasses import dataclass

from parqueadero.domain.exceptions import DatosInvalidos


@dataclass(frozen=True, slots=True)
class Money:
    """Monto en centavos enteros. Nunca float."""

    centavos: int

    def __post_init__(self) -> None:
        if self.centavos < 0:
            raise DatosInvalidos("El monto no puede ser negativo")

    @classmethod
    def zero(cls) -> Money:
        return cls(0)

    def __add__(self, other: Money) -> Money:
        return Money(self.centavos + other.centavos)

    def __mul__(self, factor: int) -> Money:
        if factor < 0:
            raise DatosInvalidos("El factor de dinero no puede ser negativo")
        return Money(self.centavos * factor)

    def min(self, other: Money) -> Money:
        return self if self.centavos <= other.centavos else other
