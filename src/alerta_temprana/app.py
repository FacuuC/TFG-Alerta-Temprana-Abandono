"""Punto de entrada: un único servicio con FastAPI (API interna) y Dash (panel).

Arquitectura del documento (Figura 9): el contenedor de la aplicación reúne la
interfaz en Dash, la API en FastAPI, el planificador y el servicio de
predicción. Dash corre sobre Flask (WSGI), por eso se monta dentro de FastAPI
con a2wsgi. Las rutas de la API se registran antes del montaje de Dash.

Al iniciar se crean las tablas que falten y los usuarios de prueba (tarea 1.2).

Ejecutar en desarrollo:  uvicorn alerta_temprana.app:app --reload
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from a2wsgi import WSGIMiddleware
from fastapi import FastAPI

from alerta_temprana import __version__
from alerta_temprana.api.cargas import router as rutas_cargas
from alerta_temprana.db.inicializacion import inicializar_base
from alerta_temprana.db.sesion import base_disponible, obtener_motor
from alerta_temprana.ui.panel import crear_panel

registro = logging.getLogger(__name__)


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI) -> AsyncIterator[None]:
    try:
        inicializar_base(obtener_motor())
    except Exception as error:  # la app arranca igual; /salud informa la base sin conexión
        registro.warning("No se pudo inicializar la base de datos: %s", type(error).__name__)
    yield


app = FastAPI(title="Alerta temprana de abandono", version=__version__, lifespan=ciclo_de_vida)


@app.get("/salud", tags=["sistema"])
def salud() -> dict[str, str]:
    """Control de salud que usa Docker (healthcheck)."""
    return {"estado": "ok", "base_de_datos": "ok" if base_disponible() else "sin conexión"}


app.include_router(rutas_cargas)

panel = crear_panel()
app.mount("/", WSGIMiddleware(panel.server))
