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


# --- Criterio 2: un modelo por momento, solo con sus variables -------------------------


def _modelo(momento: V.Momento):
    from alerta_temprana.modelo.persistencia import cargar_modelo

    if not (RAIZ / "modelos" / momento.value / "v1.0" / "pipeline.joblib").exists():
        pytest.skip(f"Falta entrenar: python scripts/entrenar.py --momento {momento.value}")
    return cargar_modelo(RAIZ / "modelos", momento, "1.0")


@pytest.mark.datos
@pytest.mark.parametrize("momento", list(V.Momento))
def test_criterio_2_modelo_de_cada_momento_usa_solo_sus_variables(momento):
    pipeline, meta = _modelo(momento)
    esperadas = V.VARIABLES_POR_MOMENTO[momento]
    assert meta["momento"] == momento.value
    assert meta["variables"] == esperadas
    assert list(pipeline.feature_names_in_) == esperadas
    usadas = set(P.variable_de_cada_columna(pipeline.named_steps["preprocesador"]))
    assert usadas == set(esperadas)


@pytest.mark.datos
def test_criterio_2_inscripcion_no_usa_variables_de_semestre(df):
    pipeline, _ = _modelo(V.Momento.INSCRIPCION)
    filas = df.head(50)
    base = pipeline.predict_proba(filas[V.VARIABLES_POR_MOMENTO[V.Momento.INSCRIPCION]])[:, 1]
    con_semestres = filas[V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_2S]].copy()
    con_semestres[list(V.VARIABLES_SEMESTRE_1) + list(V.VARIABLES_SEMESTRE_2)] = 99  # valores absurdos
    try:
        alterada = pipeline.predict_proba(con_semestres)[:, 1]
    except ValueError:
        return  # falla: tampoco las usa
    np.testing.assert_array_equal(base, alterada)  # las ignora


# --- Criterio 5 (parte de entrenamiento): versión, fecha, métricas y umbrales -------------


@pytest.mark.datos
@pytest.mark.parametrize("momento", list(V.Momento))
def test_criterio_5_metadatos_de_entrenamiento(momento):
    from datetime import datetime

    _, meta = _modelo(momento)
    assert meta["version"] == "1.0"
    datetime.fromisoformat(meta["fecha"])
    for clave in ("auc_roc", "auc_roc_referencia", "precision_alerta", "sensibilidad_alerta"):
        assert 0 <= meta["validacion"][clave] <= 1
    assert 0 < meta["umbral_medio"] <= meta["umbral_alto"] < 1
    assert isinstance(meta["habilitado"], bool)


@pytest.mark.datos
def test_modelo_congelado_reproduce_las_fichas_del_cuestionario(df):
    """Regla 11: el modelo de cierre_1s v1.0 que se carga es el que generó las fichas.

    Usa los estudiantes de prueba SIN su situación final (solo predice, como el script de fichas).
    """
    casos_csv = RAIZ / "reportes" / "cuestionario" / "casos.csv"
    if not casos_csv.exists() or not RUTA_PARTICION.exists():
        pytest.skip("Faltan las fichas o la partición")
    pipeline, _ = _modelo(V.Momento.CIERRE_1S)
    casos = pd.read_csv(casos_csv)
    prueba = P.dividir(df, P.cargar_particion(RUTA_PARTICION), "prueba")
    assert P.OBJETIVO_BINARIO not in prueba.columns
    variables = V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_1S]
    probabilidades = pipeline.predict_proba(prueba.loc[casos["indice_original"], variables])[:, 1]
    np.testing.assert_allclose(probabilidades.round(4), casos["probabilidad"], atol=1e-4)


def test_carga_portable_no_deja_cambios_globales():
    import xgboost.core as xgb_core

    from alerta_temprana.modelo.persistencia import _carga_portable_xgboost

    original = xgb_core.Booster.__setstate__
    with _carga_portable_xgboost():
        assert xgb_core.Booster.__setstate__ is not original
    assert xgb_core.Booster.__setstate__ is original
