"""Rutas internas del cálculo del riesgo (HU-003; decisión P4).

Exponen las mismas funciones de servicio/ que usa el panel de Dash.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from alerta_temprana.db.sesion import obtener_sesion
from alerta_temprana.db.tablas import Carga
from alerta_temprana.servicio.planificador import Planificador, obtener_planificador
from alerta_temprana.servicio.prediccion import ultima_actualizacion

router = APIRouter(prefix="/api", tags=["predicciones"])
SesionDB = Annotated[Session, Depends(obtener_sesion)]
PlanificadorApp = Annotated[Planificador, Depends(obtener_planificador)]


@router.get("/cargas/{id_carga}/recalculo")
def estado_del_recalculo(id_carga: int, sesion: SesionDB, planificador: PlanificadorApp) -> dict:
    """Estado del cálculo del riesgo de una carga: en_curso, completado, sin_modelo o error."""
    if sesion.get(Carga, id_carga) is None:
        raise HTTPException(status_code=404, detail=f"No existe la carga {id_carga}.")
    estado = planificador.estado(id_carga)
    if estado is None:
        return {
            "id_carga": id_carga,
            "estado": "sin_informacion",
            "mensaje": "No hay estimaciones guardadas de esta carga.",
            "resumen": None,
        }
    return estado.como_dict()


@router.get("/predicciones/ultima-actualizacion")
def ultima_actualizacion_del_riesgo(sesion: SesionDB) -> dict:
    """Fecha del último cálculo y versión y momento del modelo usado (HU-003, criterio 4)."""
    ultima = ultima_actualizacion(sesion)
    if ultima is None:
        return {"fecha": None, "version": None, "momento": None}
    return ultima | {"fecha": ultima["fecha"].isoformat()}
