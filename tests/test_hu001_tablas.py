"""HU-001, tarea 1.2: tablas del DER y datos iniciales."""

import pytest
from sqlalchemy import inspect, select

from alerta_temprana.datos import variables as V
from alerta_temprana.db.inicializacion import USUARIOS_PRUEBA, crear_datos_iniciales
from alerta_temprana.db.tablas import Base, Estudiante, RendimientoSemestre, Rol, Usuario

TABLAS_DER = {
    "rol",
    "usuario",
    "carga",
    "estudiante",
    "rendimiento_semestre",
    "modelo",
    "metrica_subgrupo",
    "prediccion",
    "factor_explicativo",
    "alerta",
    "cambio_estado",
}
IDENTIFICATORIAS = {"legajo", "documento", "apellido_nombre", "nombre", "dni"}


def test_las_tablas_son_las_del_der():
    assert set(Base.metadata.tables) == TABLAS_DER


def test_estudiante_tiene_las_variables_de_inscripcion_y_nada_identificatorio():
    columnas = set(Estudiante.__table__.columns.keys())
    assert columnas == {"codigo_estudiante", "id_carga", "situacion_final", *V.VARIABLES_INSCRIPCION}
    assert not columnas & IDENTIFICATORIAS
    assert not columnas & set(V.VARIABLES_EXCLUIDAS)


def test_rendimiento_tiene_los_seis_campos_por_semestre():
    columnas = set(RendimientoSemestre.__table__.columns.keys())
    assert set(V.CAMPOS_RENDIMIENTO) <= columnas
    assert Estudiante.__table__.c.codigo_estudiante.type.length == 12


@pytest.mark.db
def test_tablas_creadas_en_postgresql(motor_pruebas):
    assert TABLAS_DER <= set(inspect(motor_pruebas).get_table_names())


@pytest.mark.db
def test_datos_iniciales_un_usuario_por_rol_y_sin_duplicar(sesion_db):
    crear_datos_iniciales(sesion_db)  # segunda vez: no debe duplicar
    roles = list(sesion_db.scalars(select(Rol.nombre)))
    assert sorted(roles) == sorted(set(USUARIOS_PRUEBA.values()))
    usuarios = {u.nombre_usuario: u for u in sesion_db.scalars(select(Usuario))}
    assert set(usuarios) == set(USUARIOS_PRUEBA)
    assert all(u.hash_contrasena is None and u.activo for u in usuarios.values())
