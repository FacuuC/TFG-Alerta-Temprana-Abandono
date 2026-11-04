"""Formato argentino para informes e interfaz: coma decimal y fechas dd/mm/aaaa."""

from __future__ import annotations

import math
from datetime import date, datetime
from zoneinfo import ZoneInfo

ZONA_ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")


def hora_argentina(valor: datetime | str) -> datetime:
    """Pasa una fecha con zona horaria (o su texto ISO) a la hora argentina.

    Los metadatos guardan las fechas en UTC («2026-11-04T00:01:28+00:00» es el 03/11 a
    las 21:01 en Argentina). Una fecha sin zona se toma como ya expresada en hora argentina.
    """
    if isinstance(valor, str):
        valor = datetime.fromisoformat(valor)
    if valor.tzinfo is None:
        return valor
    return valor.astimezone(ZONA_ARGENTINA)


def decimal(valor: float, decimales: int = 4) -> str:
    """0.8878 -> «0,8878». Un valor no definido (NaN) se muestra como «—»."""
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    return f"{valor:.{decimales}f}".replace(".", ",")


def porcentaje(proporcion: float, decimales: int = 1) -> str:
    """0.149 -> «14,9 %»."""
    if proporcion is None or (isinstance(proporcion, float) and math.isnan(proporcion)):
        return "—"
    return f"{proporcion * 100:.{decimales}f} %".replace(".", ",")


def entero(valor: int) -> str:
    """2654 -> «2.654» (punto como separador de miles)."""
    return f"{int(valor):,}".replace(",", ".")


def fecha(valor: date | datetime) -> str:
    return valor.strftime("%d/%m/%Y")


def fecha_hora(valor: datetime) -> str:
    return valor.strftime("%d/%m/%Y %H:%M")
