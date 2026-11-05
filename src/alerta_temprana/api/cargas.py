"""Rutas internas de carga de datos (HU-001; decisión P4).

Exponen las mismas funciones de servicio/carga.py que usa la pantalla de Dash. Sin
inicio de sesión en el Sprint 1: el usuario de prueba llega como campo del formulario
y el servicio controla que sea del Área de Sistemas (decisión P5).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from alerta_temprana.datos.validacion import CargaRechazada
from alerta_temprana.datos.variables import Momento
from alerta_temprana.db.sesion import obtener_sesion
from alerta_temprana.servicio.carga import PermisoDenegado, listar_cargas, registrar_carga

router = APIRouter(prefix="/api/cargas", tags=["cargas"])
SesionDB = Annotated[Session, Depends(obtener_sesion)]


@router.post("")
def cargar_archivo(
    sesion: SesionDB,
    archivo: Annotated[UploadFile, File(description="CSV separado por «;», UTF-8, punto decimal")],
    momento: Annotated[Momento, Form(description="inscripcion, cierre_1s o cierre_2s")],
    usuario: Annotated[str, Form(description="Usuario de prueba (por ejemplo, sistemas01)")],
) -> dict:
    """Valida, seudonimiza y guarda la carga. Responde 422 si se rechaza completa (con
    las columnas con problemas) y 403 si el usuario no es del Área de Sistemas."""
    try:
        contenido = archivo.file.read()
    finally:
        archivo.file.close()  # el archivo original no se conserva
    try:
        resultado = registrar_carga(sesion, contenido, momento, usuario)
    except PermisoDenegado as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except CargaRechazada as error:
        raise HTTPException(
            status_code=422,
            detail={
                "mensaje": error.mensaje,
                "columnas": error.columnas,
                "problemas": [{"columna": p.columna, "motivo": p.motivo} for p in error.problemas],
            },
        ) from error
    return resultado.como_dict()


@router.get("")
def cargas_anteriores(sesion: SesionDB, limite: int = 20) -> list[dict]:
    return [c | {"fecha": c["fecha"].isoformat()} for c in listar_cargas(sesion, limite)]
