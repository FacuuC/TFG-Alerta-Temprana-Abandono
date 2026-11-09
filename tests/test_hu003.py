"""HU-003: estimación y actualización automática del riesgo (tareas 3.1 a 3.3)."""

from __future__ import annotations

import json
import shutil

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import func, select, update
from sqlalchemy.orm import sessionmaker

from alerta_temprana.config import RAIZ
from alerta_temprana.datos import variables as V
from alerta_temprana.datos.seudonimizacion import codigo_estudiante
from alerta_temprana.datos.variables import Momento as M
from alerta_temprana.db.tablas import Alerta, Carga, FactorExplicativo, Modelo, Prediccion
from alerta_temprana.servicio import carga as servicio_carga
from alerta_temprana.servicio import modelos as servicio_modelos
from alerta_temprana.servicio import planificador as servicio_planificador
from alerta_temprana.servicio import prediccion as P
from alerta_temprana.servicio.modelos import ModeloNoDisponible, cargar_habilitado, registrar_modelos

RAIZ_MODELOS = RAIZ / "modelos"
CLAVE = "clave-de-pruebas"
ARCHIVO_FIXTURE = {
    M.INSCRIPCION: "inscripcion_valida.csv",
    M.CIERRE_1S: "cierre_1s_valida.csv",
    M.CIERRE_2S: "cierre_2s_valida.csv",
}


# Las fixtures `sin_enganches` y `planificador` están en conftest.py.


def _contar(sesion, tabla, *condiciones) -> int:
    return sesion.scalar(select(func.count()).select_from(tabla).where(*condiciones))


def _cargar(sesion, ruta_fixtures, momento: M, nombre: str | None = None):
    contenido = (ruta_fixtures / (nombre or ARCHIVO_FIXTURE[momento])).read_bytes()
    return servicio_carga.registrar_carga(sesion, contenido, momento, "sistemas01", CLAVE)


def _fixture_como_dataframe(ruta_fixtures, momento: M) -> pd.DataFrame:
    """El archivo leído directo con pandas, con la nota promedio a 2 decimales como en la base."""
    df = pd.read_csv(ruta_fixtures / ARCHIVO_FIXTURE[momento], sep=";", dtype={"legajo": str})
    df.index = [codigo_estudiante(legajo, CLAVE) for legajo in df["legajo"]]
    for columna in [c for c in df.columns if c.startswith("nota_promedio_s")]:
        df[columna] = df[columna].round(2)
    return df[V.VARIABLES_POR_MOMENTO[momento]]


# --- Registro de los modelos en MODELO ---------------------------------------------------


@pytest.mark.db
def test_registrar_modelos_agrega_los_tres_y_no_duplica(sesion_db):
    agregados = registrar_modelos(sesion_db, RAIZ_MODELOS)
    assert sorted(agregados) == ["cierre_1s v1.0", "cierre_2s v1.0", "inscripcion v1.0"]
    assert registrar_modelos(sesion_db, RAIZ_MODELOS) == []
    assert sesion_db.scalar(select(func.count()).select_from(Modelo)) == 3


@pytest.mark.db
def test_registrar_modelos_no_rehabilita_un_modelo_deshabilitado(sesion_db):
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    sesion_db.execute(update(Modelo).where(Modelo.momento == "cierre_2s").values(habilitado=False))
    sesion_db.commit()
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    assert sesion_db.scalar(select(Modelo.habilitado).where(Modelo.momento == "cierre_2s")) is False


@pytest.mark.db
def test_cargar_habilitado_usa_los_umbrales_exactos_de_los_metadatos(sesion_db):
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    modelo = cargar_habilitado(sesion_db, M.CIERRE_1S, RAIZ_MODELOS)
    meta = json.loads((RAIZ_MODELOS / "cierre_1s" / "v1.0" / "metadatos.json").read_text(encoding="utf-8"))
    assert modelo.umbral_alto == meta["umbral_alto"] == 0.8935980796813965
    assert modelo.umbral_medio == meta["umbral_medio"]
    assert modelo.momento is M.CIERRE_1S and modelo.version == "1.0"


@pytest.mark.db
def test_sin_modelo_habilitado_cargar_habilitado_devuelve_none(sesion_db):
    assert cargar_habilitado(sesion_db, M.INSCRIPCION, RAIZ_MODELOS) is None


@pytest.mark.db
def test_modelo_con_huella_distinta_no_se_usa(sesion_db, tmp_path):
    """El pipeline tiene que coincidir con la SHA-256 de sus metadatos."""
    copia = tmp_path / "modelos"
    shutil.copytree(RAIZ_MODELOS / "inscripcion", copia / "inscripcion")
    ruta_meta = copia / "inscripcion" / "v1.0" / "metadatos.json"
    meta = json.loads(ruta_meta.read_text(encoding="utf-8"))
    meta["sha256_pipeline"] = "0" * 64
    ruta_meta.write_text(json.dumps(meta), encoding="utf-8")
    registrar_modelos(sesion_db, copia)
    servicio_modelos._cache.clear()
    with pytest.raises(ModeloNoDisponible, match="SHA-256"):
        cargar_habilitado(sesion_db, M.INSCRIPCION, copia)


# --- Tarea 3.1: servicio de predicción ---------------------------------------------------


@pytest.mark.db
@pytest.mark.parametrize("momento", list(M))
def test_datos_desde_la_base_dan_la_misma_probabilidad_que_el_archivo(
    sesion_db, ruta_fixtures, sin_enganches, momento
):
    """Criterio 2 y control de la lectura desde ESTUDIANTE y RENDIMIENTO_SEMESTRE: mismas
    columnas, mismo orden, mismos tipos y mismas probabilidades que el archivo original."""
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    resultado = _cargar(sesion_db, ruta_fixtures, momento)
    esperado = _fixture_como_dataframe(ruta_fixtures, momento)
    datos = P.armar_datos(sesion_db, list(esperado.index), momento)
    assert list(datos.columns) == V.VARIABLES_POR_MOMENTO[momento]
    assert len(datos) == resultado.registros_validos == 10
    pd.testing.assert_frame_equal(datos, esperado, check_dtype=False, check_names=False)

    modelo = cargar_habilitado(sesion_db, momento, RAIZ_MODELOS)
    directas = modelo.pipeline.predict_proba(esperado)[:, 1]
    estimaciones = P.estimar(modelo, datos)
    np.testing.assert_allclose([e.probabilidad for e in estimaciones], directas, rtol=0, atol=1e-9)


@pytest.mark.db
def test_cierre_1s_no_usa_variables_del_segundo_semestre_aunque_esten_en_la_base(
    sesion_db, ruta_fixtures, sin_enganches
):
    """Sin información futura: con el rendimiento del 2.º semestre ya cargado, el cálculo de
    cierre_1s usa solo las 25 variables de su momento."""
    _cargar(sesion_db, ruta_fixtures, M.CIERRE_2S)
    codigos = list(_fixture_como_dataframe(ruta_fixtures, M.CIERRE_1S).index)
    datos = P.armar_datos(sesion_db, codigos, M.CIERRE_1S)
    assert list(datos.columns) == V.VARIABLES_POR_MOMENTO[M.CIERRE_1S]
    assert len(datos.columns) == 25
    assert not [c for c in datos.columns if c.endswith("_s2")]


@pytest.mark.db
def test_sin_el_rendimiento_del_semestre_no_se_estima(sesion_db, ruta_fixtures, sin_enganches):
    _cargar(sesion_db, ruta_fixtures, M.INSCRIPCION)
    codigos = list(_fixture_como_dataframe(ruta_fixtures, M.INSCRIPCION).index)
    with pytest.raises(P.DatosIncompletos, match="semestre 1"):
        P.armar_datos(sesion_db, codigos, M.CIERRE_1S)


@pytest.mark.db
def test_estimar_da_nivel_unico_y_cinco_factores_ordenados(sesion_db, ruta_fixtures, sin_enganches):
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    _cargar(sesion_db, ruta_fixtures, M.CIERRE_1S)
    codigos = list(_fixture_como_dataframe(ruta_fixtures, M.CIERRE_1S).index)
    modelo = cargar_habilitado(sesion_db, M.CIERRE_1S, RAIZ_MODELOS)
    for e in P.estimar(modelo, P.armar_datos(sesion_db, codigos, M.CIERRE_1S)):
        assert e.nivel in ("alto", "medio", "bajo")
        assert [f.orden for f, _ in e.factores] == [1, 2, 3, 4, 5]
        pesos = [abs(f.contribucion) for f, _ in e.factores]
        assert pesos == sorted(pesos, reverse=True)
        assert all(f.variable in V.VARIABLES_POR_MOMENTO[M.CIERRE_1S] for f, _ in e.factores)
        assert all(len(valor) <= 40 for _, valor in e.factores)


def test_estimar_rechaza_datos_con_variables_de_otro_momento():
    class _Modelo:
        momento = M.CIERRE_1S

    datos = pd.DataFrame(columns=V.VARIABLES_POR_MOMENTO[M.CIERRE_2S])
    with pytest.raises(ValueError, match="variables del momento"):
        P.estimar(_Modelo(), datos)


@pytest.mark.parametrize(
    ("valor", "texto"), [(9500.0, "9500"), (2, "2"), (13.9, "13.9"), (-4.06, "-4.06"), (12.69, "12.69")]
)
def test_valor_del_factor_se_guarda_sin_formatear(valor, texto):
    assert P.valor_como_texto(valor) == texto


# --- Tarea 3.2: recálculo al terminar cada carga -----------------------------------------


@pytest.mark.db
def test_carga_valida_calcula_el_riesgo_de_cada_estudiante_sin_intervencion(
    sesion_db, ruta_fixtures, planificador
):
    """Criterio 1: después de registrar_carga, sin ninguna otra llamada, cada estudiante
    incorporado tiene una predicción vigente con sus cinco factores."""
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    resultado = _cargar(sesion_db, ruta_fixtures, M.INSCRIPCION)
    assert resultado.recalculo["estado"] in ("en_curso", "completado")

    estado = planificador.esperar(resultado.id_carga, tiempo=60)
    assert estado.estado == "completado"
    assert estado.mensaje == "Completado: modelo v1.0 (Inscripción) · 10 estudiantes"
    assert estado.resumen["estudiantes"] == resultado.registros_validos == 10
    assert sum(estado.resumen["por_nivel"].values()) == 10

    codigos = list(_fixture_como_dataframe(ruta_fixtures, M.INSCRIPCION).index)
    vigentes = sesion_db.scalars(select(Prediccion).where(Prediccion.vigente)).all()
    assert sorted(p.codigo_estudiante for p in vigentes) == sorted(codigos)
    assert all(p.id_carga == resultado.id_carga for p in vigentes)
    for p in vigentes:
        assert _contar(sesion_db, FactorExplicativo, FactorExplicativo.id_prediccion == p.id_prediccion) == 5


@pytest.mark.db
@pytest.mark.parametrize("momento", list(M))
def test_se_usa_el_modelo_del_momento_de_la_carga(sesion_db, ruta_fixtures, planificador, momento):
    """Criterio 2."""
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    resultado = _cargar(sesion_db, ruta_fixtures, momento)
    planificador.esperar(resultado.id_carga, tiempo=60)
    id_modelo = sesion_db.scalar(
        select(Modelo.id_modelo).where(Modelo.momento == momento.value, Modelo.habilitado)
    )
    modelos_usados = set(sesion_db.scalars(select(Prediccion.id_modelo).distinct()))
    assert modelos_usados == {id_modelo}


@pytest.mark.db
def test_cargas_sucesivas_reemplazan_la_vigente_y_conservan_el_historial(
    sesion_db, ruta_fixtures, planificador
):
    """Criterio 3 y tarea 3.3: inscripción y después cierre del 1.er semestre."""
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    primera = _cargar(sesion_db, ruta_fixtures, M.INSCRIPCION)
    planificador.esperar(primera.id_carga, tiempo=60)
    anteriores = {
        p.codigo_estudiante: (p.id_prediccion, p.probabilidad)
        for p in sesion_db.scalars(select(Prediccion).where(Prediccion.vigente))
    }
    segunda = _cargar(sesion_db, ruta_fixtures, M.CIERRE_1S)
    assert planificador.esperar(segunda.id_carga, tiempo=60).estado == "completado"

    for codigo, (id_anterior, probabilidad) in anteriores.items():
        historial = sesion_db.scalars(
            select(Prediccion)
            .where(Prediccion.codigo_estudiante == codigo)
            .order_by(Prediccion.id_prediccion)
        ).all()
        assert len(historial) == 2
        vieja, nueva = historial
        assert (vieja.id_prediccion, vieja.probabilidad, vieja.vigente) == (id_anterior, probabilidad, False)
        assert vieja.id_carga == primera.id_carga
        assert nueva.vigente is True and nueva.id_carga == segunda.id_carga
        assert nueva.fecha >= vieja.fecha
        # el historial conserva sus factores
        assert _contar(sesion_db, FactorExplicativo, FactorExplicativo.id_prediccion == id_anterior) == 5
    momentos = dict(
        sesion_db.execute(
            select(Prediccion.vigente, Modelo.momento)
            .join(Modelo, Prediccion.id_modelo == Modelo.id_modelo)
            .distinct()
        ).all()
    )
    assert momentos == {False: "inscripcion", True: "cierre_1s"}


@pytest.mark.db
def test_si_falla_el_guardado_la_prediccion_anterior_sigue_vigente(
    sesion_db, ruta_fixtures, planificador, monkeypatch
):
    """Criterio 3: el reemplazo es una transacción."""
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    primera = _cargar(sesion_db, ruta_fixtures, M.INSCRIPCION)
    planificador.esperar(primera.id_carga, tiempo=60)

    def falla(*_args, **_kwargs):
        raise RuntimeError("falla simulada")

    monkeypatch.setattr(P, "actualizar_alertas", falla)
    segunda = _cargar(sesion_db, ruta_fixtures, M.CIERRE_1S)
    estado = planificador.esperar(segunda.id_carga, tiempo=60)
    assert estado.estado == "error"
    assert "las estimaciones anteriores siguen vigentes" in estado.mensaje
    assert _contar(sesion_db, Prediccion) == 10
    vigentes = sesion_db.scalars(select(Prediccion.id_carga).where(Prediccion.vigente)).all()
    assert vigentes == [primera.id_carga] * 10


@pytest.mark.db
def test_sin_modelo_habilitado_no_se_calcula_y_se_informa_el_motivo(sesion_db, ruta_fixtures, planificador):
    """Criterio 5: la carga se registra, no hay predicciones y el resultado dice por qué."""
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    sesion_db.execute(update(Modelo).where(Modelo.momento == "cierre_1s").values(habilitado=False))
    sesion_db.commit()

    resultado = _cargar(sesion_db, ruta_fixtures, M.CIERRE_1S)
    assert _contar(sesion_db, Carga, Carga.id_carga == resultado.id_carga) == 1
    assert resultado.recalculo["estado"] == "sin_modelo"
    assert resultado.recalculo["mensaje"].startswith(
        "No se calcularon riesgos: no hay un modelo habilitado para el momento «Cierre del 1.er semestre»."
    )
    assert planificador.esperar(resultado.id_carga).estado == "sin_modelo"
    assert _contar(sesion_db, Prediccion) == 0
    assert _contar(sesion_db, Alerta) == 0


@pytest.mark.db
def test_sin_ningun_modelo_registrado_tampoco_se_calcula(sesion_db, ruta_fixtures, planificador, caplog):
    """Criterio 5 con la tabla MODELO vacía; el motivo queda también en el registro."""
    with caplog.at_level("WARNING", logger="alerta_temprana.servicio.planificador"):
        resultado = _cargar(sesion_db, ruta_fixtures, M.INSCRIPCION)
    assert resultado.recalculo["estado"] == "sin_modelo"
    assert "sin modelo habilitado" in caplog.text
    assert _contar(sesion_db, Prediccion) == 0


@pytest.mark.db
def test_estado_se_reconstruye_desde_la_base(sesion_db, ruta_fixtures, planificador, motor_pruebas):
    """Después de reiniciar la aplicación (planificador nuevo, sin estados en memoria)."""
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    resultado = _cargar(sesion_db, ruta_fixtures, M.INSCRIPCION)
    planificador.esperar(resultado.id_carga, tiempo=60)
    nuevo = servicio_planificador.Planificador(sessionmaker(bind=motor_pruebas), RAIZ_MODELOS)
    try:
        estado = nuevo.estado(resultado.id_carga)
        assert estado.estado == "completado"
        assert estado.mensaje == "Completado: modelo v1.0 (Inscripción) · 10 estudiantes"
        assert nuevo.estado(resultado.id_carga + 1000) is None
    finally:
        nuevo.cerrar()


# --- Criterio 4: fecha de la última actualización y versión del modelo -------------------


@pytest.mark.db
def test_ultima_actualizacion_es_la_del_ultimo_calculo(sesion_db, ruta_fixtures, planificador):
    assert P.ultima_actualizacion(sesion_db) is None
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    primera = _cargar(sesion_db, ruta_fixtures, M.INSCRIPCION)
    planificador.esperar(primera.id_carga, tiempo=60)
    segunda = _cargar(sesion_db, ruta_fixtures, M.CIERRE_1S)
    estado = planificador.esperar(segunda.id_carga, tiempo=60)

    ultima = P.ultima_actualizacion(sesion_db)
    assert (ultima["version"], ultima["momento"]) == ("1.0", "cierre_1s")
    assert ultima["fecha"].isoformat() == estado.resumen["fecha"]


def test_texto_de_la_ultima_actualizacion_con_formato_argentino():
    from datetime import UTC, datetime

    from alerta_temprana.ui.actualizacion import SIN_CALCULO, texto_ultima_actualizacion

    ultima = {"fecha": datetime(2026, 11, 6, 17, 32, tzinfo=UTC), "version": "1.0", "momento": "cierre_1s"}
    assert (
        texto_ultima_actualizacion(ultima)
        == "Última actualización: 06/11/2026 14:32 · modelo v1.0 (Cierre del 1.er semestre)"
    )
    assert texto_ultima_actualizacion(None) == SIN_CALCULO


def test_la_barra_superior_tiene_la_ultima_actualizacion_para_todos_los_usuarios():
    from alerta_temprana.ui.diseno import barra_superior

    assert "ultima-actualizacion" in str(barra_superior("Carga de datos"))


@pytest.fixture
def cliente(sesion_db, planificador):
    from fastapi.testclient import TestClient

    from alerta_temprana.app import app
    from alerta_temprana.db.sesion import obtener_sesion

    app.dependency_overrides[obtener_sesion] = lambda: sesion_db
    app.dependency_overrides[servicio_planificador.obtener_planificador] = lambda: planificador
    yield TestClient(app)  # sin «with»: no corre el ciclo de vida sobre la base de desarrollo
    app.dependency_overrides.clear()


@pytest.mark.db
def test_api_informa_el_recalculo_y_la_ultima_actualizacion(cliente, sesion_db, ruta_fixtures, planificador):
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    assert cliente.get("/api/predicciones/ultima-actualizacion").json()["fecha"] is None
    with (ruta_fixtures / "cierre_1s_valida.csv").open("rb") as archivo:
        respuesta = cliente.post(
            "/api/cargas",
            files={"archivo": ("cierre_1s.csv", archivo, "text/csv")},
            data={"momento": "cierre_1s", "usuario": "sistemas01"},
        )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["recalculo"]["estado"] in ("en_curso", "completado")
    planificador.esperar(datos["id_carga"], tiempo=60)

    estado = cliente.get(f"/api/cargas/{datos['id_carga']}/recalculo").json()
    assert estado["estado"] == "completado"
    assert estado["mensaje"] == "Completado: modelo v1.0 (Cierre del 1.er semestre) · 10 estudiantes"
    ultima = cliente.get("/api/predicciones/ultima-actualizacion").json()
    assert (ultima["version"], ultima["momento"]) == ("1.0", "cierre_1s")
    assert ultima["fecha"] is not None
    assert cliente.get("/api/cargas/9999/recalculo").status_code == 404


@pytest.mark.db
def test_api_sin_modelo_devuelve_el_motivo_en_la_respuesta_de_la_carga(cliente, ruta_fixtures):
    """Criterio 5 por la API: el Área de Sistemas recibe el motivo en la respuesta."""
    with (ruta_fixtures / "inscripcion_valida.csv").open("rb") as archivo:
        datos = cliente.post(
            "/api/cargas",
            files={"archivo": ("inscripcion.csv", archivo, "text/csv")},
            data={"momento": "inscripcion", "usuario": "sistemas01"},
        ).json()
    assert datos["recalculo"]["estado"] == "sin_modelo"
    assert "no hay un modelo habilitado" in datos["recalculo"]["mensaje"]
    estado = cliente.get(f"/api/cargas/{datos['id_carga']}/recalculo").json()
    assert estado["estado"] == "sin_modelo"


def test_pantalla_muestra_el_estado_del_recalculo():
    from alerta_temprana.ui import carga as pantalla

    en_curso = {"estado": "en_curso", "mensaje": "Cálculo del riesgo en curso…", "resumen": None}
    assert "en curso" in str(pantalla.mostrar_recalculo(en_curso))
    completado = {
        "estado": "completado",
        "mensaje": "Completado: modelo v1.0 (Cierre del 1.er semestre) · 885 estudiantes",
        "resumen": {
            "por_nivel": {"alto": 134, "medio": 162, "bajo": 589},
            "alertas_creadas": 296,
            "alertas_actualizadas": 0,
        },
    }
    texto = str(pantalla.mostrar_recalculo(completado))
    assert "Completado: modelo v1.0 (Cierre del 1.er semestre)" in texto
    assert "Nivel alto: 134" in texto and "Alertas nuevas: 296" in texto
    sin_modelo = {"estado": "sin_modelo", "mensaje": servicio_planificador.mensaje_sin_modelo(M.CIERRE_2S)}
    assert "Cierre del 2.º semestre" in str(pantalla.mostrar_recalculo(sin_modelo))
    assert pantalla.mostrar_recalculo(None) is None


# --- Tarea 3.3: cargas sucesivas de punta a punta con data/cargas/ -----------------------
# Los tres archivos simulados son los 885 estudiantes de prueba, sin situación final
# (decisión P2). Estas pruebas solo cuentan niveles y comparan con las fichas: no leen
# etiquetas ni calculan métricas sobre prueba.

RUTA_CARGAS = RAIZ / "data" / "cargas"
ALTO_ESPERADO = {M.INSCRIPCION: 117, M.CIERRE_1S: 134, M.CIERRE_2S: 137}  # 13,2 / 15,1 / 15,5 % de 885


@pytest.fixture
def archivos_de_carga():
    from alerta_temprana.datos.cargas_simuladas import nombre_archivo

    rutas = {m: RUTA_CARGAS / nombre_archivo(m) for m in M}
    if not all(r.exists() for r in rutas.values()):
        pytest.skip("Faltan los archivos simulados: python scripts/generar_cargas.py")
    return rutas


def _cargar_los_tres(sesion, archivos, plan) -> dict[M, int]:
    """Carga los tres archivos en orden, con la clave actual, y devuelve cuántos
    estudiantes quedaron en nivel alto (vigente) después de cada carga."""
    altos = {}
    for momento in M:
        resultado = servicio_carga.registrar_carga(
            sesion, archivos[momento].read_bytes(), momento, "sistemas01"
        )
        assert (resultado.registros_validos, resultado.registros_rechazados) == (885, 0)
        estado = plan.esperar(resultado.id_carga, tiempo=300)
        assert estado.estado == "completado", estado.mensaje
        assert estado.resumen["estudiantes"] == 885
        altos[momento] = _contar(sesion, Prediccion, Prediccion.vigente, Prediccion.nivel == "alto")
    return altos


@pytest.mark.db
@pytest.mark.datos
def test_tres_cargas_en_orden_dan_los_niveles_altos_del_informe(sesion_db, archivos_de_carga, planificador):
    """117, 134 y 137 estudiantes en nivel alto: las proporciones de reportes/informe_evaluacion.md
    (13,2 / 15,1 / 15,5 %). Controla también que la nota promedio guardada con 2 decimales no
    mueva a nadie de nivel."""
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    altos = _cargar_los_tres(sesion_db, archivos_de_carga, planificador)
    assert altos == ALTO_ESPERADO
    assert _contar(sesion_db, Prediccion) == 3 * 885
    assert _contar(sesion_db, Prediccion, Prediccion.vigente) == 885


@pytest.mark.db
@pytest.mark.datos
def test_los_seis_casos_de_las_fichas_coinciden_con_su_prediccion_de_cierre_1s(
    sesion_db, archivos_de_carga, planificador
):
    """La predicción de cierre_1s de cada caso del cuestionario (en el historial, porque
    después se carga cierre_2s) tiene la probabilidad, el nivel y los 5 factores de
    reportes/cuestionario/casos.csv, en el mismo orden y con las mismas contribuciones."""
    from alerta_temprana.config import obtener_configuracion
    from alerta_temprana.datos.seudonimizacion import legajo_sintetico
    from alerta_temprana.modelo.etiquetas import texto_factor

    registrar_modelos(sesion_db, RAIZ_MODELOS)
    _cargar_los_tres(sesion_db, archivos_de_carga, planificador)
    casos = pd.read_csv(RAIZ / "reportes" / "cuestionario" / "casos.csv")
    clave = obtener_configuracion().seudonimo_clave
    id_cierre_1s = sesion_db.scalar(select(Modelo.id_modelo).where(Modelo.momento == "cierre_1s"))

    for caso in casos.itertuples():
        codigo = codigo_estudiante(legajo_sintetico(caso.indice_original), clave)
        prediccion = sesion_db.scalars(
            select(Prediccion).where(
                Prediccion.codigo_estudiante == codigo, Prediccion.id_modelo == id_cierre_1s
            )
        ).one()
        assert prediccion.vigente is False  # la vigente es la de cierre_2s
        assert float(prediccion.probabilidad) == caso.probabilidad, f"caso {caso.caso}"
        assert prediccion.nivel == caso.nivel, f"caso {caso.caso}"

        fila = P.armar_datos(sesion_db, [codigo], M.CIERRE_1S).loc[codigo]
        factores = sesion_db.scalars(
            select(FactorExplicativo)
            .where(FactorExplicativo.id_prediccion == prediccion.id_prediccion)
            .order_by(FactorExplicativo.orden)
        ).all()
        assert [f.orden for f in factores] == [1, 2, 3, 4, 5]
        for factor in factores:
            assert texto_factor(factor.variable, fila) == getattr(caso, f"factor_{factor.orden}"), (
                f"caso {caso.caso}, factor {factor.orden}"
            )
            assert float(factor.contribucion) == getattr(caso, f"contribucion_{factor.orden}"), (
                f"caso {caso.caso}, factor {factor.orden}"
            )
            assert factor.valor == P.valor_como_texto(fila[factor.variable])
