"""Pantalla del listado de alertas tempranas (Figura 6; HU-005, tarea 5.2).

Filtros arriba (carrera, turno, nivel de urgencia y estado de seguimiento), **sin valor
al abrir**: se muestran todas las alertas, incluidas las de nivel bajo (observación 7 del
tutor, 07/11). Debajo, las tarjetas de nivel alto, nivel medio y pendientes de contacto,
calculadas sobre las mismas alertas que muestra la tabla, y la tabla en un contenedor con
desplazamiento y encabezado fijo.

El callback solo arma los filtros, llama a servicio/alertas.py y muestra el resultado:
el orden y los filtros están en la consulta. Cada fila tiene «Ver ficha», que abre la
ficha de la alerta (HU-006) sin recargar la página. El desplegable del estado es de
HU-007; acá el estado se muestra como texto.
"""

from __future__ import annotations

from dash import Input, Output, callback, dcc, html
from sqlalchemy.exc import SQLAlchemyError

from alerta_temprana import formato
from alerta_temprana.db.sesion import obtener_fabrica_sesiones
from alerta_temprana.modelo.etiquetas import CARRERA
from alerta_temprana.servicio.alertas import (
    ESTADOS_SEGUIMIENTO,
    TURNOS,
    FiltrosAlertas,
    consultar_alertas,
    resumir_alertas,
)
from alerta_temprana.ui.diseno import (
    COLOR_BORDE,
    COLOR_NIVEL,
    COLOR_TARJETA,
    COLOR_TEXTO_SECUNDARIO,
    ESTILO_TARJETA,
    ETIQUETA_ESTADO,
    ETIQUETA_NIVEL,
    etiqueta_nivel,
    ruta_ficha,
)

COLUMNAS_TABLA: dict[str, str] = {
    "codigo_estudiante": "Código",
    "carrera": "Carrera",
    "turno": "Turno",
    "nivel": "Nivel",
    "probabilidad": "Probabilidad",
    "estado": "Estado",
    "ficha": "Ficha",  # enlace «Ver ficha» (HU-006)
}
VER_FICHA = "Ver ficha"
ETIQUETA_TURNO = {"diurno": "Diurno", "nocturno": "Nocturno"}
FILTROS = ("filtro-carrera", "filtro-turno", "filtro-nivel", "filtro-estado")

SIN_ALERTAS = "Todavía no hay alertas."
SIN_COINCIDENCIAS = "Ninguna alerta cumple los filtros."
ALTO_TABLA = "480px"  # la captura de la Figura 6 muestra filtros, tarjetas y las primeras filas

_ESTILO_CELDA = {"textAlign": "left", "padding": "8px", "borderBottom": f"1px solid {COLOR_BORDE}"}
_ESTILO_ENCABEZADO = {
    **_ESTILO_CELDA,
    "position": "sticky",
    "top": 0,
    "background": COLOR_TARJETA,
    "zIndex": 1,
    "boxShadow": f"inset 0 -1px 0 {COLOR_BORDE}",
}


def _filtro(id_: str, etiqueta: str, opciones: list[dict], marcador: str, multiple: bool = True) -> html.Div:
    return html.Div(
        [
            html.Label(etiqueta, htmlFor=id_, style={"fontWeight": 600, "display": "block"}),
            dcc.Dropdown(id=id_, options=opciones, value=None, multi=multiple, placeholder=marcador),
        ],
        style={"flex": "1 1 200px", "minWidth": "180px"},
    )


def filtros() -> html.Div:
    carreras = sorted(CARRERA.items(), key=lambda par: par[1])
    return html.Div(
        style={**ESTILO_TARJETA, "display": "flex", "flexWrap": "wrap", "gap": "16px"},
        children=[
            _filtro("filtro-carrera", "Carrera", [{"label": n, "value": c} for c, n in carreras], "Todas"),
            _filtro(
                "filtro-turno",
                "Turno",
                [{"label": ETIQUETA_TURNO[t], "value": t} for t in TURNOS],
                "Todos",
                multiple=False,
            ),
            _filtro(
                "filtro-nivel",
                "Nivel de urgencia",
                [{"label": e, "value": n} for n, e in ETIQUETA_NIVEL.items()],
                "Todos",
            ),
            _filtro(
                "filtro-estado",
                "Estado de seguimiento",
                [{"label": ETIQUETA_ESTADO[e], "value": e} for e in ESTADOS_SEGUIMIENTO],
                "Todos",
            ),
        ],
    )


def contenido() -> list:
    return [
        filtros(),
        html.Div(id="tarjetas-listado", style={"display": "flex", "flexWrap": "wrap", "gap": "20px"}),
        html.Div(
            style=ESTILO_TARJETA,
            children=[
                html.Div(id="cantidad-alertas", style={"color": COLOR_TEXTO_SECUNDARIO, "marginBottom": "8px"}),
                html.Div(
                    id="contenedor-tabla-alertas",
                    style={"maxHeight": ALTO_TABLA, "overflowY": "auto"},
                    children=html.Table(
                        style={"width": "100%", "borderCollapse": "collapse"},
                        children=[
                            html.Thead(
                                html.Tr([html.Th(t, style=_ESTILO_ENCABEZADO) for t in COLUMNAS_TABLA.values()])
                            ),
                            html.Tbody(id="tabla-alertas"),
                        ],
                    ),
                ),
            ],
        ),
    ]


# --- Presentación (sin lógica de negocio) ------------------------------------------------


def _tarjeta(titulo: str, valor: int, color: str | None = None) -> html.Div:
    borde = {"borderLeft": f"6px solid {color}"} if color else {}
    return html.Div(
        [
            html.Div(titulo, style={"color": COLOR_TEXTO_SECUNDARIO}),
            html.Strong(formato.entero(valor), style={"fontSize": "1.8em"}),
        ],
        style={**ESTILO_TARJETA, **borde, "flex": "1 1 180px"},
    )


def tarjetas(resumen: dict[str, int]) -> list[html.Div]:
    return [
        _tarjeta("Nivel alto", resumen["alto"], COLOR_NIVEL["alto"]["texto"]),
        _tarjeta("Nivel medio", resumen["medio"], COLOR_NIVEL["medio"]["texto"]),
        _tarjeta("Pendientes de contacto", resumen["pendientes"]),
    ]


def texto_cantidad(total: int) -> str:
    return "1 alerta" if total == 1 else f"{formato.entero(total)} alertas"


def _celda(alerta: dict, columna: str):
    if columna == "nivel":
        return etiqueta_nivel(alerta["nivel"])
    if columna == "probabilidad":
        return formato.decimal(alerta["probabilidad"], 2)
    if columna == "turno":
        return ETIQUETA_TURNO[alerta["turno"]]
    if columna == "estado":
        return ETIQUETA_ESTADO[alerta["estado"]]
    if columna == "ficha":
        return dcc.Link(VER_FICHA, href=ruta_ficha(alerta["id_alerta"]))  # sin recargar la página
    return alerta[columna]


def filas_tabla(alertas: list[dict], con_filtros: bool = False) -> list[html.Tr]:
    if not alertas:
        mensaje = SIN_COINCIDENCIAS if con_filtros else SIN_ALERTAS
        return [html.Tr(html.Td(mensaje, colSpan=len(COLUMNAS_TABLA), style=_ESTILO_CELDA))]
    return [
        html.Tr([html.Td(_celda(a, c), style=_ESTILO_CELDA) for c in COLUMNAS_TABLA]) for a in alertas
    ]


def armar_filtros(
    carreras: list[int] | None, turno: str | None, niveles: list[str] | None, estados: list[str] | None
) -> FiltrosAlertas:
    return FiltrosAlertas(
        carreras=list(carreras or []), turno=turno or None, niveles=list(niveles or []), estados=list(estados or [])
    )


# --- Callback --------------------------------------------------------------------------


@callback(
    Output("tarjetas-listado", "children"),
    Output("cantidad-alertas", "children"),
    Output("tabla-alertas", "children"),
    *(Input(f, "value") for f in FILTROS),
    Input("usuario-prueba", "value"),
    Input("estado-recalculo", "data"),
)
def actualizar_listado(carreras, turno, niveles, estados, _usuario, _estado):
    filtros_activos = armar_filtros(carreras, turno, niveles, estados)
    con_filtros = filtros_activos != FiltrosAlertas()
    try:
        with obtener_fabrica_sesiones()() as sesion:
            alertas = consultar_alertas(sesion, filtros_activos)
    except SQLAlchemyError:
        mensaje = html.Tr(
            html.Td("No se pudo consultar la base de datos.", colSpan=len(COLUMNAS_TABLA), style=_ESTILO_CELDA)
        )
        return [], "", [mensaje]
    resumen = resumir_alertas(alertas)
    return tarjetas(resumen), texto_cantidad(resumen["total"]), filas_tabla(alertas, con_filtros)
