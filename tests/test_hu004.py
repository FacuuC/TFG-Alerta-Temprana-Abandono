"""HU-004: clasificación por niveles de urgencia (tarea 4.2 y criterios 2 a 4).

Los criterios 1 y 5 se cumplieron en HU-002 (test_modelo.py, test_hu002.py e informe de
evaluación). Acá: nivel único con los umbrales exactos, alertas según la decisión P3 y
umbrales asociados a la versión del modelo.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select, update

from alerta_temprana.config import RAIZ
from alerta_temprana.datos.variables import Momento as M
from alerta_temprana.db.tablas import Alerta, CambioEstado, Modelo, Prediccion
from alerta_temprana.modelo.umbrales import clasificar
from alerta_temprana.servicio import prediccion as P
from alerta_temprana.servicio.alertas import actualizar_alertas, decidir_alerta
from alerta_temprana.servicio.modelos import cargar_habilitado, registrar_modelos
from tests.test_hu003 import _cargar, _fixture_como_dataframe

RAIZ_MODELOS = RAIZ / "modelos"


def _calcular(sesion, ruta_fixtures, plan, momento: M):
    resultado = _cargar(sesion, ruta_fixtures, momento)
    estado = plan.esperar(resultado.id_carga, tiempo=60)
    assert estado.estado == "completado"
    return estado


def _leer(sesion, consulta):
    """Relee de la base: el recálculo corre en otro hilo y otra sesión, y esta sesión no
    refresca sola los objetos que ya tiene en memoria."""
    return sesion.scalars(consulta.execution_options(populate_existing=True))


def _vigentes(sesion) -> dict[str, Prediccion]:
    return {p.codigo_estudiante: p for p in _leer(sesion, select(Prediccion).where(Prediccion.vigente))}


def _alertas(sesion) -> dict[str, Alerta]:
    return {a.codigo_estudiante: a for a in _leer(sesion, select(Alerta))}


# --- Criterio 2: un único nivel con los umbrales exactos -------------------------------


@pytest.mark.db
@pytest.mark.parametrize("momento", list(M))
def test_cada_prediccion_guardada_tiene_el_nivel_de_los_umbrales_exactos(
    sesion_db, ruta_fixtures, planificador, momento
):
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    _calcular(sesion_db, ruta_fixtures, planificador, momento)
    modelo = cargar_habilitado(sesion_db, momento, RAIZ_MODELOS)
    datos = _fixture_como_dataframe(ruta_fixtures, momento)
    exactas = dict(zip(datos.index, modelo.pipeline.predict_proba(datos)[:, 1], strict=True))
    vigentes = _vigentes(sesion_db)
    assert len(vigentes) == 10
    for codigo, prediccion in vigentes.items():
        assert prediccion.nivel == clasificar(exactas[codigo], modelo.umbral_alto, modelo.umbral_medio)
        assert float(prediccion.probabilidad) == pytest.approx(exactas[codigo], abs=5e-5)


def test_umbral_exacto_y_redondeado_pueden_dar_niveles_distintos():
    """Por eso se clasifica con el umbral de metadatos.json y no con el de MODELO."""
    exacto_medio = 0.5301468968391418  # cierre_1s v1.0
    p = 0.53012
    assert clasificar(p, 0.8935980796813965, exacto_medio) == "bajo"
    assert clasificar(p, 0.8936, round(exacto_medio, 4)) == "medio"


# --- Criterio 3: alertas según la decisión P3 ------------------------------------------


@pytest.mark.parametrize(
    ("nivel", "tiene_alerta", "accion"),
    [
        ("alto", False, "crear"),
        ("medio", False, "crear"),
        ("bajo", False, "ninguna"),
        ("alto", True, "actualizar"),
        ("medio", True, "actualizar"),
        ("bajo", True, "actualizar"),
    ],
)
def test_decidir_alerta(nivel, tiene_alerta, accion):
    assert decidir_alerta(nivel, tiene_alerta) == accion


@pytest.mark.db
def test_alto_o_medio_genera_alerta_pendiente_y_bajo_no(sesion_db, ruta_fixtures, planificador):
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    estado = _calcular(sesion_db, ruta_fixtures, planificador, M.CIERRE_1S)
    vigentes, alertas = _vigentes(sesion_db), _alertas(sesion_db)
    con_alerta = {c for c, p in vigentes.items() if p.nivel in ("alto", "medio")}
    assert con_alerta, "las fixtures tienen que tener algún estudiante en alto o medio"
    assert len(con_alerta) < len(vigentes), "y alguno en bajo"
    assert set(alertas) == con_alerta
    for codigo, alerta in alertas.items():
        assert alerta.estado == "pendiente"
        assert alerta.id_prediccion == vigentes[codigo].id_prediccion
    assert estado.resumen["alertas_creadas"] == len(con_alerta)
    assert sesion_db.scalar(select(func.count()).select_from(CambioEstado)) == 0  # HU-007


@pytest.mark.db
def test_al_recalcular_la_alerta_conserva_su_estado_y_apunta_a_la_vigente(
    sesion_db, ruta_fixtures, planificador
):
    """P3: una alerta por estudiante; si ya existe, se actualiza la predicción y se
    conserva el estado (HU-007, criterio 4)."""
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    _calcular(sesion_db, ruta_fixtures, planificador, M.CIERRE_1S)
    alertas = _alertas(sesion_db)
    codigo = sorted(alertas)[0]
    sesion_db.execute(update(Alerta).where(Alerta.codigo_estudiante == codigo).values(estado="contactado"))
    sesion_db.commit()
    creada = alertas[codigo].fecha_creacion

    _calcular(sesion_db, ruta_fixtures, planificador, M.CIERRE_2S)
    despues, vigentes = _alertas(sesion_db), _vigentes(sesion_db)
    assert (
        sesion_db.scalar(select(func.count()).select_from(Alerta).where(Alerta.codigo_estudiante == codigo))
        == 1
    )
    assert despues[codigo].estado == "contactado"
    assert despues[codigo].fecha_creacion == creada
    assert despues[codigo].id_prediccion == vigentes[codigo].id_prediccion
    for c, alerta in despues.items():
        assert alerta.id_prediccion == vigentes[c].id_prediccion
        if c not in alertas:  # alertas nuevas del segundo cálculo
            assert vigentes[c].nivel in ("alto", "medio") and alerta.estado == "pendiente"


@pytest.mark.db
def test_si_baja_a_nivel_bajo_la_alerta_queda_con_su_estado(sesion_db, ruta_fixtures, planificador):
    """P3: la alerta no se borra; queda con su estado y con el nivel de la predicción vigente."""
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    _calcular(sesion_db, ruta_fixtures, planificador, M.CIERRE_1S)
    codigo = sorted(_alertas(sesion_db))[0]
    sesion_db.execute(
        update(Alerta).where(Alerta.codigo_estudiante == codigo).values(estado="en_acompanamiento")
    )
    vigente = _vigentes(sesion_db)[codigo]
    sesion_db.execute(
        update(Prediccion).where(Prediccion.id_prediccion == vigente.id_prediccion).values(nivel="bajo")
    )
    creadas, actualizadas = actualizar_alertas(
        sesion_db, {codigo: (vigente.id_prediccion, "bajo")}, datetime.now(UTC)
    )
    sesion_db.commit()
    assert (creadas, actualizadas) == (0, 1)
    alerta = _alertas(sesion_db)[codigo]
    assert alerta.estado == "en_acompanamiento"
    nivel = sesion_db.scalar(select(Prediccion.nivel).where(Prediccion.id_prediccion == alerta.id_prediccion))
    assert nivel == "bajo"


@pytest.mark.db
def test_nivel_bajo_sin_alerta_previa_no_crea_alerta(sesion_db, ruta_fixtures, planificador):
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    _calcular(sesion_db, ruta_fixtures, planificador, M.CIERRE_1S)
    vigentes, alertas = _vigentes(sesion_db), _alertas(sesion_db)
    sin_alerta = [c for c in vigentes if c not in alertas]
    assert sin_alerta
    codigo = sin_alerta[0]
    assert actualizar_alertas(
        sesion_db, {codigo: (vigentes[codigo].id_prediccion, "bajo")}, datetime.now(UTC)
    ) == (0, 0)
    sesion_db.commit()
    assert codigo not in _alertas(sesion_db)


def test_el_servicio_de_prediccion_usa_la_regla_de_alertas():
    assert P.actualizar_alertas is actualizar_alertas


def _metadatos(momento: M) -> dict:
    return json.loads((RAIZ_MODELOS / momento.value / "v1.0" / "metadatos.json").read_text(encoding="utf-8"))


# --- Criterio 4: umbrales asociados a la versión del modelo ----------------------------


@pytest.mark.db
@pytest.mark.parametrize("momento", list(M))
def test_umbrales_guardados_con_la_version_del_modelo(sesion_db, momento):
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    meta = _metadatos(momento)
    fila = sesion_db.scalars(select(Modelo).where(Modelo.momento == momento.value)).one()
    assert fila.version == meta["version"] == "1.0"
    assert fila.umbral_alto == Decimal(str(round(meta["umbral_alto"], 4)))
    assert fila.umbral_medio == Decimal(str(round(meta["umbral_medio"], 4)))
    assert fila.umbral_medio <= fila.umbral_alto
    assert fila.habilitado is True


# --- Tarea 3.3: casos de cargas sucesivas ----------------------------------------------


def _foto(sesion) -> tuple[list, list]:
    """Predicciones y alertas tal como están en la base, para comparar antes y después."""
    predicciones = sesion.execute(
        select(Prediccion.id_prediccion, Prediccion.codigo_estudiante, Prediccion.vigente, Prediccion.nivel)
        .order_by(Prediccion.id_prediccion)
        .execution_options(populate_existing=True)
    ).all()
    alertas = sesion.execute(
        select(Alerta.id_alerta, Alerta.codigo_estudiante, Alerta.id_prediccion, Alerta.estado)
        .order_by(Alerta.id_alerta)
        .execution_options(populate_existing=True)
    ).all()
    return predicciones, alertas


@pytest.mark.db
def test_carga_rechazada_no_dispara_el_recalculo_ni_cambia_lo_vigente(sesion_db, ruta_fixtures, planificador):
    """Carga fallida: un archivo con coma decimal se rechaza completo (HU-001, criterio 2)
    después de una carga válida; no se encola ningún cálculo y nada cambia."""
    from alerta_temprana.datos.validacion import CargaRechazada
    from alerta_temprana.db.tablas import Carga

    registrar_modelos(sesion_db, RAIZ_MODELOS)
    _calcular(sesion_db, ruta_fixtures, planificador, M.INSCRIPCION)
    sesion_db.execute(update(Alerta).values(estado="contactado"))
    sesion_db.commit()
    antes = _foto(sesion_db)
    cargas_antes = sesion_db.scalar(select(func.count()).select_from(Carga))
    estados_antes = dict(planificador._estados)

    with pytest.raises(CargaRechazada, match="coma decimal"):
        _cargar(sesion_db, ruta_fixtures, M.INSCRIPCION, "coma_decimal.csv")

    assert planificador._estados == estados_antes  # el enganche no se llamó
    assert sesion_db.scalar(select(func.count()).select_from(Carga)) == cargas_antes
    assert _foto(sesion_db) == antes
    assert {a.estado for a in antes[1]} == {"contactado"}


@pytest.mark.db
def test_el_estado_de_seguimiento_se_conserva_en_la_carga_siguiente(sesion_db, ruta_fixtures, planificador):
    """Conservación del estado entre cargas (P3; HU-007, criterio 4): una alerta en un
    estado distinto de «pendiente» lo conserva después de la carga siguiente, tanto si
    sigue en alto o medio como si baja a bajo. El estado se fija directo (el cambio de
    estado es de HU-007)."""
    registrar_modelos(sesion_db, RAIZ_MODELOS)
    _calcular(sesion_db, ruta_fixtures, planificador, M.INSCRIPCION)
    estados = ("contactado", "en_acompanamiento")
    fijados = {}
    for i, codigo in enumerate(sorted(_alertas(sesion_db))):
        fijados[codigo] = estados[i % 2]
        sesion_db.execute(
            update(Alerta).where(Alerta.codigo_estudiante == codigo).values(estado=fijados[codigo])
        )
    sesion_db.commit()

    estado = _calcular(sesion_db, ruta_fixtures, planificador, M.CIERRE_1S)
    alertas, vigentes = _alertas(sesion_db), _vigentes(sesion_db)
    siguen = [c for c in fijados if vigentes[c].nivel in ("alto", "medio")]
    bajan = [c for c in fijados if vigentes[c].nivel == "bajo"]
    assert siguen and bajan, "las fixtures tienen que cubrir los dos casos"
    for codigo, estado_fijado in fijados.items():
        assert alertas[codigo].estado == estado_fijado, codigo
        assert alertas[codigo].id_prediccion == vigentes[codigo].id_prediccion
    assert estado.resumen["alertas_actualizadas"] == len(fijados)
    # Las alertas nuevas de esta carga, y solo esas, quedan en «pendiente»
    nuevas = set(alertas) - set(fijados)
    assert {alertas[c].estado for c in nuevas} <= {"pendiente"}
    assert estado.resumen["alertas_creadas"] == len(nuevas)
