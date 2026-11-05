"""Pantalla de carga de datos (Figura 5; HU-001).

Los callbacks solo leen la pantalla, llaman a servicio/carga.py y muestran el
resultado: la validación, la seudonimización y el guardado no están acá. El archivo
subido viaja en memoria (base64) y se descarta después de procesarlo; el informe de
errores se arma en memoria y no se guarda en la base.
"""

from __future__ import annotations

import base64

from dash import Input, Output, State, callback, dcc, html, no_update
from sqlalchemy.exc import SQLAlchemyError

from alerta_temprana import formato
from alerta_temprana.datos.carga import informe_errores_csv
from alerta_temprana.datos.validacion import CargaRechazada, ErrorRegistro
from alerta_temprana.datos.variables import ETIQUETA_MOMENTO, Momento
from alerta_temprana.db.sesion import obtener_fabrica_sesiones
from alerta_temprana.servicio.carga import PermisoDenegado, ResultadoCarga, listar_cargas, registrar_carga
from alerta_temprana.ui.diseno import (
    COLOR_BORDE,
    COLOR_ERROR,
    COLOR_OK,
    COLOR_TEXTO_SECUNDARIO,
    ESTILO_TARJETA,
    es_area_sistemas,
)

COLUMNAS_CARGAS: dict[str, str] = {
    "fecha": "Fecha",
    "momento": "Momento",
    "usuario": "Usuario",
    "validos": "Válidos",
    "rechazados": "Rechazados",
}
_ESTILO_CELDA = {"textAlign": "left", "padding": "6px 8px", "borderBottom": f"1px solid {COLOR_BORDE}"}
LEYENDA_SEUDONIMIZACION = "Los datos identificatorios se reemplazaron por códigos seudonimizados."
AVISO_OTRO_ROL = (
    "La carga de datos es del Área de Sistemas de Información. "
    "Elegí el usuario «Área de Sistemas» en la barra superior."
)


def contenido() -> list:
    return [
        html.Div(id="aviso-rol", style={**ESTILO_TARJETA, "display": "none"}),
        html.Div(
            id="formulario-carga",
            style=ESTILO_TARJETA,
            children=[
                html.Label("Momento de predicción", htmlFor="momento-carga", style={"fontWeight": 600}),
                dcc.RadioItems(
                    id="momento-carga",
                    options=[{"label": f" {ETIQUETA_MOMENTO[m]}", "value": m.value} for m in Momento],
                    value=Momento.INSCRIPCION.value,
                    inline=True,
                    labelStyle={"marginRight": "24px"},
                    style={"margin": "8px 0 20px"},
                ),
                dcc.Upload(
                    id="archivo-carga",
                    accept=".csv,text/csv",
                    multiple=False,
                    children=html.Div(
                        [
                            "Arrastrá el archivo CSV acá o ",
                            html.A("elegilo", style={"textDecoration": "underline"}),
                        ]
                    ),
                    style={
                        "border": f"2px dashed {COLOR_BORDE}",
                        "borderRadius": "8px",
                        "padding": "28px",
                        "textAlign": "center",
                        "cursor": "pointer",
                    },
                ),
                html.Div(id="nombre-archivo", style={"color": COLOR_TEXTO_SECUNDARIO, "margin": "8px 0"}),
                html.Small(
                    "CSV separado por «;», en UTF-8 y con punto decimal.",
                    style={"color": COLOR_TEXTO_SECUNDARIO, "display": "block", "marginBottom": "16px"},
                ),
                html.Button("Validar y cargar", id="boton-cargar", n_clicks=0, style={"padding": "8px 20px"}),
            ],
        ),
        dcc.Loading(html.Div(id="resultado-carga")),
        dcc.Store(id="errores-carga"),
        dcc.Store(id="id-ultima-carga"),
        dcc.Download(id="descarga-informe"),
        html.Div(
            style=ESTILO_TARJETA,
            children=[
                html.H3("Cargas anteriores", style={"marginTop": 0}),
                html.Table(
                    style={"width": "100%", "borderCollapse": "collapse"},
                    children=[
                        html.Thead(
                            html.Tr(
                                [html.Th(nombre, style=_ESTILO_CELDA) for nombre in COLUMNAS_CARGAS.values()]
                            )
                        ),
                        html.Tbody(id="tabla-cargas"),
                    ],
                ),
            ],
        ),
    ]


# --- Presentación del resultado (sin lógica de negocio) --------------------------------


def _dato(etiqueta: str, valor: str) -> html.Div:
    return html.Div(
        [
            html.Div(etiqueta, style={"color": COLOR_TEXTO_SECUNDARIO}),
            html.Strong(valor, style={"fontSize": "1.4em"}),
        ],
        style={"minWidth": "150px"},
    )


def mostrar_resultado(resultado: ResultadoCarga) -> html.Div:
    descartadas = resultado.columnas_descartadas
    texto_descarte = "; ".join(
        f"{grupo}: {', '.join(columnas)}" for grupo, columnas in descartadas.items() if columnas
    )
    return html.Div(
        style=ESTILO_TARJETA,
        children=[
            html.H3("Resultado de la carga", style={"marginTop": 0, "color": COLOR_OK}),
            html.P(
                f"{ETIQUETA_MOMENTO[Momento(resultado.momento)]} · "
                f"{formato.fecha_hora(formato.hora_argentina(resultado.fecha))} · {resultado.usuario}"
            ),
            html.Div(
                style={"display": "flex", "gap": "24px", "flexWrap": "wrap", "margin": "12px 0"},
                children=[
                    _dato("Registros válidos", formato.entero(resultado.registros_validos)),
                    _dato("Registros rechazados", formato.entero(resultado.registros_rechazados)),
                    _dato("Estudiantes nuevos", formato.entero(resultado.estudiantes_nuevos)),
                    _dato("Ya existentes", formato.entero(resultado.estudiantes_existentes)),
                    _dato(
                        "Rendimientos semestrales agregados", formato.entero(resultado.rendimientos_agregados)
                    ),
                ],
            ),
            html.Button(
                "Descargar informe de errores",
                id="boton-informe",
                n_clicks=0,
                disabled=not resultado.errores,
                style={"padding": "6px 16px"},
            ),
            html.P(LEYENDA_SEUDONIMIZACION, style={"marginTop": "16px"}),
            html.Small(
                f"Columnas descartadas: {texto_descarte}." if texto_descarte else "",
                style={"color": COLOR_TEXTO_SECUNDARIO},
            ),
        ],
    )


def mostrar_rechazo(error: CargaRechazada) -> html.Div:
    return html.Div(
        style={**ESTILO_TARJETA, "borderColor": COLOR_ERROR},
        children=[
            html.H3("Carga rechazada", style={"marginTop": 0, "color": COLOR_ERROR}),
            html.P(error.mensaje),
            html.Ul([html.Li(f"{p.columna}: {p.motivo}") for p in error.problemas])
            if error.problemas
            else None,
            html.P("No se incorporó ningún registro.", style={"color": COLOR_TEXTO_SECUNDARIO}),
        ],
    )


def mostrar_aviso(mensaje: str) -> html.Div:
    return html.Div(
        html.P(mensaje, style={"margin": 0}), style={**ESTILO_TARJETA, "borderColor": COLOR_ERROR}
    )


def filas_cargas_anteriores(cargas: list[dict]) -> list[dict]:
    return [
        {
            "fecha": formato.fecha_hora(formato.hora_argentina(c["fecha"])),
            "momento": ETIQUETA_MOMENTO[Momento(c["momento"])],
            "usuario": c["usuario"],
            "validos": formato.entero(c["registros_validos"]),
            "rechazados": formato.entero(c["registros_rechazados"]),
        }
        for c in cargas
    ]


def decodificar_archivo(contenido_upload: str) -> bytes:
    """`data:<tipo>;base64,<datos>` de dcc.Upload -> bytes (en memoria)."""
    return base64.b64decode(contenido_upload.split(",", 1)[1])


# --- Callbacks ------------------------------------------------------------------------


@callback(
    Output("formulario-carga", "style"),
    Output("aviso-rol", "style"),
    Output("aviso-rol", "children"),
    Output("menu-opciones", "children"),
    Input("usuario-prueba", "value"),
)
def segun_usuario(usuario: str):
    if es_area_sistemas(usuario):
        menu = [html.Div("Carga de datos", style={"fontWeight": 600})]
        return ESTILO_TARJETA, {**ESTILO_TARJETA, "display": "none"}, None, menu
    menu = [
        html.Small("El listado y la ficha se agregan en las próximas historias.", style={"color": "#d1d5db"})
    ]
    return (
        {**ESTILO_TARJETA, "display": "none"},
        ESTILO_TARJETA,
        html.P(AVISO_OTRO_ROL, style={"margin": 0}),
        menu,
    )


@callback(Output("nombre-archivo", "children"), Input("archivo-carga", "filename"))
def mostrar_nombre(nombre: str | None):
    return f"Archivo elegido: {nombre}" if nombre else ""


@callback(
    Output("resultado-carga", "children"),
    Output("errores-carga", "data"),
    Output("id-ultima-carga", "data"),
    Output("archivo-carga", "contents"),
    Input("boton-cargar", "n_clicks"),
    State("archivo-carga", "contents"),
    State("momento-carga", "value"),
    State("usuario-prueba", "value"),
    prevent_initial_call=True,
)
def cargar(_clics: int, contenido_upload: str | None, momento: str, usuario: str):
    if not contenido_upload:
        return mostrar_aviso("Elegí un archivo CSV antes de cargar."), None, no_update, no_update
    try:
        contenido_archivo = decodificar_archivo(contenido_upload)
    except (ValueError, IndexError):
        return mostrar_aviso("No se pudo leer el archivo."), None, no_update, None
    try:
        with obtener_fabrica_sesiones()() as sesion:
            resultado = registrar_carga(sesion, contenido_archivo, momento, usuario)
    except PermisoDenegado as error:
        return mostrar_aviso(str(error)), None, no_update, None
    except CargaRechazada as error:
        return mostrar_rechazo(error), None, no_update, None
    except SQLAlchemyError:
        return (
            mostrar_aviso("No se pudo guardar la carga: la base de datos no responde."),
            None,
            no_update,
            None,
        )
    errores = [e.__dict__ for e in resultado.errores]
    return (
        mostrar_resultado(resultado),
        {"id_carga": resultado.id_carga, "errores": errores},
        resultado.id_carga,
        None,
    )


@callback(
    Output("descarga-informe", "data"),
    Input("boton-informe", "n_clicks"),
    State("errores-carga", "data"),
    prevent_initial_call=True,
)
def descargar_informe(clics: int, datos: dict | None):
    if not clics or not datos:
        return no_update
    errores = [ErrorRegistro(**e) for e in datos["errores"]]
    return dcc.send_bytes(informe_errores_csv(errores), f"informe_errores_carga_{datos['id_carga']}.csv")


@callback(
    Output("tabla-cargas", "children"), Input("usuario-prueba", "value"), Input("id-ultima-carga", "data")
)
def actualizar_cargas_anteriores(_usuario: str, _id_carga: int | None):
    try:
        with obtener_fabrica_sesiones()() as sesion:
            filas = filas_cargas_anteriores(listar_cargas(sesion))
    except SQLAlchemyError:  # base no disponible: la pantalla sigue funcionando
        return [html.Tr(html.Td("No se pudo consultar la base de datos.", colSpan=len(COLUMNAS_CARGAS)))]
    if not filas:
        return [html.Tr(html.Td("Todavía no hay cargas.", colSpan=len(COLUMNAS_CARGAS)))]
    return [html.Tr([html.Td(fila[c], style=_ESTILO_CELDA) for c in COLUMNAS_CARGAS]) for fila in filas]
