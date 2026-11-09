"""Última actualización del riesgo en la barra superior (HU-003, criterio 4).

Cualquier usuario que consulta la plataforma ve la fecha del último cálculo y la versión
del modelo usado. Se actualiza al abrir la página, al cambiar de usuario y al terminar
un recálculo. HU-005 muestra lo mismo en el listado (Figura 6).
"""

from __future__ import annotations

from dash import Input, Output, callback
from sqlalchemy.exc import SQLAlchemyError

from alerta_temprana import formato
from alerta_temprana.datos.variables import ETIQUETA_MOMENTO, Momento
from alerta_temprana.db.sesion import obtener_fabrica_sesiones
from alerta_temprana.servicio.prediccion import ultima_actualizacion

SIN_CALCULO = "Todavía no se calculó el riesgo."


def texto_ultima_actualizacion(ultima: dict | None) -> str:
    """«Última actualización: 06/11/2026 14:32 · modelo v1.0 (Cierre del 1.er semestre)»."""
    if ultima is None:
        return SIN_CALCULO
    fecha = formato.fecha_hora(formato.hora_argentina(ultima["fecha"]))
    momento = ETIQUETA_MOMENTO[Momento(ultima["momento"])]
    return f"Última actualización: {fecha} · modelo v{ultima['version']} ({momento})"


@callback(
    Output("ultima-actualizacion", "children"),
    Input("usuario-prueba", "value"),
    Input("estado-recalculo", "data"),
)
def mostrar_ultima_actualizacion(_usuario: str, _estado: dict | None) -> str:
    try:
        with obtener_fabrica_sesiones()() as sesion:
            return texto_ultima_actualizacion(ultima_actualizacion(sesion))
    except SQLAlchemyError:
        return "No se pudo consultar la última actualización: la base de datos no responde."
