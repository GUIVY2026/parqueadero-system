from __future__ import annotations

from datetime import datetime

from parqueadero.domain.exceptions import DatosInvalidos
from parqueadero.domain.value_objects.money import Money
from parqueadero.domain.value_objects.tiempo import exigir_utc


class CalculadoraCobro:
    """
    Servicio de dominio encargado de calcular el valor de un parqueo.

    Reglas:

    - 0 a 3 horas:
        $1.500 por cada hora o fracción.

    - Más de 3 y hasta 12 horas:
        tarifa fija de $6.000.

    - Más de 12 y hasta 24 horas:
        tarifa fija de $12.000.

    - Más de 24 horas:
        se reinicia el ciclo de 24 horas y se calcula cada ciclo
        adicional según las mismas reglas.

    El cálculo se realiza exclusivamente en minutos para evitar
    errores derivados del cambio de día/calendario.
    """

    MINUTOS_POR_HORA: int = 60
    MINUTOS_POR_DIA: int = 24 * MINUTOS_POR_HORA

    LIMITE_TRES_HORAS: int = 3 * MINUTOS_POR_HORA
    LIMITE_DOCE_HORAS: int = 12 * MINUTOS_POR_HORA
    LIMITE_VEINTICUATRO_HORAS: int = MINUTOS_POR_DIA

    TARIFA_POR_HORA_O_FRACCION: Money = Money(150_000)
    TARIFA_HASTA_DOCE_HORAS: Money = Money(600_000)
    TARIFA_HASTA_VEINTICUATRO_HORAS: Money = Money(1_200_000)

    def calcular_monto(
        self,
        hora_entrada: datetime,
        hora_salida: datetime,
    ) -> Money:
        """
        Calcula el monto del parqueadero.

        Args:
            hora_entrada: Fecha y hora de entrada.
            hora_salida: Fecha y hora de salida.

        Returns:
            Money con el valor total a cobrar.

        Raises:
            DatosInvalidos:
                Si las fechas no son UTC o la salida es anterior
                a la entrada.
        """
        entrada = exigir_utc(hora_entrada)
        salida = exigir_utc(hora_salida)

        if salida < entrada:
            raise DatosInvalidos(
                "La hora de salida no puede ser anterior "
                "a la hora de entrada"
            )

        diferencia = salida - entrada
        minutos_totales = (
            diferencia.days * self.MINUTOS_POR_DIA
            + diferencia.seconds // 60
        )

        if minutos_totales <= 0:
            return Money.zero()

        ciclos_completos = minutos_totales // self.MINUTOS_POR_DIA
        minutos_restantes = minutos_totales % self.MINUTOS_POR_DIA

        monto_total = Money.zero()

        if ciclos_completos > 0:
            monto_total = (
                self.TARIFA_HASTA_VEINTICUATRO_HORAS
                * ciclos_completos
            )

        if minutos_restantes > 0:
            monto_total = monto_total + self._calcular_ciclo(
                minutos_restantes
            )

        return monto_total

    def _calcular_ciclo(
        self,
        minutos: int,
    ) -> Money:
        """
        Calcula el valor correspondiente a un período de máximo 24 horas.

        La fracción de hora siempre se redondea hacia arriba.
        """
        if minutos <= self.LIMITE_TRES_HORAS:
            horas_o_fracciones = (
                minutos + self.MINUTOS_POR_HORA - 1
            ) // self.MINUTOS_POR_HORA

            return (
                self.TARIFA_POR_HORA_O_FRACCION
                * horas_o_fracciones
            )

        if minutos <= self.LIMITE_DOCE_HORAS:
            return self.TARIFA_HASTA_DOCE_HORAS

        return self.TARIFA_HASTA_VEINTICUATRO_HORAS