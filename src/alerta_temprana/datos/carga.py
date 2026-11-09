"""Procesamiento de un archivo de carga, sin tocar la base (HU-001; tareas 1.3 y 1.4).

Lee el archivo, valida la estructura (criterio 2) y cada registro (criterio 3),
reemplaza el legajo por el código seudonimizado y descarta todo lo que el modelo del
momento no usa (criterio 4): identificatorias, excluidas, variables de momentos
posteriores y cualquier otra columna. Devuelve las filas listas para ESTUDIANTE y
RENDIMIENTO_SEMESTRE. El guardado está en servicio/carga.py.

El formato aceptado (separado por «;», UTF-8, punto decimal, nombres de columnas de la
plataforma) es el de los archivos simulados de `data/cargas/` (decisión P2); el código
seudonimizado es el de la decisión P1 (datos/seudonimizacion.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from alerta_temprana.datos import variables as V
from alerta_temprana.datos.seudonimizacion import ColisionDeCodigos, codigos_sin_colisiones
from alerta_temprana.datos.validacion import (
    COLUMNA_LEGAJO,
    COLUMNAS_IDENTIFICATORIAS,
    CargaRechazada,
    ErrorRegistro,
    columnas_obligatorias,
    leer_archivo,
    validar_estructura,
    validar_registros,
)

# Semestres cuyo rendimiento se incorpora en cada momento
SEMESTRES_POR_MOMENTO: dict[V.Momento, tuple[int, ...]] = {
    V.Momento.INSCRIPCION: (),
    V.Momento.CIERRE_1S: (1,),
    V.Momento.CIERRE_2S: (1, 2),
}


@dataclass
class ArchivoProcesado:
    momento: V.Momento
    estudiantes: pd.DataFrame  # codigo_estudiante + 19 variables de la inscripción
    rendimientos: pd.DataFrame  # codigo_estudiante, semestre + 6 campos de RENDIMIENTO_SEMESTRE
    errores: list[ErrorRegistro]
    registros_validos: int
    registros_rechazados: int
    columnas_descartadas: dict[str, list[str]] = field(default_factory=dict)


def clasificar_descartadas(columnas: list[str], momento: V.Momento) -> dict[str, list[str]]:
    """Columnas del archivo que no se guardan, agrupadas para informarlas.

    El legajo se usa para calcular el código y después se descarta.
    """
    obligatorias = set(columnas_obligatorias(momento)) - {COLUMNA_LEGAJO}
    descartadas = [c for c in columnas if c not in obligatorias]
    return {
        "identificatorias": [c for c in descartadas if c in COLUMNAS_IDENTIFICATORIAS],
        "excluidas": [c for c in descartadas if c in V.VARIABLES_EXCLUIDAS],
        "otras": [
            c for c in descartadas if c not in COLUMNAS_IDENTIFICATORIAS and c not in V.VARIABLES_EXCLUIDAS
        ],
    }


def _tabla_rendimientos(validos: pd.DataFrame, momento: V.Momento) -> pd.DataFrame:
    partes = []
    for semestre in SEMESTRES_POR_MOMENTO[momento]:
        columnas = {f"{campo}_s{semestre}": campo for campo in V.CAMPOS_RENDIMIENTO}
        parte = validos[["codigo_estudiante", *columnas]].rename(columns=columnas)
        parte.insert(1, "semestre", semestre)
        partes.append(parte)
    if not partes:
        return pd.DataFrame(columns=["codigo_estudiante", "semestre", *V.CAMPOS_RENDIMIENTO])
    return pd.concat(partes, ignore_index=True)


def procesar_archivo(contenido: bytes, momento: V.Momento, clave: str) -> ArchivoProcesado:
    """Lanza CargaRechazada si hay que rechazar la carga completa."""
    momento = V.Momento(momento)
    datos = leer_archivo(contenido)
    validar_estructura(datos, momento)

    legajos = datos[COLUMNA_LEGAJO]
    try:
        por_legajo = codigos_sin_colisiones(legajos[legajos != ""], clave)
    except ColisionDeCodigos as error:
        raise CargaRechazada(str(error)) from error
    codigos = legajos.map(por_legajo)  # None donde falta el legajo
    codigos = codigos.astype(object).where(codigos.notna(), None)

    validacion = validar_registros(datos, momento, codigos)
    validos = validacion.validos  # solo código y variables del momento: el legajo ya no está
    estudiantes = validos[["codigo_estudiante", *V.VARIABLES_INSCRIPCION]].reset_index(drop=True)
    return ArchivoProcesado(
        momento=momento,
        estudiantes=estudiantes,
        rendimientos=_tabla_rendimientos(validos, momento),
        errores=validacion.errores,
        registros_validos=len(validos),
        registros_rechazados=len(validacion.filas_rechazadas),
        columnas_descartadas=clasificar_descartadas(list(datos.columns), momento),
    )


def informe_errores_csv(errores: list[ErrorRegistro]) -> bytes:
    """Informe de errores descargable: fila, código seudonimizado (nunca el legajo),
    columna y motivo. Separado por «;» y en UTF-8 con BOM para que Excel muestre los acentos."""
    tabla = pd.DataFrame(
        [(e.fila, e.codigo_estudiante or "", e.columna, e.motivo) for e in errores],
        columns=["fila", "codigo_estudiante", "columna", "motivo"],
    )
    return tabla.to_csv(sep=";", index=False).encode("utf-8-sig")
