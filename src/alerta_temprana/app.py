"""Punto de entrada: un único servicio con FastAPI (API interna) y Dash (panel).

Arquitectura del documento (Figura 9): el contenedor de la aplicación reúne la
interfaz en Dash, la API en FastAPI, el planificador y el servicio de
predicción. Dash corre sobre Flask (WSGI), por eso se monta dentro de FastAPI
con a2wsgi. Las rutas de la API se registran antes del montaje de Dash.

Ejecutar en desarrollo:  uvicorn alerta_temprana.app:app --reload
"""

from __future__ import annotations

import dash
from a2wsgi import WSGIMiddleware
from dash import html
from fastapi import FastAPI

from alerta_temprana import __version__
from alerta_temprana.db.sesion import base_disponible

app = FastAPI(title="Alerta temprana de abandono", version=__version__)


@app.get("/salud", tags=["sistema"])
def salud() -> dict[str, str]:
    """Control de salud que usa Docker (healthcheck)."""
    return {"estado": "ok", "base_de_datos": "ok" if base_disponible() else "sin conexión"}


# --- Panel en Dash (esqueleto; las pantallas se implementan en el Sprint 1) ---
panel = dash.Dash(__name__, requests_pathname_prefix="/", title="Alerta temprana")
panel.layout = html.Div(
    style={"display": "flex", "minHeight": "100vh", "fontFamily": "system-ui, sans-serif"},
    children=[
        html.Nav(
            style={"width": "260px", "background": "#1f2937", "color": "#fff", "padding": "24px"},
            children=[html.H3("Alerta temprana", style={"margin": 0}), html.Small("Riesgo de abandono")],
        ),
        html.Main(
            style={"flex": 1, "padding": "32px", "background": "#f3f4f6"},
            children=[
                html.H2("Entorno funcionando"),
                html.P("Las pantallas de carga, listado y ficha se implementan en el Sprint 1."),
                html.P(f"Versión {__version__}"),
            ],
        ),
    ],
)

app.mount("/", WSGIMiddleware(panel.server))
