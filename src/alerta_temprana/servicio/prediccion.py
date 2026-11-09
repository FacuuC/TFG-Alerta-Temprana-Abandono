"""Servicio de predicción (HU-003, tareas 3.1 y 3.2; HU-004, tarea 4.2).

En una sola pasada, para los estudiantes de una carga:

1. arma el DataFrame con **solo** las variables del momento (19, 25 o 31) desde
   ESTUDIANTE y RENDIMIENTO_SEMESTRE: un cálculo de cierre_1s nunca ve datos `_s2`,
   aunque estén en la base;
2. calcula la probabilidad con el modelo habilitado del momento, el nivel de urgencia con
   los umbrales exactos de sus metadatos y los cinco factores que más pesan en la
   estimación (SHAP; no son causas del abandono);
3. guarda todo en una transacción: la predicción nueva queda vigente, la anterior pasa al
   historial (`vigente = false`) con sus factores, y las alertas se crean o actualizan
   según la decisión P3 (servicio/alertas.py).

La probabilidad se guarda redondeada a 4 decimales (NUMERIC(5,4)); el nivel se calcula
con la probabilidad sin redondear.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
from sqlalchemy import func, insert, select, update
from sqlalchemy.orm import Session

from alerta_temprana.datos import variables as V
from alerta_temprana.datos.carga import SEMESTRES_POR_MOMENTO
from alerta_temprana.db.tablas import (
    Estudiante,
    FactorExplicativo,
    Modelo,
    Prediccion,
    RendimientoSemestre,
)
from alerta_temprana.modelo.explicaciones import Factor, principales_factores, valores_shap_por_variable
from alerta_temprana.modelo.umbrales import NIVELES, clasificar
from alerta_temprana.servicio.alertas import actualizar_alertas
from alerta_temprana.servicio.modelos import ModeloCargado

CANTIDAD_FACTORES = 5
# Variables con decimales; el resto son códigos, binarias o cantidades enteras
_DECIMALES = {"tasa_desempleo", "tasa_inflacion", "variacion_pib", "nota_titulo_previo"} | {
    f"nota_promedio_s{s}" for s in (1, 2)
}


class DatosIncompletos(Exception):
    """Faltan datos de algún estudiante para el momento (por ejemplo, el rendimiento del 1.er semestre)."""


# --- 3.1: datos del momento --------------------------------------------------------------


def armar_datos(sesion: Session, codigos: list[str], momento: V.Momento | str) -> pd.DataFrame:
    """Variables del momento de cada estudiante, con índice `codigo_estudiante`.

    Las columnas son exactamente `VARIABLES_POR_MOMENTO[momento]`, en ese orden, con los
    tipos del entrenamiento (enteros y decimales, no Decimal ni booleanos).
    """
    momento = V.Momento(momento)
    variables = V.VARIABLES_POR_MOMENTO[momento]
    codigos = list(dict.fromkeys(codigos))
    columnas = [Estudiante.codigo_estudiante, *(getattr(Estudiante, v) for v in V.VARIABLES_INSCRIPCION)]
    filas = sesion.execute(select(*columnas).where(Estudiante.codigo_estudiante.in_(codigos))).all()
    datos = pd.DataFrame(filas, columns=["codigo_estudiante", *V.VARIABLES_INSCRIPCION]).set_index(
        "codigo_estudiante"
    )
    faltan = set(codigos) - set(datos.index)
    if faltan:
        raise DatosIncompletos(f"{len(faltan)} estudiantes de la carga no están en la base.")

    for semestre in SEMESTRES_POR_MOMENTO[momento]:
        campos = [getattr(RendimientoSemestre, c) for c in V.CAMPOS_RENDIMIENTO]
        filas = sesion.execute(
            select(RendimientoSemestre.codigo_estudiante, *campos).where(
                RendimientoSemestre.codigo_estudiante.in_(codigos), RendimientoSemestre.semestre == semestre
            )
        ).all()
        nombres = [f"{c}_s{semestre}" for c in V.CAMPOS_RENDIMIENTO]
        rendimiento = pd.DataFrame(filas, columns=["codigo_estudiante", *nombres]).set_index(
            "codigo_estudiante"
        )
        sin_datos = set(codigos) - set(rendimiento.index)
        if sin_datos:
            raise DatosIncompletos(
                f"{len(sin_datos)} estudiantes no tienen el rendimiento del semestre {semestre}, "
                f"necesario para el momento {V.ETIQUETA_MOMENTO[momento]}."
            )
        datos = datos.join(rendimiento)

    datos = datos.loc[codigos, variables]
    for variable in variables:
        datos[variable] = datos[variable].astype(float if variable in _DECIMALES else "int64")
    return datos


# --- 3.1: estimación ---------------------------------------------------------------------


def valor_como_texto(valor: float) -> str:
    """Valor de una variable para FACTOR_EXPLICATIVO.valor (VARCHAR(40)), sin formatear.

    Se guarda el valor tal cual («9500», «2», «13.9»); la ficha (HU-006) lo muestra con
    nombre y formato comprensibles (modelo/etiquetas.py), porque algunos textos no entran
    en 40 caracteres.
    """
    numero = float(valor)
    return str(int(numero)) if numero.is_integer() else repr(round(numero, 4))


@dataclass(frozen=True)
class Estimacion:
    codigo_estudiante: str
    probabilidad: float  # sin redondear
    nivel: str
    factores: list[tuple[Factor, str]]  # factor y valor del estudiante como texto


def estimar(modelo: ModeloCargado, datos: pd.DataFrame) -> list[Estimacion]:
    """Probabilidad, nivel y los cinco factores de cada fila de `datos` (función pura)."""
    if list(datos.columns) != V.VARIABLES_POR_MOMENTO[modelo.momento]:
        raise ValueError("Los datos no tienen exactamente las variables del momento del modelo.")
    if datos.empty:
        return []
    probabilidades = modelo.pipeline.predict_proba(datos)[:, 1]
    shap = valores_shap_por_variable(modelo.pipeline, datos)
    estimaciones = []
    for codigo, probabilidad in zip(datos.index, probabilidades, strict=True):
        factores = principales_factores(shap.loc[codigo], CANTIDAD_FACTORES)
        estimaciones.append(
            Estimacion(
                codigo_estudiante=str(codigo),
                probabilidad=float(probabilidad),
                nivel=clasificar(float(probabilidad), modelo.umbral_alto, modelo.umbral_medio),
                factores=[(f, valor_como_texto(datos.at[codigo, f.variable])) for f in factores],
            )
        )
    return estimaciones


# --- 3.2: guardado con historial ---------------------------------------------------------


@dataclass
class ResumenRecalculo:
    id_carga: int
    momento: str
    id_modelo: int
    version: str
    fecha: datetime
    estudiantes: int
    por_nivel: dict[str, int] = field(default_factory=dict)
    alertas_creadas: int = 0
    alertas_actualizadas: int = 0

    def como_dict(self) -> dict:
        datos = asdict(self)
        datos["fecha"] = self.fecha.isoformat()
        return datos


def _decimal(valor: float) -> Decimal:
    return Decimal(str(round(float(valor), 4)))


def guardar_estimaciones(
    sesion: Session, modelo: ModeloCargado, id_carga: int, estimaciones: list[Estimacion], fecha: datetime
) -> ResumenRecalculo:
    """Guarda las predicciones, sus factores y las alertas en una transacción.

    Si algo falla se revierte todo y las predicciones anteriores siguen vigentes.
    """
    codigos = [e.codigo_estudiante for e in estimaciones]
    try:
        if codigos:
            sesion.execute(
                update(Prediccion)
                .where(Prediccion.codigo_estudiante.in_(codigos), Prediccion.vigente)
                .values(vigente=False)
            )
            ids = sesion.execute(
                insert(Prediccion).returning(
                    Prediccion.id_prediccion, Prediccion.codigo_estudiante, sort_by_parameter_order=True
                ),
                [
                    {
                        "codigo_estudiante": e.codigo_estudiante,
                        "id_modelo": modelo.id_modelo,
                        "id_carga": id_carga,
                        "fecha": fecha,
                        "probabilidad": _decimal(e.probabilidad),
                        "nivel": e.nivel,
                        "vigente": True,
                    }
                    for e in estimaciones
                ],
            ).all()
            id_por_codigo = {codigo: id_prediccion for id_prediccion, codigo in ids}
            sesion.execute(
                insert(FactorExplicativo),
                [
                    {
                        "id_prediccion": id_por_codigo[e.codigo_estudiante],
                        "orden": factor.orden,
                        "variable": factor.variable,
                        "valor": valor,
                        "contribucion": _decimal(factor.contribucion),
                    }
                    for e in estimaciones
                    for factor, valor in e.factores
                ],
            )
            vigentes = {
                e.codigo_estudiante: (id_por_codigo[e.codigo_estudiante], e.nivel) for e in estimaciones
            }
            creadas, actualizadas = actualizar_alertas(sesion, vigentes, fecha)
        else:
            creadas = actualizadas = 0
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    cuenta = Counter(e.nivel for e in estimaciones)
    return ResumenRecalculo(
        id_carga=id_carga,
        momento=modelo.momento.value,
        id_modelo=modelo.id_modelo,
        version=modelo.version,
        fecha=fecha,
        estudiantes=len(estimaciones),
        por_nivel={n: cuenta.get(n, 0) for n in NIVELES},
        alertas_creadas=creadas,
        alertas_actualizadas=actualizadas,
    )


def recalcular(sesion: Session, modelo: ModeloCargado, id_carga: int, codigos: list[str]) -> ResumenRecalculo:
    """Recálculo completo de los estudiantes de una carga con el modelo de su momento."""
    datos = armar_datos(sesion, codigos, modelo.momento)
    estimaciones = estimar(modelo, datos)
    return guardar_estimaciones(sesion, modelo, id_carga, estimaciones, datetime.now(UTC))


# --- Criterio 4: última actualización ---------------------------------------------------


def ultima_actualizacion(sesion: Session) -> dict | None:
    """Fecha del último cálculo vigente y versión y momento del modelo que lo hizo, o None."""
    fila = sesion.execute(
        select(Prediccion.fecha, Modelo.version, Modelo.momento)
        .join(Modelo, Prediccion.id_modelo == Modelo.id_modelo)
        .where(Prediccion.vigente)
        .order_by(Prediccion.fecha.desc(), Prediccion.id_prediccion.desc())
        .limit(1)
    ).first()
    if fila is None:
        return None
    return {"fecha": fila.fecha, "version": fila.version, "momento": fila.momento}


def resumen_de_carga(sesion: Session, id_carga: int) -> dict | None:
    """Lo que quedó guardado del cálculo de una carga (sirve después de reiniciar la app)."""
    filas = sesion.execute(
        select(Modelo.version, Modelo.momento, Prediccion.nivel, func.count(), func.max(Prediccion.fecha))
        .join(Modelo, Prediccion.id_modelo == Modelo.id_modelo)
        .where(Prediccion.id_carga == id_carga)
        .group_by(Modelo.version, Modelo.momento, Prediccion.nivel)
    ).all()
    if not filas:
        return None
    por_nivel = {n: 0 for n in NIVELES}
    for _, _, nivel, cantidad, _ in filas:
        por_nivel[nivel] = cantidad
    return {
        "version": filas[0].version,
        "momento": filas[0].momento,
        "estudiantes": sum(por_nivel.values()),
        "por_nivel": por_nivel,
        "fecha": max(f[4] for f in filas),
    }
