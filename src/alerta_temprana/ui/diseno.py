"""Elementos comunes de las pantallas (docs/proyecto/06-pantallas.md).

Menú lateral oscuro con «Alerta temprana / Riesgo de abandono», título de la pantalla
arriba a la izquierda y, arriba a la derecha, el selector del usuario de prueba
(decisión P5): en el Sprint 1 no hay inicio de sesión, así que en lugar de «Cerrar
sesión» se elige el usuario que queda registrado en cargas y cambios de estado. El
selector define el menú y la pantalla que se muestra: el contenido siempre es una de las
pantallas del menú del usuario elegido; si no lo es (al cambiar de usuario o al escribir
una dirección a mano), se pasa a la pantalla inicial de su rol (decisión del 09/11). Es
**navegación, no control de acceso**: cualquiera puede elegir cualquier usuario y la API
no cambia.
"""

from __future__ import annotations

from dash import dcc, html

from alerta_temprana.db.inicializacion import (
    ROL_AREA_SISTEMAS,
    ROL_COORDINACION,
    ROL_SECRETARIA,
    ROL_TUTOR,
    USUARIOS_PRUEBA,
)

# Usuarios del selector (06-pantallas.md: Área de Sistemas, Coordinación, Tutor/a; y
# Secretaría Académica, que no ve alertas ni fichas y cuyo panel de métricas es HU-008)
USUARIOS_SELECTOR: dict[str, str] = {
    "sistemas01": "Área de Sistemas",
    "coordinacion01": "Coordinación",
    "tutor01": "Tutor/a",
    "secretaria01": "Secretaría Académica",
}
USUARIO_POR_DEFECTO = "sistemas01"

# Pantallas del Sprint 1 (ruta -> título)
RUTA_CARGA = "/"
RUTA_LISTADO = "/listado"
RUTA_METRICAS = "/metricas"
TITULOS: dict[str, str] = {
    RUTA_CARGA: "Carga de datos",
    RUTA_LISTADO: "Listado de alertas tempranas",
    RUTA_METRICAS: "Panel de métricas",
}

# Menú por rol (ruta, texto del enlace). La primera es la pantalla inicial del rol.
MENU_POR_ROL: dict[str, list[tuple[str, str]]] = {
    ROL_AREA_SISTEMAS: [(RUTA_CARGA, "Carga de datos")],
    ROL_COORDINACION: [(RUTA_LISTADO, "Listado de alertas")],
    ROL_TUTOR: [(RUTA_LISTADO, "Listado de alertas")],
    ROL_SECRETARIA: [(RUTA_METRICAS, "Panel de métricas")],
}
AVISO_SIN_PANTALLAS = "El panel de métricas (HU-008) no forma parte de este prototipo."

# Nivel de urgencia: color **y** texto (HU-005, criterio 4)
ETIQUETA_NIVEL: dict[str, str] = {"alto": "Alto", "medio": "Medio", "bajo": "Bajo"}
COLOR_NIVEL: dict[str, dict[str, str]] = {
    "alto": {"fondo": "#fee2e2", "texto": "#991b1b"},
    "medio": {"fondo": "#fef3c7", "texto": "#92400e"},
    "bajo": {"fondo": "#d1fae5", "texto": "#065f46"},
}

# Estado de seguimiento (términos fijos de CLAUDE.md)
ETIQUETA_ESTADO: dict[str, str] = {
    "pendiente": "Pendiente",
    "contactado": "Contactado",
    "en_acompanamiento": "En acompañamiento",
}

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


def etiqueta_nivel(nivel: str) -> html.Span:
    """Nivel de urgencia como etiqueta con color y con el texto «Alto», «Medio» o «Bajo»,
    para que la lectura no dependa solo del color."""
    color = COLOR_NIVEL[nivel]
    return html.Span(
        ETIQUETA_NIVEL[nivel],
        className=f"nivel nivel-{nivel}",
        style={
            "background": color["fondo"],
            "color": color["texto"],
            "border": f"1px solid {color['texto']}",
            "borderRadius": "999px",
            "padding": "2px 10px",
            "fontWeight": 600,
            "fontSize": "0.9em",
            "whiteSpace": "nowrap",
        },
    )


def menu_de(nombre_usuario: str | None) -> list[tuple[str, str]]:
    """Pantallas del menú del usuario de prueba (uno desconocido usa el de por defecto)."""
    rol = USUARIOS_PRUEBA.get(nombre_usuario or "", USUARIOS_PRUEBA[USUARIO_POR_DEFECTO])
    return MENU_POR_ROL[rol]


def ruta_para(nombre_usuario: str | None, ruta: str | None) -> str:
    """Pantalla que corresponde mostrar: la actual si está en el menú del usuario; si no,
    la pantalla inicial de su rol. Es navegación, no control de acceso."""
    rutas = [r for r, _ in menu_de(nombre_usuario)]
    return ruta if ruta in rutas else rutas[0]


def opciones_menu(nombre_usuario: str | None, ruta_actual: str | None = None) -> list:
    """Enlaces del menú lateral según el rol del usuario de prueba."""
    return [
        html.Div(
            dcc.Link(
                texto,
                href=ruta,
                style={
                    "color": "#fff",
                    "textDecoration": "none",
                    "fontWeight": 600 if ruta == ruta_actual else 400,
                },
            ),
            style={"marginBottom": "12px"},
        )
        for ruta, texto in menu_de(nombre_usuario)
    ]


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
                    html.H2(titulo, id="titulo-pagina", style={"margin": 0}),
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
