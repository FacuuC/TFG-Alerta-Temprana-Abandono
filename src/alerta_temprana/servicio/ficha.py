"""Ficha del estudiante de una alerta (HU-006, tarea 6.3; criterios 1 a 3).

Reúne la predicción vigente de la alerta (probabilidad, nivel, fecha del cálculo y modelo)
y sus cinco factores que más pesan en la estimación, con nombre y valor comprensibles.
Los factores muestran cuánto pesa cada variable en la estimación, **no las causas** del
abandono.

FACTOR_EXPLICATIVO.valor guarda el valor de la variable sin formatear («9853», «1»,
«13.21»; decisión del 05/11). Para el texto comprensible se usa ese valor guardado; la
fila del estudiante (armada con las variables del momento del modelo) solo aporta lo que
el texto necesita de otra variable, por ejemplo las materias inscriptas de «1 de 6».

El seguimiento incluye el estado actual, la fecha de creación de la alerta y sus cambios de
estado con usuario y fecha (CAMBIO_ESTADO; HU-007).

Si algún factor no corresponde al momento del modelo (una variable excluida, o una `_s2`
en un cálculo de cierre del 1.er semestre) o no hay exactamente cinco, la ficha se
devuelve **sin factores**: no se muestra ninguno y el detalle queda en el registro de la
aplicación, para que el error no llegue a la pantalla ni a la API.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from alerta_temprana.datos import variables as V
from alerta_temprana.db.tablas import Alerta, Estudiante, FactorExplicativo, Modelo, Prediccion
from alerta_temprana.modelo.etiquetas import CARRERA, SENTIDO_FACTOR, texto_factor
from alerta_temprana.servicio.prediccion import CANTIDAD_FACTORES, armar_datos
from alerta_temprana.servicio.seguimiento import historial_estados

registro = logging.getLogger(__name__)


class ExplicacionNoValida(Exception):
    """Los factores guardados de una predicción no se pueden mostrar."""


def _controlar_factores(factores: list[FactorExplicativo], momento: V.Momento) -> None:
    if len(factores) != CANTIDAD_FACTORES:
        raise ExplicacionNoValida(f"tiene {len(factores)} factores en lugar de {CANTIDAD_FACTORES}")
    permitidas = set(V.VARIABLES_POR_MOMENTO[momento])
    ajenas = [f.variable for f in factores if f.variable not in permitidas]
    if ajenas:
        raise ExplicacionNoValida(
            f"variables que no corresponden al momento {momento.value}: {', '.join(ajenas)}"
        )


def _valor_guardado(texto: str) -> float:
    try:
        return float(texto)
    except ValueError as error:
        raise ExplicacionNoValida(f"valor guardado no numérico: {texto!r}") from error


def factores_comprensibles(
    sesion: Session, codigo: str, momento: V.Momento, factores: list[FactorExplicativo]
) -> list[dict]:
    """Los cinco factores en orden, con su texto comprensible y su sentido.

    Lanza ExplicacionNoValida si alguno no corresponde al momento del modelo.
    """
    _controlar_factores(factores, momento)
    fila = armar_datos(sesion, [codigo], momento).loc[codigo].to_dict()
    resultado = []
    for factor in sorted(factores, key=lambda f: f.orden):
        fila_factor = fila | {factor.variable: _valor_guardado(factor.valor)}
        contribucion = float(factor.contribucion)
        aumenta = contribucion > 0
        resultado.append(
            {
                "orden": factor.orden,
                "variable": factor.variable,
                "texto": texto_factor(factor.variable, fila_factor),
                "contribucion": contribucion,
                "sentido": "aumenta" if aumenta else "disminuye",
                "texto_sentido": SENTIDO_FACTOR[aumenta],
            }
        )
    return resultado


def consultar_ficha(sesion: Session, id_alerta: int) -> dict | None:
    """Ficha de una alerta con su predicción vigente, o None si la alerta no existe.

    Sin datos identificatorios: solo el código seudonimizado. `factores` es None cuando
    la explicación guardada no se puede mostrar (ver el docstring del módulo).
    """
    fila = sesion.execute(
        select(
            Alerta, Prediccion, Modelo.version, Modelo.momento, Estudiante.carrera, Estudiante.turno_diurno
        )
        .join(Prediccion, Alerta.id_prediccion == Prediccion.id_prediccion)
        .join(Modelo, Prediccion.id_modelo == Modelo.id_modelo)
        .join(Estudiante, Alerta.codigo_estudiante == Estudiante.codigo_estudiante)
        .where(Alerta.id_alerta == id_alerta)
    ).first()
    if fila is None:
        return None
    alerta, prediccion, version, momento, carrera, turno_diurno = fila
    momento = V.Momento(momento)
    guardados = list(
        sesion.scalars(
            select(FactorExplicativo).where(FactorExplicativo.id_prediccion == prediccion.id_prediccion)
        )
    )
    try:
        factores: list[dict] | None = factores_comprensibles(
            sesion, alerta.codigo_estudiante, momento, guardados
        )
    except ExplicacionNoValida as error:
        registro.error(
            "No se puede mostrar la explicación de la alerta %s (predicción %s, modelo v%s %s): %s",
            alerta.id_alerta,
            prediccion.id_prediccion,
            version,
            momento.value,
            error,
        )
        factores = None
    return {
        "id_alerta": alerta.id_alerta,
        "codigo_estudiante": alerta.codigo_estudiante,
        "carrera": CARRERA.get(carrera, str(carrera)),
        "turno": "diurno" if turno_diurno else "nocturno",
        "probabilidad": float(prediccion.probabilidad),
        "nivel": prediccion.nivel,
        "fecha_calculo": prediccion.fecha,
        "version_modelo": version,
        "momento": momento.value,
        "vigente": prediccion.vigente,
        "factores": factores,
        "estado": alerta.estado,
        "fecha_creacion": alerta.fecha_creacion,
        "cambios_estado": historial_estados(sesion, alerta.id_alerta),  # HU-007, criterio 2
    }
