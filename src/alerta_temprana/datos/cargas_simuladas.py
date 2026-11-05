"""Archivos de carga simulados: exportación de SIU-Guaraní (decisión P2; HU-001).

El conjunto de datos es histórico, así que la actualización por momentos se simula:
los estudiantes del conjunto de **prueba** se exportan en tres archivos sucesivos, uno
por momento, y cada uno es una foto completa hasta ese momento.

- Separados por «;», UTF-8, punto decimal, nombres de columnas de la plataforma.
- Identificadores **sintéticos** que la plataforma descarta: `legajo` (el mismo de las
  fichas del cuestionario, `legajo_sintetico`), `documento` y `apellido_nombre`.
  Son constantes entre los tres archivos: el mismo estudiante recibe el mismo código.
- Las 5 variables excluidas, para demostrar que se descartan en la carga.
- **Sin la situación final:** el dataset se lee sin la columna Target, así que las
  etiquetas de prueba nunca se leen.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from alerta_temprana.datos import variables as V
from alerta_temprana.datos.seudonimizacion import legajo_sintetico
from alerta_temprana.modelo.preparacion import cargar_particion, cargar_variables_sin_objetivo

IDENTIFICATORIAS = ["legajo", "documento", "apellido_nombre"]


def nombre_archivo(momento: V.Momento) -> str:
    return f"exportacion_{momento.value}.csv"


def columnas_exportacion(momento: V.Momento) -> list[str]:
    del_momento = V.VARIABLES_POR_MOMENTO[momento]
    semestres = del_momento[len(V.VARIABLES_INSCRIPCION) :]
    return [*IDENTIFICATORIAS, *V.VARIABLES_INSCRIPCION, *V.VARIABLES_EXCLUIDAS, *semestres]


def estudiantes_de_prueba(ruta_dataset: Path, ruta_particion: Path) -> pd.DataFrame:
    """Variables (sin Target) de los estudiantes de prueba, con sus identificadores sintéticos."""
    df = cargar_variables_sin_objetivo(ruta_dataset)
    assert V.OBJETIVO not in df.columns
    particion = cargar_particion(ruta_particion)
    prueba = df.loc[sorted(particion[particion == "prueba"].index)].copy()
    numero = range(1, len(prueba) + 1)
    prueba.insert(0, "legajo", [legajo_sintetico(i) for i in prueba.index])
    prueba.insert(1, "documento", [str(90_000_000 + int(i)) for i in prueba.index])
    prueba.insert(2, "apellido_nombre", [f"Estudiante {n:04d}" for n in numero])
    return prueba


def generar_cargas(ruta_dataset: Path, ruta_particion: Path, carpeta: Path) -> dict[V.Momento, Path]:
    """Escribe los tres archivos en `carpeta` y devuelve sus rutas."""
    prueba = estudiantes_de_prueba(ruta_dataset, ruta_particion)
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas: dict[V.Momento, Path] = {}
    for momento in V.Momento:
        ruta = carpeta / nombre_archivo(momento)
        prueba[columnas_exportacion(momento)].to_csv(ruta, sep=";", index=False, encoding="utf-8")
        rutas[momento] = ruta
    return rutas
