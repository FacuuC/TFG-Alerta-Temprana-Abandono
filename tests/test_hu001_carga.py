"""HU-001, tarea 1.4 y guardado: seudonimización, descarte, momento y usuario.

Las pruebas marcadas con `db` usan la base de pruebas (conftest.py).
"""

import re

import pytest
from sqlalchemy import func, inspect, select, text

from alerta_temprana.datos import seudonimizacion as S
from alerta_temprana.datos import variables as V
from alerta_temprana.datos.carga import procesar_archivo
from alerta_temprana.datos.validacion import CargaRechazada
from alerta_temprana.db.tablas import Carga, Estudiante, RendimientoSemestre, Usuario
from alerta_temprana.servicio import carga as servicio

CLAVE = "clave-de-pruebas"
M = V.Momento
FORMATO_CODIGO = re.compile(r"^EST-[0-9A-F]{8}$")


def _leer(ruta_fixtures, nombre: str) -> bytes:
    return (ruta_fixtures / nombre).read_bytes()


# --- Seudonimización y descarte (sin base) -------------------------------------------


def test_codigo_con_formato_y_estable():
    codigo = S.codigo_estudiante("T0001", CLAVE)
    assert FORMATO_CODIGO.match(codigo)
    assert len(codigo) == 12
    assert codigo == S.codigo_estudiante(" T0001 ", CLAVE)
    assert codigo != S.codigo_estudiante("T0001", "otra-clave")


def test_colision_de_codigos_rechaza_la_carga_completa(ruta_fixtures, monkeypatch):
    monkeypatch.setattr(S, "codigo_estudiante", lambda legajo, clave: "EST-00000000")
    with pytest.raises(CargaRechazada, match="mismo código seudonimizado"):
        procesar_archivo(_leer(ruta_fixtures, "inscripcion_valida.csv"), M.INSCRIPCION, CLAVE)


def test_se_descartan_identificatorias_excluidas_y_variables_posteriores(ruta_fixtures):
    """Un archivo de cierre del 2.º semestre cargado como cierre del 1.º: nada de _s2."""
    resultado = procesar_archivo(_leer(ruta_fixtures, "cierre_2s_valida.csv"), M.CIERRE_1S, CLAVE)
    descartadas = resultado.columnas_descartadas
    assert descartadas["identificatorias"] == ["legajo", "documento", "apellido_nombre"]
    assert descartadas["excluidas"] == list(V.VARIABLES_EXCLUIDAS)
    assert descartadas["otras"] == list(V.VARIABLES_SEMESTRE_2)
    assert list(resultado.estudiantes.columns) == ["codigo_estudiante", *V.VARIABLES_INSCRIPCION]
    assert set(resultado.rendimientos["semestre"]) == {1}
    assert resultado.estudiantes["codigo_estudiante"].map(FORMATO_CODIGO.match).all()


# --- Guardado (con base) -------------------------------------------------------------


@pytest.fixture
def sin_enganches():
    anteriores = list(servicio._al_terminar_carga)
    servicio._al_terminar_carga.clear()
    yield
    servicio._al_terminar_carga[:] = anteriores


@pytest.mark.db
def test_carga_valida_incorpora_e_informa_la_cantidad(sesion_db, ruta_fixtures, sin_enganches):
    """Criterio 1."""
    resultado = servicio.registrar_carga(
        sesion_db, _leer(ruta_fixtures, "inscripcion_valida.csv"), M.INSCRIPCION, "sistemas01", CLAVE
    )
    assert resultado.registros_validos == 10
    assert resultado.estudiantes_nuevos == 10
    assert sesion_db.scalar(select(func.count()).select_from(Estudiante)) == 10
    assert sesion_db.scalar(select(func.count()).select_from(RendimientoSemestre)) == 0


@pytest.mark.db
def test_carga_rechazada_no_guarda_nada(sesion_db, ruta_fixtures, sin_enganches):
    """Criterio 2: rechazo de la carga completa."""
    with pytest.raises(CargaRechazada):
        servicio.registrar_carga(
            sesion_db, _leer(ruta_fixtures, "sin_columna.csv"), M.INSCRIPCION, "sistemas01", CLAVE
        )
    assert sesion_db.scalar(select(func.count()).select_from(Carga)) == 0
    assert sesion_db.scalar(select(func.count()).select_from(Estudiante)) == 0


@pytest.mark.db
def test_registros_con_errores_no_se_guardan(sesion_db, ruta_fixtures, sin_enganches):
    """Criterio 3."""
    resultado = servicio.registrar_carga(
        sesion_db, _leer(ruta_fixtures, "registros_con_errores.csv"), M.INSCRIPCION, "sistemas01", CLAVE
    )
    assert (resultado.registros_validos, resultado.registros_rechazados) == (7, 3)
    carga = sesion_db.scalar(select(Carga))
    assert (carga.registros_validos, carga.registros_rechazados) == (7, 3)
    guardados = set(sesion_db.scalars(select(Estudiante.codigo_estudiante)))
    assert len(guardados) == 7
    assert not guardados & {e.codigo_estudiante for e in resultado.errores}


@pytest.mark.db
def test_ninguna_tabla_guarda_datos_identificatorios_ni_excluidos(
    sesion_db, motor_pruebas, ruta_fixtures, sin_enganches
):
    """Criterio 4: ni columnas ni valores de legajo, documento o nombre; nada excluido."""
    for momento in M:
        servicio.registrar_carga(
            sesion_db, _leer(ruta_fixtures, f"{momento.value}_valida.csv"), momento, "sistemas01", CLAVE
        )
    prohibidas = {"legajo", "documento", "apellido_nombre", "dni", *V.VARIABLES_EXCLUIDAS}
    inspector = inspect(motor_pruebas)
    for tabla in inspector.get_table_names():
        columnas = {c["name"] for c in inspector.get_columns(tabla)}
        assert not columnas & prohibidas, tabla

    texto_fixture = _leer(ruta_fixtures, "inscripcion_valida.csv").decode("utf-8")
    legajos = re.findall(r"^(T\d{4});(\d+);([^;]+);", texto_fixture, flags=re.MULTILINE)
    volcado = " ".join(
        str(valor)
        for tabla in ("estudiante", "rendimiento_semestre", "carga")
        for fila in sesion_db.execute(text(f"SELECT * FROM {tabla}")).all()
        for valor in fila
    )
    for legajo, documento, nombre in legajos:
        assert legajo not in volcado and documento not in volcado and nombre not in volcado

    codigos = list(sesion_db.scalars(select(Estudiante.codigo_estudiante)))
    assert len(codigos) == 10 and all(FORMATO_CODIGO.match(c) for c in codigos)


@pytest.mark.db
def test_mismo_legajo_mismo_codigo_entre_cargas_sin_duplicar(sesion_db, ruta_fixtures, sin_enganches):
    """Criterio 4 y momentos sucesivos (decisión del 04/11): no se duplica ni se modifica."""
    primera = servicio.registrar_carga(
        sesion_db, _leer(ruta_fixtures, "inscripcion_valida.csv"), M.INSCRIPCION, "sistemas01", CLAVE
    )
    codigos_inscripcion = set(sesion_db.scalars(select(Estudiante.codigo_estudiante)))
    segunda = servicio.registrar_carga(
        sesion_db, _leer(ruta_fixtures, "cierre_1s_valida.csv"), M.CIERRE_1S, "sistemas01", CLAVE
    )
    tercera = servicio.registrar_carga(
        sesion_db, _leer(ruta_fixtures, "cierre_2s_valida.csv"), M.CIERRE_2S, "sistemas01", CLAVE
    )
    assert set(sesion_db.scalars(select(Estudiante.codigo_estudiante))) == codigos_inscripcion
    assert (primera.estudiantes_nuevos, primera.estudiantes_existentes, primera.rendimientos_agregados) == (
        10,
        0,
        0,
    )
    assert (segunda.estudiantes_nuevos, segunda.estudiantes_existentes, segunda.rendimientos_agregados) == (
        0,
        10,
        10,
    )
    assert (tercera.estudiantes_nuevos, tercera.estudiantes_existentes, tercera.rendimientos_agregados) == (
        0,
        10,
        10,
    )
    # Los estudiantes conservan la carga en la que se incorporaron; cada semestre, la suya
    assert set(sesion_db.scalars(select(Estudiante.id_carga))) == {primera.id_carga}
    por_semestre = dict(
        sesion_db.execute(
            select(RendimientoSemestre.semestre, func.min(RendimientoSemestre.id_carga)).group_by(
                RendimientoSemestre.semestre
            )
        ).all()
    )
    assert por_semestre == {1: segunda.id_carga, 2: tercera.id_carga}

    # Repetir una carga no duplica nada
    repetida = servicio.registrar_carga(
        sesion_db, _leer(ruta_fixtures, "cierre_2s_valida.csv"), M.CIERRE_2S, "sistemas01", CLAVE
    )
    assert (repetida.estudiantes_nuevos, repetida.rendimientos_agregados) == (0, 0)
    assert sesion_db.scalar(select(func.count()).select_from(RendimientoSemestre)) == 20


@pytest.mark.db
def test_carga_queda_asociada_al_momento_y_al_usuario(sesion_db, ruta_fixtures, sin_enganches):
    """Criterio 5."""
    resultado = servicio.registrar_carga(
        sesion_db, _leer(ruta_fixtures, "cierre_1s_valida.csv"), M.CIERRE_1S, "sistemas01", CLAVE
    )
    carga = sesion_db.get(Carga, resultado.id_carga)
    usuario = sesion_db.get(Usuario, carga.id_usuario)
    assert carga.momento == "cierre_1s"
    assert usuario.nombre_usuario == "sistemas01"
    assert carga.fecha.tzinfo is not None
    assert servicio.listar_cargas(sesion_db)[0]["momento"] == "cierre_1s"


@pytest.mark.db
@pytest.mark.parametrize("usuario", ["tutor01", "coordinacion01", "secretaria01", "inexistente"])
def test_solo_el_area_de_sistemas_puede_cargar(sesion_db, ruta_fixtures, sin_enganches, usuario):
    """Decisión P5: el control de rol está en el servicio, así lo respeta también la API."""
    with pytest.raises(servicio.PermisoDenegado):
        servicio.registrar_carga(
            sesion_db, _leer(ruta_fixtures, "inscripcion_valida.csv"), M.INSCRIPCION, usuario, CLAVE
        )
    assert sesion_db.scalar(select(func.count()).select_from(Carga)) == 0


@pytest.mark.db
def test_al_terminar_la_carga_se_avisa_a_las_funciones_registradas(sesion_db, ruta_fixtures, sin_enganches):
    """Punto de enganche para el recálculo de HU-003."""
    avisos = []
    servicio.registrar_al_terminar_carga(
        lambda id_carga, momento, codigos: avisos.append((id_carga, momento, codigos)) or "ok"
    )
    resultado = servicio.registrar_carga(
        sesion_db, _leer(ruta_fixtures, "inscripcion_valida.csv"), M.INSCRIPCION, "sistemas01", CLAVE
    )
    codigos = [S.codigo_estudiante(f"T{n:04d}", CLAVE) for n in range(1, 11)]
    assert avisos == [(resultado.id_carga, M.INSCRIPCION, codigos)]
    assert resultado.al_terminar == ["ok"]
    assert resultado.recalculo is None  # solo lo completa el planificador de HU-003
