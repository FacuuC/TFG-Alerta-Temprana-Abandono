"""Creación de las tablas y datos iniciales (tarea 1.2).

Al iniciar la aplicación se crean las tablas que falten (`create_all`, sin Alembic) y
se cargan los cuatro roles y un usuario de prueba por rol, sin contraseña: en el
Sprint 1 no hay inicio de sesión (HU-009 es del Sprint 2). Se puede ejecutar varias
veces: no duplica nada.
"""

from __future__ import annotations

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from alerta_temprana.db.tablas import Base, Rol, Usuario

ROL_AREA_SISTEMAS = "area_sistemas"
ROL_COORDINACION = "coordinacion_tutorias"
ROL_TUTOR = "tutor"
ROL_SECRETARIA = "secretaria_academica"

ROLES: dict[int, str] = {
    1: ROL_AREA_SISTEMAS,
    2: ROL_COORDINACION,
    3: ROL_TUTOR,
    4: ROL_SECRETARIA,
}

# nombre_usuario -> rol (docs/proyecto/03-modelo-de-datos.md, «Datos iniciales»)
USUARIOS_PRUEBA: dict[str, str] = {
    "sistemas01": ROL_AREA_SISTEMAS,
    "coordinacion01": ROL_COORDINACION,
    "tutor01": ROL_TUTOR,
    "secretaria01": ROL_SECRETARIA,
}


def crear_datos_iniciales(sesion: Session) -> None:
    """Agrega los roles y usuarios de prueba que falten."""
    existentes = {r.nombre: r.id_rol for r in sesion.scalars(select(Rol))}
    for id_rol, nombre in ROLES.items():
        if nombre not in existentes:
            sesion.add(Rol(id_rol=id_rol, nombre=nombre))
            existentes[nombre] = id_rol
    sesion.flush()
    usuarios = set(sesion.scalars(select(Usuario.nombre_usuario)))
    for nombre_usuario, rol in USUARIOS_PRUEBA.items():
        if nombre_usuario not in usuarios:
            sesion.add(Usuario(nombre_usuario=nombre_usuario, id_rol=existentes[rol], activo=True))
    sesion.commit()


def inicializar_base(motor: Engine) -> None:
    """Crea las tablas que falten y los datos iniciales."""
    Base.metadata.create_all(motor)
    with Session(motor) as sesion:
        crear_datos_iniciales(sesion)
