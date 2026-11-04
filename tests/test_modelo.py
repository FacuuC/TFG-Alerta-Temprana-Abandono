"""Pruebas de HU-002 (camino rápido), 4.1, 6.1 y 6.2."""

import numpy as np
import pandas as pd
import pytest

from alerta_temprana.datos import variables as V
from alerta_temprana.datos.seudonimizacion import codigo_estudiante, legajo_sintetico
from alerta_temprana.modelo import preparacion as P
from alerta_temprana.modelo import umbrales as U
from alerta_temprana.modelo.etiquetas import CODIGOS, NOMBRES, texto_factor, texto_ocupacion, texto_valor
from alerta_temprana.modelo.explicaciones import principales_factores

# --- Umbrales y niveles (HU-004, criterios 1 y 2) ----------------------------------


def test_umbral_alto_respeta_la_capacidad():
    p = np.linspace(0, 1, 1000)
    t = U.umbral_alto(p, 0.15)
    assert np.mean(p >= t) <= 0.15
    # el siguiente valor más bajo ya la superaría
    assert np.mean(p >= p[p < t].max()) > 0.15


def test_umbral_medio_detecta_al_menos_el_80_por_ciento():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 500)
    p = np.clip(0.3 * y + rng.random(500) * 0.7, 0, 1)
    t = U.umbral_medio(p, y, 0.80)
    assert np.mean(p[y == 1] >= t) >= 0.80


@pytest.mark.parametrize(
    ("probabilidad", "nivel"),
    [(0.9, "alto"), (0.8, "alto"), (0.79, "medio"), (0.5, "medio"), (0.49, "bajo"), (0.0, "bajo")],
)
def test_clasificar_bordes_y_nivel_unico(probabilidad, nivel):
    assert U.clasificar(probabilidad, alto=0.8, medio=0.5) == nivel


# --- Seudonimización (HU-001, criterio 4; decisión P1) --------------------------------


def test_codigo_seudonimizado_formato_y_estabilidad():
    codigo = codigo_estudiante("L00001", "clave")
    assert len(codigo) == 12 and codigo.startswith("EST-")
    assert codigo == codigo_estudiante("L00001", "clave")
    assert codigo != codigo_estudiante("L00001", "otra-clave")
    assert legajo_sintetico(0) == "L00001"


# --- Etiquetas (HU-006, criterio 3) ---------------------------------------------------


def test_todas_las_variables_tienen_nombre():
    assert set(NOMBRES) == set(V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_2S])


def test_texto_de_materias_aprobadas_como_en_el_documento():
    fila = {"materias_aprobadas_s1": 2, "materias_inscriptas_s1": 6}
    assert texto_factor("materias_aprobadas_s1", fila) == "Materias aprobadas en el 1.er semestre: 2 de 6"


def test_ocupacion_por_gran_grupo():
    assert texto_ocupacion(0) == "estudiante"
    assert texto_ocupacion(122) == "profesionales científicos e intelectuales"
    assert texto_ocupacion(194) == "ocupaciones elementales"


# --- Con el dataset -------------------------------------------------------------------


@pytest.fixture(scope="module")
def df(request):
    from tests.conftest import RUTA_DATASET

    if not RUTA_DATASET.exists():
        pytest.skip("Falta el dataset")
    return P.cargar_dataset(RUTA_DATASET)


@pytest.mark.datos
def test_objetivo_binario(df):
    assert df.loc[df[V.OBJETIVO] == "abandono", P.OBJETIVO_BINARIO].eq(1).all()
    assert df.loc[df[V.OBJETIVO].isin(["cursando", "graduado"]), P.OBJETIVO_BINARIO].eq(0).all()


@pytest.mark.datos
def test_particion_60_20_20_estratificada_y_reproducible(df):
    a = P.crear_particion(df, 42)
    b = P.crear_particion(df, 42)
    assert a.equals(b)
    proporciones = a.value_counts(normalize=True)
    assert abs(proporciones["entrenamiento"] - 0.60) < 0.001
    assert abs(proporciones["validacion"] - 0.20) < 0.001
    tasa = df.groupby(a)[P.OBJETIVO_BINARIO].mean()
    assert tasa.max() - tasa.min() < 0.01


@pytest.mark.datos
def test_cada_momento_usa_solo_sus_variables(df):
    for momento in V.Momento:
        pre = P.construir_preprocesador(momento).fit(df)
        usadas = set(P.variable_de_cada_columna(pre))
        assert usadas == set(V.VARIABLES_POR_MOMENTO[momento])


@pytest.mark.datos
def test_todos_los_codigos_del_archivo_tienen_etiqueta(df):
    for variable, codigos in CODIGOS.items():
        faltantes = set(df[variable].astype(int)) - set(codigos)
        assert not faltantes, f"{variable}: {faltantes}"
    for variable in ("ocupacion_madre", "ocupacion_padre"):
        for codigo in df[variable].astype(int).unique():
            texto_ocupacion(int(codigo))
    fila = df.iloc[0]
    for variable in NOMBRES:
        assert "código" not in texto_valor(variable, fila)


def test_principales_factores_ordenados_por_peso():
    fila = pd.Series({"a": 0.1, "b": -0.9, "c": 0.5, "d": 0.0, "e": -0.2, "f": 0.05})
    factores = principales_factores(fila, 5)
    assert [f.variable for f in factores] == ["b", "c", "e", "a", "f"]
    assert not factores[0].aumenta_riesgo and factores[1].aumenta_riesgo


# --- Candado del conjunto de prueba (regla 1 de CLAUDE.md) -----------------------------


def test_prueba_sin_objetivo_por_defecto(df):
    conjunto = P.crear_particion(df, 42)
    prueba = P.dividir(df, conjunto, "prueba")
    assert V.OBJETIVO not in prueba.columns and P.OBJETIVO_BINARIO not in prueba.columns
    assert P.OBJETIVO_BINARIO in P.dividir(df, conjunto, "validacion").columns


def test_objetivo_de_prueba_exige_confirmacion_humana(df):
    from alerta_temprana.modelo.candado_prueba import UsoDePruebaNoAutorizado

    conjunto = P.crear_particion(df, 42)
    with pytest.raises(UsoDePruebaNoAutorizado):  # pytest no corre en una terminal interactiva
        P.dividir(df, conjunto, "prueba", con_objetivo=True)


def test_registro_de_usos(tmp_path):
    from alerta_temprana.modelo.candado_prueba import registrar_uso, usos_registrados

    registro = tmp_path / "uso.json"
    assert usos_registrados(registro) == []
    registrar_uso({"modelos": ["cierre_1s/v1.0"]}, registro)
    assert usos_registrados(registro)[0]["modelos"] == ["cierre_1s/v1.0"]
