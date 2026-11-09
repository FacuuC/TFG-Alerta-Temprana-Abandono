"""Punto de entrada: un único servicio con FastAPI (API interna) y Dash (panel).

Arquitectura del documento (Figura 9): el contenedor de la aplicación reúne la
interfaz en Dash, la API en FastAPI, el planificador y el servicio de
predicción. Dash corre sobre Flask (WSGI), por eso se monta dentro de FastAPI
con a2wsgi. Las rutas de la API se registran antes del montaje de Dash.

Al iniciar se crean las tablas que falten y los usuarios de prueba (tarea 1.2), se
registran en MODELO los modelos de `modelos/` y se engancha el planificador a cada carga,
para que el riesgo se recalcule solo (HU-003).

Ejecutar en desarrollo:  uvicorn alerta_temprana.app:app --reload
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from a2wsgi import WSGIMiddleware
from fastapi import FastAPI

from alerta_temprana import __version__
from alerta_temprana.api.alertas import router as rutas_alertas
from alerta_temprana.api.cargas import router as rutas_cargas
from alerta_temprana.api.predicciones import router as rutas_predicciones
from alerta_temprana.config import obtener_configuracion
from alerta_temprana.db.inicializacion import inicializar_base
from alerta_temprana.db.sesion import base_disponible, obtener_fabrica_sesiones, obtener_motor
from alerta_temprana.servicio.carga import registrar_al_terminar_carga
from alerta_temprana.servicio.modelos import registrar_modelos
from alerta_temprana.servicio.planificador import obtener_planificador
from alerta_temprana.ui.panel import crear_panel

registro = logging.getLogger(__name__)


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI) -> AsyncIterator[None]:
    try:
        inicializar_base(obtener_motor())
        with obtener_fabrica_sesiones()() as sesion:
            agregados = registrar_modelos(sesion, obtener_configuracion().ruta_modelos)
        if agregados:
            registro.info("Modelos registrados: %s", ", ".join(agregados))
    except Exception as error:  # la app arranca igual; /salud informa la base sin conexión
        registro.warning("No se pudo inicializar la base de datos: %s", type(error).__name__)
    registrar_al_terminar_carga(obtener_planificador().al_terminar_carga)
    yield
    obtener_planificador().cerrar()


app = FastAPI(title="Alerta temprana de abandono", version=__version__, lifespan=ciclo_de_vida)


@app.get("/salud", tags=["sistema"])
def salud() -> dict[str, str]:
    """Control de salud que usa Docker (healthcheck)."""
    return {"estado": "ok", "base_de_datos": "ok" if base_disponible() else "sin conexión"}


app.include_router(rutas_cargas)
app.include_router(rutas_predicciones)
app.include_router(rutas_alertas)

panel = crear_panel()
app.mount("/", WSGIMiddleware(panel.server))
