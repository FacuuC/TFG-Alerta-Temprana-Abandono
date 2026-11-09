"""Rutas internas del listado de alertas (HU-005, tarea 5.1) y de la ficha (HU-006; decisión P4).

Exponen las mismas funciones de servicio/ que usan las pantallas. El listado, sin
parámetros, devuelve todas las alertas, incluidas las de nivel bajo.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from alerta_temprana.db.sesion import obtener_sesion
from alerta_temprana.servicio.alertas import FiltrosAlertas, consultar_alertas, resumir_alertas
from alerta_temprana.servicio.ficha import consultar_ficha

router = APIRouter(prefix="/api/alertas", tags=["alertas"])
SesionDB = Annotated[Session, Depends(obtener_sesion)]


@router.get("")
def listado_de_alertas(
    sesion: SesionDB,
    carrera: Annotated[list[int] | None, Query(description="Código de carrera (repetible)")] = None,
    turno: Annotated[str | None, Query(description="diurno o nocturno")] = None,
    nivel: Annotated[list[str] | None, Query(description="alto, medio o bajo (repetible)")] = None,
    estado: Annotated[
        list[str] | None, Query(description="pendiente, contactado o en_acompanamiento (repetible)")
    ] = None,
) -> dict:
    """Alertas ordenadas por nivel y probabilidad, con los contadores del mismo conjunto."""
    try:
        filtros = FiltrosAlertas(
            carreras=carrera or [], turno=turno, niveles=nivel or [], estados=estado or []
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    alertas = consultar_alertas(sesion, filtros)
    return {"resumen": resumir_alertas(alertas), "alertas": alertas}


@router.get("/{id_alerta}")
def ficha_de_alerta(sesion: SesionDB, id_alerta: int) -> dict:
    """Ficha del estudiante de una alerta (HU-006): predicción vigente y sus cinco factores.

    `factores` es null si la explicación guardada no se puede mostrar (el detalle queda
    en el registro de la aplicación).
    """
    ficha = consultar_ficha(sesion, id_alerta)
    if ficha is None:
        raise HTTPException(status_code=404, detail="No se encontró la alerta.")
    return ficha
