"""HU-001: API interna (`/api/cargas`) y presentación de la pantalla de carga."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from alerta_temprana.app import app
from alerta_temprana.datos.validacion import CargaRechazada, ProblemaColumna
from alerta_temprana.db.sesion import obtener_sesion
from alerta_temprana.servicio.carga import ResultadoCarga
from alerta_temprana.ui import carga as pantalla
from alerta_temprana.ui.diseno import es_area_sistemas


@pytest.fixture
def cliente(sesion_db):
    app.dependency_overrides[obtener_sesion] = lambda: sesion_db
    yield TestClient(app)  # sin «with»: no corre el ciclo de vida sobre la base de desarrollo
    app.dependency_overrides.clear()


def _enviar(cliente, ruta_fixtures, nombre: str, momento: str, usuario: str = "sistemas01"):
    with (ruta_fixtures / nombre).open("rb") as archivo:
        return cliente.post(
            "/api/cargas",
            files={"archivo": (nombre, archivo, "text/csv")},
            data={"momento": momento, "usuario": usuario},
        )


@pytest.mark.db
def test_api_carga_valida(cliente, ruta_fixtures):
    respuesta = _enviar(cliente, ruta_fixtures, "registros_con_errores.csv", "inscripcion")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert (datos["registros_validos"], datos["registros_rechazados"]) == (7, 3)
    assert datos["estudiantes_nuevos"] == 7
    assert len(datos["errores"]) == 3
    assert "legajo" not in str(datos["errores"]).replace("'columna': 'legajo'", "")
    anteriores = cliente.get("/api/cargas").json()
    assert anteriores[0]["momento"] == "inscripcion" and anteriores[0]["usuario"] == "sistemas01"


@pytest.mark.db
def test_api_rechazo_completo_responde_422_con_columnas(cliente, ruta_fixtures):
    respuesta = _enviar(cliente, ruta_fixtures, "sin_columna.csv", "inscripcion")
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"]["columnas"] == ["carrera"]


@pytest.mark.db
def test_api_usuario_sin_rol_de_carga_responde_403(cliente, ruta_fixtures):
    respuesta = _enviar(cliente, ruta_fixtures, "inscripcion_valida.csv", "inscripcion", usuario="tutor01")
    assert respuesta.status_code == 403


def test_api_momento_desconocido_responde_422():
    respuesta = TestClient(app).post(
        "/api/cargas",
        files={"archivo": ("a.csv", b"x", "text/csv")},
        data={"momento": "ingreso", "usuario": "sistemas01"},
    )
    assert respuesta.status_code == 422


# --- Pantalla (presentación) -------------------------------------------------------------


def test_selector_habilita_la_carga_solo_al_area_de_sistemas():
    assert es_area_sistemas("sistemas01")
    assert not es_area_sistemas("tutor01")
    assert not es_area_sistemas("coordinacion01")
    estilo_formulario, estilo_aviso, *_ = pantalla.segun_usuario("tutor01")
    assert estilo_formulario["display"] == "none" and estilo_aviso.get("display") != "none"


def test_resultado_muestra_cantidades_y_leyenda():
    resultado = ResultadoCarga(
        id_carga=1,
        momento="cierre_1s",
        fecha=datetime(2026, 11, 5, 15, 0, tzinfo=UTC),
        usuario="sistemas01",
        registros_validos=885,
        registros_rechazados=0,
        estudiantes_nuevos=0,
        estudiantes_existentes=885,
        rendimientos_agregados=885,
        columnas_descartadas={"identificatorias": ["legajo"], "excluidas": ["deudor"], "otras": []},
    )
    texto = str(pantalla.mostrar_resultado(resultado))
    assert "885" in texto
    assert "05/11/2026 12:00" in texto  # hora argentina, dd/mm/aaaa
    assert pantalla.LEYENDA_SEUDONIMIZACION in texto
    assert "Cierre del 1.er semestre" in texto


def test_rechazo_muestra_las_columnas():
    error = CargaRechazada(
        "Se rechazó la carga completa", [ProblemaColumna("carrera", "falta la columna obligatoria")]
    )
    assert "carrera: falta la columna obligatoria" in str(pantalla.mostrar_rechazo(error))


def test_decodificar_archivo_del_upload():
    assert pantalla.decodificar_archivo("data:text/csv;base64,YTtiCg==") == b"a;b\n"
