"""Formato argentino para informes e interfaz: coma decimal y fechas dd/mm/aaaa."""

from __future__ import annotations

import math
from datetime import date, datetime


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
