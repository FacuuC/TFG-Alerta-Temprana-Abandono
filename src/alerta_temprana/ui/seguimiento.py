"""Control del estado de seguimiento en el listado y en la ficha (HU-007, tarea 7.2).

El desplegable con los tres estados y el botón para guardar. Al guardar, los callbacks
llaman a `guardar_estado`, que usa la función de servicio (`cambiar_estado`, la misma de
la API) y arma el mensaje de confirmación o el motivo del rechazo. Las fechas se guardan
en UTC y acá se muestran en hora argentina (dd/mm/aaaa hh:mm).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from dash import dcc, html
from sqlalchemy.exc import SQLAlchemyError

from alerta_temprana import formato
from alerta_temprana.db.sesion import obtener_fabrica_sesiones
from alerta_temprana.servicio.alertas import ESTADOS_SEGUIMIENTO
from alerta_temprana.servicio.seguimiento import (
    AlertaInexistente,
    CambioRegistrado,
    PermisoDenegado,
    cambiar_estado,
)
from alerta_temprana.ui.diseno import COLOR_ERROR, COLOR_OK, COLOR_TEXTO_SECUNDARIO, ETIQUETA_ESTADO

OPCIONES_ESTADO = [{"label": ETIQUETA_ESTADO[e], "value": e} for e in ESTADOS_SEGUIMIENTO]
SIN_BASE = "No se pudo guardar el estado: no se pudo conectar con la base de datos."
SIN_ALERTA = "No se encontró la alerta."

_ESTILO_BOTON = {
    "background": "#2563eb",
    "color": "#fff",
    "border": "none",
    "borderRadius": "6px",
    "cursor": "pointer",
    "fontWeight": 600,
}


def desplegable_estado(id_, estado: str, ancho: str) -> dcc.Dropdown:
    return dcc.Dropdown(
        id=id_,
        options=OPCIONES_ESTADO,
        value=estado,
        clearable=False,
        searchable=False,
        style={"width": ancho},
    )


def boton_guardar(id_, texto: str, relleno: str) -> html.Button:
    return html.Button(texto, id=id_, n_clicks=0, style={**_ESTILO_BOTON, "padding": relleno})


# --- Textos (sin lógica de negocio) --------------------------------------------------------


def _cuando(fecha: datetime) -> str:
    return formato.fecha_hora(formato.hora_argentina(fecha))


def texto_confirmacion(resultado: CambioRegistrado) -> str:
    estado = ETIQUETA_ESTADO[resultado.estado_nuevo]
    if not resultado.registrado:
        return f"{resultado.codigo_estudiante} ya estaba en «{estado}»; no se registró ningún cambio."
    return (
        f"Estado de {resultado.codigo_estudiante} guardado: {estado} "
        f"({resultado.usuario}, {_cuando(resultado.fecha)})."
    )


def texto_ultimo_cambio(estado_anterior: str, estado_nuevo: str, usuario: str, fecha: datetime) -> str:
    """«Último cambio: Pendiente → Contactado, por tutor01, el 09/11/2026 14:32»."""
    return (
        f"Último cambio: {ETIQUETA_ESTADO[estado_anterior]} → {ETIQUETA_ESTADO[estado_nuevo]}, "
        f"por {usuario}, el {_cuando(fecha)}"
    )


def mensaje(texto: str, correcto: bool) -> html.Div:
    return html.Div(
        texto,
        role="status",
        className="mensaje-estado " + ("mensaje-ok" if correcto else "mensaje-error"),
        style={"color": COLOR_OK if correcto else COLOR_ERROR, "fontWeight": 600, "margin": "8px 0"},
    )


def ultimo_cambio(cambios: list[dict]) -> html.Div | str:
    if not cambios:
        return ""
    ultimo = cambios[-1]
    return html.Div(
        texto_ultimo_cambio(ultimo["estado_anterior"], ultimo["estado_nuevo"], ultimo["usuario"], ultimo["fecha"]),
        style={"color": COLOR_TEXTO_SECUNDARIO, "marginTop": "4px"},
    )


# --- Guardado ------------------------------------------------------------------------------


@dataclass
class Guardado:
    mensaje: html.Div
    resultado: CambioRegistrado | None  # None si se rechazó


def guardar_estado(id_alerta: int, estado: str | None, usuario: str | None) -> Guardado:
    """Guarda el estado elegido con `cambiar_estado` y arma el mensaje para la pantalla."""
    try:
        with obtener_fabrica_sesiones()() as sesion:
            resultado = cambiar_estado(sesion, id_alerta, estado or "", usuario or "")
    except (PermisoDenegado, ValueError) as error:
        return Guardado(mensaje(str(error), correcto=False), None)
    except AlertaInexistente:
        return Guardado(mensaje(SIN_ALERTA, correcto=False), None)
    except SQLAlchemyError:
        return Guardado(mensaje(SIN_BASE, correcto=False), None)
    return Guardado(mensaje(texto_confirmacion(resultado), correcto=True), resultado)
