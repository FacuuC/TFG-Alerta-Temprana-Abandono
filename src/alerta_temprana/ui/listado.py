"""Pantalla del listado de alertas tempranas (Figura 6; HU-005, tarea 5.2).

Filtros arriba (carrera, turno, nivel de urgencia y estado de seguimiento), **sin valor
al abrir**: se muestran todas las alertas, incluidas las de nivel bajo (observación 7 del
tutor, 07/11). Debajo, las tarjetas de nivel alto, nivel medio y pendientes de contacto,
calculadas sobre las mismas alertas que muestra la tabla, y la tabla en un contenedor con
desplazamiento y encabezado fijo.

El callback solo arma los filtros, llama a servicio/alertas.py y muestra el resultado:
el orden y los filtros están en la consulta. Cada fila tiene «Ver ficha», que abre la
ficha de la alerta (HU-006) sin recargar la página.

Estado de seguimiento (HU-007, tarea 7.2): cada fila tiene el desplegable con el estado
actual y «Guardar». Al guardar se llama a `cambiar_estado` (ui/seguimiento.py), aparece el
mensaje de confirmación arriba de la tabla y se actualizan las tarjetas, sobre las mismas
alertas que muestra la tabla. La tabla no se vuelve a armar: con 529 alertas eso tarda
unos 2,5 s por guardado (medición del 09/11), y el desplegable ya muestra el estado nuevo.
Con un filtro de estado activo, la fila guardada sigue a la vista hasta que cambie un
filtro o el usuario; ahí la tabla se vuelve a consultar.
"""

from __future__ import annotations

from dash import ALL, Input, Output, State, callback, ctx, dcc, html, no_update
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
from alerta_temprana.ui.seguimiento import boton_guardar, desplegable_estado, guardar_estado

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
GUARDAR = "Guardar"
ID_ESTADO = "estado-alerta"  # desplegable de cada fila: {"type": ID_ESTADO, "index": id_alerta}
ID_GUARDAR = "guardar-estado"  # botón de cada fila: {"type": ID_GUARDAR, "index": id_alerta}
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
        id="filtros-listado",
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
    # Cada contenedor de primer nivel tiene id propio (ver diseno.py, «ids de primer nivel»)
    return [
        filtros(),
        html.Div(id="tarjetas-listado", style={"display": "flex", "flexWrap": "wrap", "gap": "20px"}),
        html.Div(
            id="contenedor-listado",
            style=ESTILO_TARJETA,
            children=[
                html.Div(id="mensaje-estado-listado"),  # confirmación del cambio de estado (HU-007)
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


def control_estado(alerta: dict) -> html.Div:
    """Desplegable con el estado actual y «Guardar» (HU-007)."""
    id_alerta = alerta["id_alerta"]
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "8px"},
        children=[
            desplegable_estado({"type": ID_ESTADO, "index": id_alerta}, alerta["estado"], ancho="190px"),
            boton_guardar({"type": ID_GUARDAR, "index": id_alerta}, GUARDAR, relleno="6px 12px"),
        ],
    )


def _celda(alerta: dict, columna: str):
    if columna == "nivel":
        return etiqueta_nivel(alerta["nivel"])
    if columna == "probabilidad":
        return formato.decimal(alerta["probabilidad"], 2)
    if columna == "turno":
        return ETIQUETA_TURNO[alerta["turno"]]
    if columna == "estado":
        return control_estado(alerta)
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


def alerta_a_guardar(disparador, clics, ids: list[dict], valores: list) -> tuple[int, str | None] | None:
    """(id_alerta, estado elegido) del botón que se apretó, o None si el callback se disparó
    porque la tabla se volvió a armar (los botones nuevos llegan con 0 clics).

    `disparador` es el id del botón y `clics`, sus clics."""
    if not isinstance(disparador, dict) or not clics:
        return None
    id_alerta = disparador["index"]
    elegido = {i["index"]: v for i, v in zip(ids, valores, strict=True)}
    if id_alerta not in elegido:
        return None
    return id_alerta, elegido[id_alerta]


def resumen_visible(alertas: list[dict], ids_visibles: list[int]) -> dict[str, int]:
    """Contadores de las tarjetas sobre las alertas que muestra la tabla (decisión del 07/11),
    con su estado actual."""
    visibles = set(ids_visibles)
    return resumir_alertas([a for a in alertas if a["id_alerta"] in visibles])


def tarjetas_actualizadas(ids_visibles: list[int]) -> list[html.Div]:
    with obtener_fabrica_sesiones()() as sesion:
        alertas = consultar_alertas(sesion)
    return tarjetas(resumen_visible(alertas, ids_visibles))


@callback(
    Output("mensaje-estado-listado", "children"),
    Output("tarjetas-listado", "children", allow_duplicate=True),
    Input({"type": ID_GUARDAR, "index": ALL}, "n_clicks"),
    State({"type": ID_ESTADO, "index": ALL}, "id"),
    State({"type": ID_ESTADO, "index": ALL}, "value"),
    State("usuario-prueba", "value"),
    prevent_initial_call=True,
)
def guardar_desde_listado(_clics, ids, valores, usuario):
    clics_disparador = ctx.triggered[0]["value"] if ctx.triggered else None
    elegida = alerta_a_guardar(ctx.triggered_id, clics_disparador, ids, valores)
    if elegida is None:
        return no_update, no_update
    id_alerta, estado = elegida
    guardado = guardar_estado(id_alerta, estado, usuario)
    if guardado.resultado is None or not guardado.resultado.registrado:
        return guardado.mensaje, no_update
    try:
        return guardado.mensaje, tarjetas_actualizadas([i["index"] for i in ids])
    except SQLAlchemyError:
        return guardado.mensaje, no_update
