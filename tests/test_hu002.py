"""Pruebas de HU-002 (criterios de aceptación 1 a 5) y del uso único del conjunto de prueba.

Las de camino rápido (umbrales, etiquetas, candado) están en test_modelo.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alerta_temprana import formato as F
from alerta_temprana.config import RAIZ
from alerta_temprana.datos import exploracion as X
from alerta_temprana.datos import variables as V
from alerta_temprana.modelo import preparacion as P

RUTA_DATASET = RAIZ / "data" / "raw" / "data.csv"
RUTA_PARTICION = RAIZ / "data" / "procesados" / "particion.csv"


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    if not RUTA_DATASET.exists():
        pytest.skip("Falta el dataset: python scripts/descargar_datos.py")
    return P.cargar_dataset(RUTA_DATASET)


@pytest.fixture(scope="module")
def conjunto(df) -> pd.Series:
    return P.crear_particion(df, 42)


# --- Formato argentino ----------------------------------------------------------------


def test_formato_argentino():
    assert F.decimal(0.88784) == "0,8878"
    assert F.porcentaje(0.149) == "14,9 %"
    assert F.entero(2654) == "2.654"
    assert F.decimal(float("nan")) == "—"


def test_tramo_de_edad_con_los_cortes_del_documento():
    assert [V.tramo_edad(e) for e in (17, 20, 21, 25, 26, 70)] == [
        "hasta 20", "hasta 20", "21 a 25", "21 a 25", "más de 25", "más de 25"
    ]


# --- Tarea 2.1: el análisis exploratorio no mira validación ni prueba ------------------


def test_exploracion_usa_solo_entrenamiento():
    datos = pd.DataFrame({"x": range(6), "abandono": [0, 1] * 3})
    conjunto = pd.Series(["entrenamiento", "validacion", "prueba"] * 2)
    elegidos = X.datos_para_explorar(datos, conjunto)
    assert set(conjunto.loc[elegidos.index]) == {"entrenamiento"}
    assert len(elegidos) == 2


def test_categorias_poco_frecuentes():
    datos = pd.DataFrame({"carrera": [1] * 12 + [2] * 3 + [3]})
    raras = X.categorias_poco_frecuentes(datos, ["carrera"], minimo=10)
    assert raras[["codigo", "casos"]].values.tolist() == [[2, 3], [3, 1]]


def test_tasa_de_abandono_por_variable():
    datos = pd.DataFrame({"becario": [0, 0, 1, 1], "abandono": [1, 0, 0, 0]})
    tabla = X.tasa_abandono_por(datos, "becario")
    assert tabla.loc[0, "tasa"] == 0.5 and tabla.loc[1, "tasa"] == 0.0


def test_disponibilidad_por_momento_19_25_31():
    tabla = X.disponibilidad_por_momento()
    assert tabla.sum().to_dict() == {"inscripcion": 19, "cierre_1s": 25, "cierre_2s": 31}
    assert not tabla.loc["materias_aprobadas_s2", "cierre_1s"]


def test_informe_exploratorio_existe_y_no_usa_prueba():
    informe = RAIZ / "reportes" / "informe_exploratorio.md"
    if not informe.exists():
        pytest.skip("Falta generar: python scripts/explorar_datos.py")
    texto = informe.read_text(encoding="utf-8")
    for seccion in ("Variable objetivo y desbalance", "Correlaciones", "Variables por momento"):
        assert seccion in texto
    assert "solo con" in texto and "entrenamiento" in texto
    for prohibido in ("factores que explican", "ingesta", "anonimizado"):
        assert prohibido not in texto.lower()


# --- Criterio 1: objetivo binario y partición 60/20/20 estratificada -------------------


@pytest.mark.datos
def test_criterio_1_tamanos_a_un_registro(df, conjunto):
    total = len(df)
    tamanos = conjunto.value_counts()
    for nombre, fraccion in (("entrenamiento", 0.6), ("validacion", 0.2), ("prueba", 0.2)):
        assert abs(tamanos[nombre] - fraccion * total) <= 1, nombre


@pytest.mark.datos
def test_criterio_1_abandono_igual_en_los_tres_conjuntos(df, conjunto):
    tasa = df.groupby(conjunto)[P.OBJETIVO_BINARIO].mean()
    assert tasa.max() - tasa.min() <= 0.01


@pytest.mark.datos
def test_criterio_1_cursando_y_graduado_son_cero(df):
    assert set(df.loc[df[V.OBJETIVO] == "cursando", P.OBJETIVO_BINARIO]) == {0}
    assert set(df.loc[df[V.OBJETIVO] == "graduado", P.OBJETIVO_BINARIO]) == {0}
    assert set(df.loc[df[V.OBJETIVO] == "abandono", P.OBJETIVO_BINARIO]) == {1}


@pytest.mark.datos
def test_criterio_1_particion_guardada_es_la_de_la_semilla(df, conjunto):
    if not RUTA_PARTICION.exists():
        pytest.skip("Falta generar: python scripts/preparar_particion.py")
    guardada = P.cargar_particion(RUTA_PARTICION)
    assert guardada.sort_index().equals(conjunto.sort_index())
    assert np.array_equal(P.crear_particion(df, 42).to_numpy(), conjunto.to_numpy())
