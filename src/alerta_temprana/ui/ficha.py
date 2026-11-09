"""Pantalla de la ficha del estudiante (Figura 7; HU-006, tarea 6.3).

Se abre con «Ver ficha» desde el listado (/ficha/<id_alerta>). Arriba, el enlace para
volver al listado y las tarjetas de probabilidad de abandono, nivel de urgencia, carrera
y turno, y cálculo (fecha y hora · modelo). Debajo, «Factores que más pesan en esta
estimación»: los cinco factores con nombre y valor comprensibles, una barra proporcional
al peso y «Aumenta el riesgo» (rojo) o «Disminuye el riesgo» (azul), seguidos del aviso
del criterio 4. Al final, «Seguimiento» (HU-007, tarea 7.2): el desplegable del estado,
«Guardar estado», el mensaje de confirmación, el último cambio (usuario y fecha y hora en
hora argentina) y «Alerta creada el dd/mm/aaaa».

Diferencias con el prototipo dibujado que no se copian (06-pantallas.md): el título dice
«más pesan» (no «más influyen»), no aparece ninguna variable excluida y el aviso aclara
que los factores no son causas.

La consulta está en servicio/ficha.py; acá solo se presenta el resultado.
"""

from __future__ import annotations

from dash import Input, Output, State, callback, dcc, html, no_update
from sqlalchemy.exc import SQLAlchemyError

from alerta_temprana import formato
from alerta_temprana.datos.variables import ETIQUETA_MOMENTO, Momento
from alerta_temprana.db.sesion import obtener_fabrica_sesiones
from alerta_temprana.modelo.etiquetas import AVISO_FICHA, TITULO_FACTORES
from alerta_temprana.servicio.ficha import consultar_ficha
from alerta_temprana.ui import seguimiento as control
from alerta_temprana.ui.diseno import (
    COLOR_BORDE,
    COLOR_ERROR,
    COLOR_SENTIDO,
    COLOR_TEXTO_SECUNDARIO,
    ESTILO_TARJETA,
    RUTA_LISTADO,
    etiqueta_nivel,
)

TITULO = "Ficha del estudiante"
VOLVER = "← Volver al listado"
SIN_ALERTA = "No se encontró la alerta."
SIN_BASE = "No se pudo consultar la base de datos."
SIN_EXPLICACION = "No se puede mostrar la explicación de esta alerta."
ETIQUETA_TURNO = {"diurno": "Diurno", "nocturno": "Nocturno"}
GUARDAR_ESTADO = "Guardar estado"


def _leer_ficha(id_alerta: int) -> dict | None:
    with obtener_fabrica_sesiones()() as sesion:
        return consultar_ficha(sesion, id_alerta)


def pantalla(id_alerta: int) -> tuple[str, list]:
    """(título, contenido) de la ficha de una alerta."""
    try:
        ficha = _leer_ficha(id_alerta)
    except SQLAlchemyError:
        return TITULO, [enlace_volver(), _mensaje(SIN_BASE)]
    if ficha is None:
        return TITULO, [enlace_volver(), _mensaje(SIN_ALERTA)]
    return f"{TITULO} {ficha['codigo_estudiante']}", contenido(ficha)


# --- Presentación (sin lógica de negocio) ------------------------------------------------


def enlace_volver() -> html.Div:
    return html.Div(
        dcc.Link(VOLVER, href=RUTA_LISTADO, id="volver-listado"), id="ficha-volver", style={"marginBottom": "16px"}
    )


def _mensaje(texto: str) -> html.Div:
    return html.Div(html.P(texto, style={"margin": 0}), id="ficha-mensaje", style=ESTILO_TARJETA)


def _tarjeta(titulo: str, *valor, id_: str) -> html.Div:
    return html.Div(
        [html.Div(titulo, style={"color": COLOR_TEXTO_SECUNDARIO, "marginBottom": "8px"}), *valor],
        id=id_,
        style={**ESTILO_TARJETA, "flex": "1 1 200px", "marginBottom": 0},
    )


def texto_carrera_turno(carrera: str, turno: str) -> str:
    """«Educación Básica · Diurno»; las carreras que ya dicen «nocturno» no lo repiten."""
    return carrera if "nocturno" in carrera.lower() else f"{carrera} · {ETIQUETA_TURNO[turno]}"


def texto_modelo(version: str, momento: str) -> str:
    return f"modelo v{version} ({ETIQUETA_MOMENTO[Momento(momento)]})"


def tarjetas(ficha: dict) -> html.Div:
    fecha = formato.fecha_hora(formato.hora_argentina(ficha["fecha_calculo"]))
    return html.Div(
        id="ficha-tarjetas",
        style={"display": "flex", "flexWrap": "wrap", "gap": "20px", "marginBottom": "20px"},
        children=[
            _tarjeta(
                "Probabilidad de abandono",
                html.Strong(formato.decimal(ficha["probabilidad"], 2), style={"fontSize": "1.8em"}),
                id_="ficha-probabilidad",
            ),
            _tarjeta(
                "Nivel de urgencia",
                html.Div(etiqueta_nivel(ficha["nivel"]), style={"fontSize": "1.3em"}),
                id_="ficha-nivel",
            ),
            _tarjeta(
                "Carrera y turno",
                html.Strong(texto_carrera_turno(ficha["carrera"], ficha["turno"])),
                id_="ficha-carrera",
            ),
            _tarjeta(
                "Cálculo",
                html.Div(
                    [
                        html.Strong(fecha),
                        html.Span(f" · {texto_modelo(ficha['version_modelo'], ficha['momento'])}"),
                    ]
                ),
                id_="ficha-calculo",
            ),
        ],
    )


def _fila_factor(factor: dict, peso_maximo: float, ultima: bool) -> html.Div:
    color = COLOR_SENTIDO[factor["sentido"]]
    largo = 100 * abs(factor["contribucion"]) / peso_maximo if peso_maximo else 0
    return html.Div(
        className="factor",
        style={
            "display": "flex",
            "flexWrap": "wrap",
            "alignItems": "center",
            "gap": "8px 16px",
            "padding": "12px 0",
            "borderBottom": "none" if ultima else f"1px solid {COLOR_BORDE}",
        },
        children=[
            html.Div(factor["texto"], className="factor-texto", style={"flex": "1 1 320px"}),
            html.Div(
                html.Div(
                    className="factor-barra",
                    style={
                        "width": f"{max(largo, 2):.0f}%",
                        "height": "14px",
                        "background": color["barra"],
                        "borderRadius": "7px",
                    },
                ),
                style={"flex": "1 1 200px", "background": "#f3f4f6", "borderRadius": "7px"},
                title=f"Peso relativo: {largo:.0f} %",
            ),
            html.Strong(
                factor["texto_sentido"],
                className="factor-sentido",
                style={"color": color["texto"], "flex": "0 0 170px"},
            ),
        ],
    )


def aviso() -> html.Div:
    return html.Div(
        html.P(AVISO_FICHA, style={"margin": 0}),
        id="aviso-ficha",
        role="note",
        style={
            "marginTop": "16px",
            "padding": "12px 16px",
            "background": "#f9fafb",
            "borderLeft": f"4px solid {COLOR_TEXTO_SECUNDARIO}",
            "color": "#374151",
        },
    )


def factores(lista: list[dict] | None) -> html.Div:
    """Sección de los factores con el aviso debajo. Sin factores (explicación que no se
    puede mostrar), el mensaje controlado en su lugar; el aviso se mantiene."""
    if lista is None:
        cuerpo = [html.P(SIN_EXPLICACION, id="ficha-sin-explicacion", style={"color": COLOR_ERROR})]
    else:
        maximo = max((abs(f["contribucion"]) for f in lista), default=0)
        cuerpo = [_fila_factor(f, maximo, i == len(lista) - 1) for i, f in enumerate(lista)]
    return html.Div(
        id="ficha-factores",
        style=ESTILO_TARJETA,
        children=[html.H3(TITULO_FACTORES, style={"marginTop": 0}), *cuerpo, aviso()],
    )


def seguimiento(ficha: dict) -> html.Div:
    """Seguimiento de la alerta (Figura 7; HU-007): estado editable, último cambio y creación."""
    creada = formato.fecha(formato.hora_argentina(ficha["fecha_creacion"]))
    return html.Div(
        id="ficha-seguimiento",
        style=ESTILO_TARJETA,
        children=[
            html.H3("Seguimiento", style={"marginTop": 0}),
            dcc.Store(id="ficha-id-alerta", data=ficha["id_alerta"]),
            html.Div(
                style={"display": "flex", "flexWrap": "wrap", "alignItems": "flex-end", "gap": "16px"},
                children=[
                    html.Div(
                        [
                            html.Label("Estado", htmlFor="ficha-estado", style={"display": "block"}),
                            control.desplegable_estado("ficha-estado", ficha["estado"], ancho="260px"),
                        ]
                    ),
                    control.boton_guardar("boton-guardar-estado", GUARDAR_ESTADO, relleno="9px 20px"),
                    html.Div(
                        f"Alerta creada el {creada}",
                        id="ficha-creada",
                        style={"color": COLOR_TEXTO_SECUNDARIO, "marginLeft": "auto"},
                    ),
                ],
            ),
            html.Div(id="mensaje-estado-ficha"),
            html.Div(control.ultimo_cambio(ficha["cambios_estado"]), id="ficha-ultimo-cambio"),
        ],
    )


def contenido(ficha: dict) -> list:
    return [enlace_volver(), tarjetas(ficha), factores(ficha["factores"]), seguimiento(ficha)]


# --- Callback (HU-007) ---------------------------------------------------------------------


def resultado_guardado(id_alerta: int, estado: str | None, usuario: str | None) -> tuple:
    """(mensaje, último cambio) después de guardar; el último cambio solo cambia si se
    registró un cambio."""
    guardado = control.guardar_estado(id_alerta, estado, usuario)
    resultado = guardado.resultado
    if resultado is None or not resultado.registrado:
        return guardado.mensaje, no_update
    cambio = {
        "estado_anterior": resultado.estado_anterior,
        "estado_nuevo": resultado.estado_nuevo,
        "usuario": resultado.usuario,
        "fecha": resultado.fecha,
    }
    return guardado.mensaje, control.ultimo_cambio([cambio])


@callback(
    Output("mensaje-estado-ficha", "children"),
    Output("ficha-ultimo-cambio", "children"),
    Input("boton-guardar-estado", "n_clicks"),
    State("ficha-estado", "value"),
    State("ficha-id-alerta", "data"),
    State("usuario-prueba", "value"),
    prevent_initial_call=True,
)
def guardar_desde_ficha(clics, estado, id_alerta, usuario):
    if not clics or id_alerta is None:
        return no_update, no_update
    return resultado_guardado(id_alerta, estado, usuario)
