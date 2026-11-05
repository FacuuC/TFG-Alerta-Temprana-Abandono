"""HU-001: archivos de carga simulados (decisión P2) y carga de punta a punta.

Usan el dataset (marca `datos`). Se lee sin la columna Target: ninguna prueba toca las
etiquetas del conjunto de prueba.
"""

import pandas as pd
import pytest
from sqlalchemy import func, select

from alerta_temprana.config import RAIZ
from alerta_temprana.datos import variables as V
from alerta_temprana.datos.carga import procesar_archivo
from alerta_temprana.datos.cargas_simuladas import columnas_exportacion, generar_cargas
from alerta_temprana.db.tablas import Estudiante, RendimientoSemestre
from alerta_temprana.servicio import carga as servicio

RUTA_PARTICION = RAIZ / "data" / "procesados" / "particion.csv"


@pytest.fixture
def cargas(ruta_dataset, tmp_path):
    if not RUTA_PARTICION.exists():
        pytest.skip("Falta la partición: python scripts/preparar_particion.py")
    return generar_cargas(ruta_dataset, RUTA_PARTICION, tmp_path)


@pytest.mark.datos
def test_archivos_simulados_solo_prueba_sin_situacion_final(cargas):
    particion = pd.read_csv(RUTA_PARTICION, index_col="indice_original")["conjunto"]
    cantidad_prueba = int((particion == "prueba").sum())
    anteriores = None
    for momento, ruta in cargas.items():
        df = pd.read_csv(ruta, sep=";", dtype={"legajo": str})
        assert list(df.columns) == columnas_exportacion(momento)
        assert V.OBJETIVO not in df.columns and "Target" not in df.columns
        assert len(df) == cantidad_prueba
        identificadores = df[["legajo", "documento", "apellido_nombre"]]
        if anteriores is not None:  # constantes entre los tres archivos
            pd.testing.assert_frame_equal(identificadores, anteriores)
        anteriores = identificadores
    assert not any("_s2" in c for c in columnas_exportacion(V.Momento.CIERRE_1S))


@pytest.mark.datos
def test_archivos_simulados_pasan_la_validacion_sin_rechazos(cargas):
    for momento, ruta in cargas.items():
        resultado = procesar_archivo(ruta.read_bytes(), momento, "clave-de-pruebas")
        assert resultado.registros_rechazados == 0, momento
        assert resultado.registros_validos == 885


@pytest.mark.db
@pytest.mark.datos
def test_tres_cargas_sucesivas_de_punta_a_punta(sesion_db, cargas, monkeypatch):
    monkeypatch.setattr(servicio, "_al_terminar_carga", [])
    resultados = [
        servicio.registrar_carga(sesion_db, ruta.read_bytes(), momento, "sistemas01", "clave-de-pruebas")
        for momento, ruta in cargas.items()
    ]
    assert [
        (r.estudiantes_nuevos, r.estudiantes_existentes, r.rendimientos_agregados) for r in resultados
    ] == [
        (885, 0, 0),
        (0, 885, 885),
        (0, 885, 885),
    ]
    assert sesion_db.scalar(select(func.count()).select_from(Estudiante)) == 885
    assert sesion_db.scalar(select(func.count()).select_from(RendimientoSemestre)) == 2 * 885
