"""Elementos comunes de las pantallas (docs/proyecto/06-pantallas.md).

Menú lateral oscuro con «Alerta temprana / Riesgo de abandono», título de la pantalla
arriba a la izquierda y, arriba a la derecha, el selector del usuario de prueba
(decisión P5): en el Sprint 1 no hay inicio de sesión, así que en lugar de «Cerrar
sesión» se elige el usuario que queda registrado en cargas y cambios de estado. El
selector **no es un control de acceso**.
"""

from __future__ import annotations

from dash import dcc, html

from alerta_temprana.db.inicializacion import ROL_AREA_SISTEMAS, USUARIOS_PRUEBA

# Usuarios del selector (06-pantallas.md: Área de Sistemas, Coordinación, Tutor/a)
USUARIOS_SELECTOR: dict[str, str] = {
    "sistemas01": "Área de Sistemas",
    "coordinacion01": "Coordinación",
    "tutor01": "Tutor/a",
}
USUARIO_POR_DEFECTO = "sistemas01"

COLOR_MENU = "#1f2937"
COLOR_FONDO = "#f3f4f6"
COLOR_TARJETA = "#ffffff"
COLOR_BORDE = "#e5e7eb"
COLOR_TEXTO_SECUNDARIO = "#6b7280"
COLOR_ERROR = "#b91c1c"
COLOR_OK = "#047857"

ESTILO_TARJETA = {
    "background": COLOR_TARJETA,
    "border": f"1px solid {COLOR_BORDE}",
    "borderRadius": "8px",
    "padding": "20px 24px",
    "marginBottom": "20px",
}


def es_area_sistemas(nombre_usuario: str | None) -> bool:
    return USUARIOS_PRUEBA.get(nombre_usuario or "") == ROL_AREA_SISTEMAS


def menu_lateral() -> html.Nav:
    return html.Nav(
        style={
            "width": "240px",
            "background": COLOR_MENU,
            "color": "#fff",
            "padding": "24px",
            "flexShrink": 0,
        },
        children=[
            html.H3("Alerta temprana", style={"margin": 0}),
            html.Small("Riesgo de abandono", style={"color": "#d1d5db"}),
            html.Div(id="menu-opciones", style={"marginTop": "32px"}),
        ],
    )


def barra_superior(titulo: str) -> html.Header:
    return html.Header(
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "flexWrap": "wrap",
            "gap": "12px",
            "marginBottom": "24px",
        },
        children=[
            html.Div(
                [
                    html.H2(titulo, style={"margin": 0}),
                    # HU-003, criterio 4 (texto en ui/actualizacion.py)
                    html.Small(id="ultima-actualizacion", style={"color": COLOR_TEXTO_SECUNDARIO}),
                ]
            ),
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "8px"},
                children=[
                    html.Label(
                        "Usuario de prueba:",
                        htmlFor="usuario-prueba",
                        style={"color": COLOR_TEXTO_SECUNDARIO},
                    ),
                    dcc.Dropdown(
                        id="usuario-prueba",
                        options=[
                            {"label": f"{rol} ({nombre})", "value": nombre}
                            for nombre, rol in USUARIOS_SELECTOR.items()
                        ],
                        value=USUARIO_POR_DEFECTO,
                        clearable=False,
                        persistence=True,
                        persistence_type="session",
                        style={"width": "260px"},
                    ),
                ],
            ),
        ],
    )


def pagina(titulo: str, contenido: list) -> html.Div:
    return html.Div(
        style={"display": "flex", "minHeight": "100vh", "fontFamily": "system-ui, sans-serif"},
        children=[
            menu_lateral(),
            html.Main(
                style={"flex": 1, "padding": "32px", "background": COLOR_FONDO, "minWidth": 0},
                children=[barra_superior(titulo), *contenido],
            ),
        ],
    )
