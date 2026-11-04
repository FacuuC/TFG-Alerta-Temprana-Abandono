"""Preparación de los datos (CRISP-DM, fase 3; tarea 2.2).

- Lectura del archivo de UCI con los nombres de la plataforma.
- Variable objetivo binaria: abandono = 1; graduado o sigue cursando = 0.
- Partición estratificada 60/20/20 con semilla fija, la misma para los tres momentos,
  guardada en disco para que todos los scripts usen exactamente la misma.
- Preprocesador por momento (one-hot, estandarización), que se ajusta solo con
  entrenamiento porque vive dentro del Pipeline del modelo.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from alerta_temprana.datos import variables as V

OBJETIVO_BINARIO = "abandono"
CONJUNTOS = ("entrenamiento", "validacion", "prueba")


def cargar_dataset(ruta_csv: Path) -> pd.DataFrame:
    """Lee el CSV de UCI, renombra las columnas y agrega la variable objetivo binaria.

    El índice del DataFrame es la posición original de cada registro en el archivo
    (`indice_original`), que es la clave de la partición guardada.
    """
    df = pd.read_csv(ruta_csv, sep=";", encoding="utf-8-sig")
    df = df.rename(columns=V.renombrar_columnas(list(df.columns)))
    df[V.OBJETIVO] = df[V.OBJETIVO].map(V.SITUACION_FINAL)
    if df[V.OBJETIVO].isna().any():
        raise ValueError("La columna Target tiene valores distintos de Dropout, Enrolled o Graduate")
    df[OBJETIVO_BINARIO] = (df[V.OBJETIVO] == V.CLASE_POSITIVA).astype(int)
    df.index.name = "indice_original"
    return df


def crear_particion(df: pd.DataFrame, semilla: int) -> pd.Series:
    """Partición estratificada 60/20/20 por la variable binaria. Devuelve el conjunto de cada registro."""
    indices = df.index.to_numpy()
    y = df[OBJETIVO_BINARIO].to_numpy()
    idx_ent, idx_resto, _, y_resto = train_test_split(
        indices, y, train_size=0.60, stratify=y, random_state=semilla
    )
    idx_val, idx_pru = train_test_split(idx_resto, train_size=0.50, stratify=y_resto, random_state=semilla)
    conjunto = pd.Series("", index=df.index, name="conjunto")
    conjunto.loc[idx_ent] = "entrenamiento"
    conjunto.loc[idx_val] = "validacion"
    conjunto.loc[idx_pru] = "prueba"
    return conjunto


def guardar_particion(conjunto: pd.Series, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conjunto.to_frame().to_csv(ruta, index_label="indice_original")


def cargar_particion(ruta: Path) -> pd.Series:
    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta}. Generala con: python scripts/preparar_particion.py")
    return pd.read_csv(ruta, index_col="indice_original")["conjunto"]


def dividir(df: pd.DataFrame, conjunto: pd.Series, nombre: str) -> pd.DataFrame:
    """Filas de un conjunto («entrenamiento», «validacion» o «prueba»)."""
    if nombre not in CONJUNTOS:
        raise ValueError(f"Conjunto desconocido: {nombre}")
    return df.loc[conjunto[conjunto == nombre].index]


def columnas_del_momento(momento: V.Momento) -> dict[str, list[str]]:
    """Variables de un momento separadas por tipo de transformación."""
    variables = V.VARIABLES_POR_MOMENTO[momento]
    categoricas = [v for v in variables if v in V.CATEGORICAS]
    binarias = [v for v in variables if v in V.BINARIAS]
    numericas = [v for v in variables if v not in categoricas and v not in binarias]
    return {"categoricas": categoricas, "numericas": numericas, "binarias": binarias}


def construir_preprocesador(momento: V.Momento) -> ColumnTransformer:
    """One-hot para las categóricas codificadas, estandarización para las numéricas y
    binarias sin cambios. Solo usa las variables del momento: el resto se descarta."""
    cols = columnas_del_momento(momento)
    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cols["categoricas"]),
            ("num", StandardScaler(), cols["numericas"]),
            ("bin", "passthrough", cols["binarias"]),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def variable_de_cada_columna(preprocesador: ColumnTransformer) -> list[str]:
    """Para cada columna transformada, la variable original de la que sale.

    Sirve para sumar los valores SHAP de las columnas one-hot de una misma variable.
    El preprocesador tiene que estar ajustado.
    """
    origen: list[str] = []
    for nombre, transformador, columnas in preprocesador.transformers_:
        if nombre == "cat":
            for variable, categorias in zip(columnas, transformador.categories_, strict=True):
                origen.extend([variable] * len(categorias))
        elif nombre in ("num", "bin"):
            origen.extend(columnas)
    return origen
