from __future__ import annotations

from datetime import UTC, datetime

from parqueadero.domain.exceptions import DatosInvalidos, ErrorDeDominio, RecursoNoEncontrado
from parqueadero.domain.value_objects.money import Money
from parqueadero.domain.value_objects.placa import Placa


def test_recurso_no_encontrado_es_error_de_dominio() -> None:
    err = RecursoNoEncontrado("ticket")
    assert isinstance(err, ErrorDeDominio)
    assert str(err) == "ticket"


def test_placa_normaliza_mayusculas_y_espacios() -> None:
    assert Placa(" abc-123 ").valor == "ABC123"


def test_placa_invalida() -> None:
    try:
        Placa("**")
    except DatosInvalidos:
        return
    raise AssertionError("se esperaba DatosInvalidos")


def test_money_rechaza_negativos() -> None:
    try:
        Money(-1)
    except DatosInvalidos:
        return
    raise AssertionError("se esperaba DatosInvalidos")


def test_money_operaciones() -> None:
    assert (Money(100) * 3).centavos == 300
    assert (Money(50) + Money(25)).centavos == 75
    assert Money(10).min(Money(3)).centavos == 3
