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
from alerta_temprana.modelo import evaluacion as E
from alerta_temprana.modelo import preparacion as P
from alerta_temprana.modelo.informe_evaluacion import FRASE_ELECCION, TITULO_ENSAYO, armar_informe

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


# --- Umbrales guardados = regla del documento en validación (pedido el 04/11) -----------


@pytest.fixture(scope="module")
def validacion(df) -> pd.DataFrame:
    if not RUTA_PARTICION.exists():
        pytest.skip("Falta generar: python scripts/preparar_particion.py")
    return P.dividir(df, P.cargar_particion(RUTA_PARTICION), "validacion")


@pytest.mark.datos
@pytest.mark.parametrize("momento", list(V.Momento))
def test_umbrales_guardados_cumplen_la_regla_en_validacion(momento, validacion):
    """Los umbrales de metadatos.json, aplicados a validación: alto <= 15 % y alto + medio >= 80 %."""
    from alerta_temprana.modelo.umbrales import comprobar

    pipeline, meta = _modelo(momento)
    p = pipeline.predict_proba(validacion[V.VARIABLES_POR_MOMENTO[momento]])[:, 1]
    control = comprobar(p, validacion[P.OBJETIVO_BINARIO].to_numpy(), meta["umbral_alto"], meta["umbral_medio"])
    assert control["proporcion_alto"] <= meta["capacidad_tutorias"]
    assert control["deteccion_alto_medio"] >= meta["deteccion_minima"]


@pytest.mark.datos
def test_niveles_de_las_fichas_con_los_umbrales_guardados(df):
    from alerta_temprana.modelo.umbrales import clasificar_vector

    casos_csv = RAIZ / "reportes" / "cuestionario" / "casos.csv"
    if not casos_csv.exists() or not RUTA_PARTICION.exists():
        pytest.skip("Faltan las fichas o la partición")
    pipeline, meta = _modelo(V.Momento.CIERRE_1S)
    casos = pd.read_csv(casos_csv)
    prueba = P.dividir(df, P.cargar_particion(RUTA_PARTICION), "prueba")
    p = pipeline.predict_proba(prueba.loc[casos["indice_original"], V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_1S]])[:, 1]
    assert list(clasificar_vector(p, meta["umbral_alto"], meta["umbral_medio"])) == list(casos["nivel"])


# --- Evaluación final: reglas con datos simulados (criterios 3 y 4) ---------------------



@pytest.mark.parametrize(
    ("momento", "auc", "habilitado"),
    [
        (V.Momento.CIERRE_1S, 0.80, False),
        (V.Momento.CIERRE_1S, 0.7999, False),
        (V.Momento.CIERRE_1S, 0.8001, True),
        (V.Momento.INSCRIPCION, 0.60, True),
        (V.Momento.CIERRE_2S, 0.55, True),
    ],
)
def test_criterio_3_regla_de_habilitacion(momento, auc, habilitado):
    resultado, motivo = E.decidir_habilitacion(momento, auc)
    assert resultado is habilitado
    assert "0,8" in motivo if momento is V.Momento.CIERRE_1S else "informado" in motivo


def test_criterio_3_metricas_de_la_alerta():
    y = np.array([1, 1, 1, 0, 0, 0, 0, 0])
    p = np.array([0.9, 0.6, 0.2, 0.7, 0.3, 0.1, 0.1, 0.05])
    m = E.metricas_alerta(y, p, umbral_medio=0.5)
    assert (m["verdaderos_positivos"], m["falsos_negativos"], m["falsos_positivos"]) == (2, 1, 1)
    assert m["precision_alerta"] == pytest.approx(2 / 3)
    assert m["sensibilidad_alerta"] == pytest.approx(2 / 3)
    assert 0.5 < m["auc_roc"] <= 1


def _datos_simulados(n: int = 400, semilla: int = 0) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(semilla)
    datos = pd.DataFrame(
        {
            "genero": rng.integers(0, 2, n),
            "edad_ingreso": rng.choice([18, 19, 22, 24, 30, 40], n),
            "becario": rng.integers(0, 2, n),
            V.OBJETIVO: rng.choice(["abandono", "cursando", "graduado"], n, p=[0.32, 0.18, 0.5]),
        }
    )
    y = (datos[V.OBJETIVO] == "abandono").astype(int).to_numpy()
    p = np.clip(0.35 * y + 0.65 * rng.random(n), 0, 1)
    return datos, y, p


def test_criterio_4_metricas_por_subgrupo():
    datos, y, p = _datos_simulados()
    tabla = E.metricas_por_subgrupo(datos, y, p, 0.5)
    assert tabla.groupby("subgrupo").size().to_dict() == {"Género": 2, "Edad de ingreso": 3, "Becario": 2}
    assert tabla[["auc_roc", "sensibilidad_alerta", "precision_alerta"]].notna().all().all()
    assert tabla.groupby("subgrupo")["n"].sum().eq(len(datos)).all()


def test_criterio_4_subgrupo_de_una_sola_clase_no_rompe():
    datos = pd.DataFrame({"genero": [0, 0, 1, 1], "edad_ingreso": [18, 18, 30, 30], "becario": [1, 1, 0, 0]})
    tabla = E.metricas_por_subgrupo(datos, np.array([0, 0, 1, 0]), np.array([0.1, 0.2, 0.9, 0.3]), 0.5)
    femenino = tabla[(tabla.subgrupo == "Género") & (tabla.grupo == "femenino")].iloc[0]
    assert np.isnan(femenino.auc_roc)


def test_criterio_4_auc_sin_cursando_excluye_esas_filas():
    situacion = np.array(["abandono", "cursando", "graduado", "abandono", "cursando", "graduado"])
    y = (situacion == "abandono").astype(int)
    p = np.array([0.9, 0.95, 0.1, 0.8, 0.85, 0.2])  # los que siguen cursando parecen abandonos
    r = E.auc_sin_cursando(situacion, y, p)
    assert r["n_sin_cursando"] == 4 and r["n_con_cursando"] == 6
    assert r["auc_roc_sin_cursando"] == 1.0 and r["auc_roc_con_cursando"] < 1.0


def test_revision_demografica_peso_alto():
    importancia = pd.Series({"materias_aprobadas_s1": 1.2, "edad_ingreso": 0.4, "carrera": 0.3, "nota_promedio_s1": 0.2,
                             "becario": 0.15, "genero": 0.1, "nacionalidad": 0.01})
    tabla = E.revision_demografica(importancia)
    assert tabla.set_index("variable").loc["edad_ingreso", "peso_alto"]
    assert not tabla.set_index("variable").loc["genero", "peso_alto"]


# --- Uso único de la prueba y alternativa reproducible -----------------------------------


def test_guarda_deja_seguir_la_primera_vez():
    E.verificar_uso_previo([], False, [], repetir=False, motivo=None)


@pytest.mark.parametrize(
    ("usos", "informe", "con_prueba"),
    [([{"fecha": "x"}], False, []), ([], True, []), ([], False, ["cierre_1s/v1.0"])],
)
def test_guarda_se_niega_a_repetir_sin_permiso(usos, informe, con_prueba):
    with pytest.raises(E.UsoRepetidoDePrueba):
        E.verificar_uso_previo(usos, informe, con_prueba, repetir=False, motivo=None)
    with pytest.raises(E.UsoRepetidoDePrueba):  # --repetir sin motivo
        E.verificar_uso_previo(usos, informe, con_prueba, repetir=True, motivo="  ")
    E.verificar_uso_previo(usos, informe, con_prueba, repetir=True, motivo="falló la escritura del informe")


def test_tolerancia_de_la_alternativa():
    assert E.comprobar_alternativa(0.8871, 0.8875) == pytest.approx(0.0004)
    with pytest.raises(E.AlternativaNoReproducible):
        E.comprobar_alternativa(0.8871, 0.8877)


def test_alternativa_de_cierre_1s_congelado():
    meta = {"algoritmo": "xgboost", "validacion": {"auc_roc_referencia": 0.8871}}
    assert E.describir_alternativa(meta) == {
        "algoritmo": "regresion_logistica", "hiperparametros": {"class_weight": "balanced"}, "auc_roc_validacion": 0.8871
    }
    nuevo = {"algoritmo": "regresion_logistica", "alternativa_no_elegida": {
        "algoritmo": "xgboost", "hiperparametros": {"max_depth": 2}, "auc_roc_validacion": 0.8}}
    assert E.describir_alternativa(nuevo)["algoritmo"] == "xgboost"


def test_ruta_del_ensayo_fuera_del_repositorio(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location("evaluar_final", RAIZ / "scripts" / "evaluar_final.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    assert modulo.ruta_permitida_para_ensayo(tmp_path / "ensayo")
    assert not modulo.ruta_permitida_para_ensayo(RAIZ / "reportes")  # versionada


# --- Informe y metadatos con resultados simulados (criterios 3, 4 y 5) -------------------


def _resultado_simulado(ensayo: bool = False) -> E.ResultadoEvaluacion:
    from datetime import datetime

    datos, y, p = _datos_simulados()
    momentos = []
    for i, m in enumerate(V.Momento):
        metricas = E.metricas_alerta(y, p, 0.5)
        metricas["auc_roc"] = 0.75 + 0.05 * i
        momentos.append(E.ResultadoMomento(
            momento=m, version="1.0", sha256="a" * 64, fecha_entrenamiento="2026-11-04T00:00:00+00:00",
            algoritmo="xgboost", hiperparametros={"max_depth": 2}, umbral_alto=0.9, umbral_medio=0.5,
            auc_validacion=0.88, metricas=metricas,
            comprobacion={"proporcion_alto": 0.14, "deteccion_alto_medio": 0.81, "tasa_abandono_alto": 0.9,
                          "tasa_abandono_medio": 0.5, "tasa_abandono_bajo": 0.1, "proporcion_medio": 0.2,
                          "proporcion_bajo": 0.66, "decreciente": True},
            alternativa={"algoritmo": "regresion_logistica", "hiperparametros": {}, "auc_validacion_registrado": 0.8871,
                         "auc_validacion_recalculado": 0.8873, "metricas": E.metricas_alerta(y, p, 0.5)},
            habilitado=True, motivo_habilitacion="simulado",
        ))
    importancia = pd.Series({"materias_aprobadas_s1": 1.2, "edad_ingreso": 0.4, "genero": 0.1})
    return E.ResultadoEvaluacion(
        fecha=datetime(2026, 11, 5, 10, 30), ensayo=ensayo, momentos=momentos,
        subgrupos=E.metricas_por_subgrupo(datos, y, p, 0.5),
        cursando=E.auc_sin_cursando(datos[V.OBJETIVO], y, p),
        importancia=importancia, demograficas=E.revision_demografica(importancia),
        capacidad=0.15, deteccion=0.80,
    )


def _secciones_obligatorias(texto: str) -> None:
    for etiqueta in V.ETIQUETA_MOMENTO.values():
        assert etiqueta in texto
    for termino in ("AUC-ROC", "Precisión", "Sensibilidad", "Subgrupo", "Género", "Edad de ingreso", "Becario",
                    "Sin quienes siguen cursando", "Habilitación", "no las causas"):
        assert termino in texto, termino
    assert FRASE_ELECCION in texto
    for prohibido in ("factores que explican", "ingesta", "anonimizado"):
        assert prohibido not in texto.lower()


def test_criterios_3_y_4_informe_simulado():
    texto = armar_informe(_resultado_simulado())
    _secciones_obligatorias(texto)
    assert "05/11/2026 10:30" in texto
    assert "0,7500" in texto and "0,8000" in texto and "0,8500" in texto  # AUC de los tres momentos
    assert "0,8871 / 0,8873" in texto  # registrado y recalculado de la alternativa
    assert TITULO_ENSAYO not in texto


def test_informe_de_ensayo_lo_dice_en_el_titulo():
    texto = armar_informe(_resultado_simulado(ensayo=True))
    assert texto.startswith(f"# {TITULO_ENSAYO}")
    assert "ENSAYO (validación) — no son resultados de prueba" in texto


def test_criterio_5_metadatos_de_prueba_simulados():
    from datetime import datetime

    r = _resultado_simulado().momentos[1]
    cambios = E.metadatos_de_prueba(r, datetime(2026, 11, 5), {"auc_roc_sin_cursando": 0.93})
    assert cambios["habilitado"] is True and cambios["fecha_evaluacion"].startswith("2026-11-05")
    for clave in ("auc_roc", "precision_alerta", "sensibilidad_alerta", "auc_roc_sin_cursando", "alternativa_no_elegida"):
        assert clave in cambios["prueba"]
    assert cambios["sha256_pipeline"] == "a" * 64


# --- Sobre los archivos reales, cuando la evaluación final ya se hizo ---------------------


def test_criterios_3_y_4_informe_real():
    informe = RAIZ / "reportes" / "informe_evaluacion.md"
    if not informe.exists():
        pytest.skip("La evaluación final todavía no se ejecutó (la corre una persona)")
    _secciones_obligatorias(informe.read_text(encoding="utf-8"))


@pytest.mark.parametrize("momento", list(V.Momento))
def test_criterio_5_metadatos_reales_despues_de_la_prueba(momento):
    import json

    ruta = RAIZ / "modelos" / momento.value / "v1.0" / "metadatos.json"
    meta = json.loads(ruta.read_text(encoding="utf-8"))
    if meta.get("prueba") is None:
        pytest.skip("La evaluación final todavía no se ejecutó (la corre una persona)")
    assert meta["version"] == "1.0" and meta["fecha"] and meta["fecha_evaluacion"]
    for clave in ("auc_roc", "precision_alerta", "sensibilidad_alerta"):
        assert 0 <= meta["prueba"][clave] <= 1
    assert isinstance(meta["habilitado"], bool)
    if momento is V.Momento.CIERRE_1S:
        assert meta["habilitado"] == (meta["prueba"]["auc_roc"] > 0.80)
    else:
        assert meta["habilitado"] is True


def test_fechas_del_informe_en_hora_argentina():
    """La fecha de entrenamiento se guarda en UTC; el informe la muestra dd/mm/aaaa en hora argentina."""
    from datetime import datetime

    assert F.fecha(F.hora_argentina("2026-11-04T00:01:28+00:00")) == "03/11/2026"
    assert F.fecha_hora(F.hora_argentina("2026-11-04T00:01:28+00:00")) == "03/11/2026 21:01"
    assert F.hora_argentina(datetime(2026, 11, 5, 10, 30)) == datetime(2026, 11, 5, 10, 30)  # sin zona: ya local
    texto = armar_informe(_resultado_simulado())  # entrenado «2026-11-04T00:00:00+00:00»
    assert "03/11/2026" in texto and "2026-11-04" not in texto
