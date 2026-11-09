"""Rutas internas del listado de alertas (HU-005, tarea 5.1), de la ficha (HU-006) y del
cambio de estado de seguimiento (HU-007, tarea 7.1; decisión P4).

Exponen las mismas funciones de servicio/ que usan las pantallas. El listado, sin
parámetros, devuelve todas las alertas, incluidas las de nivel bajo. Sin inicio de sesión
en el Sprint 1: el usuario de prueba del cambio de estado llega en el cuerpo del pedido y
el servicio controla que sea de Coordinación o Tutor/a (decisión P5).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from alerta_temprana.db.sesion import obtener_sesion
from alerta_temprana.servicio.alertas import FiltrosAlertas, consultar_alertas, resumir_alertas
from alerta_temprana.servicio.ficha import consultar_ficha
from alerta_temprana.servicio.seguimiento import AlertaInexistente, PermisoDenegado, cambiar_estado

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


class PedidoCambioEstado(BaseModel):
    # Se valida en el servicio (422 con los valores posibles), con la misma regla que las pantallas
    estado: str = Field(description="pendiente, contactado o en_acompanamiento")
    usuario: str = Field(description="Usuario de prueba (por ejemplo, tutor01)")


@router.post("/{id_alerta}/estado")
def cambiar_estado_de_alerta(sesion: SesionDB, id_alerta: int, pedido: PedidoCambioEstado) -> dict:
    """Cambia el estado de seguimiento y registra quién y cuándo (HU-007, criterio 2).

    Responde 403 si el usuario no es de Coordinación ni Tutor/a, 404 si la alerta no existe
    y 422 si el estado no es válido. Si el estado ya era ese, `registrado` es false y no se
    guarda nada.
    """
    try:
        resultado = cambiar_estado(sesion, id_alerta, pedido.estado, pedido.usuario)
    except PermisoDenegado as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except AlertaInexistente as error:
        raise HTTPException(status_code=404, detail="No se encontró la alerta.") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return resultado.como_dict()
