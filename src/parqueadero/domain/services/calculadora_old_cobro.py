from __future__ import annotations

from datetime import datetime

from parqueadero.domain.entities.tarifa import Tarifa
from parqueadero.domain.exceptions import DatosInvalidos
from parqueadero.domain.value_objects.money import Money
from parqueadero.domain.value_objects.tiempo import exigir_utc

_SEGUNDOS_DIA = 86_400


class CalculadoraCobro:
    """Cobra al menos una fracción y aplica tope diario por cada período de 24 h."""

    def calcular(
        self,
        tarifa: Tarifa,
        hora_entrada: datetime,
        hora_salida: datetime,
    ) -> Money:
        entrada = exigir_utc(hora_entrada)
        salida = exigir_utc(hora_salida)
        if salida < entrada:
            raise DatosInvalidos("La hora de salida no puede ser anterior a la de entrada")

        segundos = int((salida - entrada).total_seconds())
        segundos_fraccion = tarifa.minutos_fraccion * 60
        fracciones = max(1, (segundos + segundos_fraccion - 1) // segundos_fraccion)
        monto = tarifa.precio_fraccion * fracciones

        if tarifa.tope_diario is None:
            return monto

        periodos_dia = max(1, (segundos + _SEGUNDOS_DIA - 1) // _SEGUNDOS_DIA)
        tope = tarifa.tope_diario * periodos_dia
        return monto.min(tope)
