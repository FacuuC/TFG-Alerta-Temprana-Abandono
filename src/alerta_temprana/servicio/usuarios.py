"""Control del usuario de prueba en las funciones de servicio (decisión P5).

En el Sprint 1 no hay inicio de sesión: el usuario de prueba llega desde el selector de
la barra superior o como campo de la API. Las funciones de servicio controlan que exista,
esté activo y tenga un rol permitido, así la pantalla y la API respetan la misma regla.
**No es un control de acceso:** cualquiera puede elegir otro usuario (HU-009, Sprint 2).
"""

from __future__ import annotations

from collections.abc import Callable, Collection

from sqlalchemy import select
from sqlalchemy.orm import Session

from alerta_temprana.db.tablas import Rol, Usuario


class PermisoDenegado(Exception):
    """El usuario de prueba elegido no puede hacer esta acción."""


def comprobar_usuario(
    sesion: Session,
    nombre_usuario: str,
    roles: Collection[str],
    mensaje_rol: Callable[[str, str], str],
) -> Usuario:
    """Devuelve el usuario si existe, está activo y su rol está en `roles`.

    Lanza PermisoDenegado si no; `mensaje_rol(nombre_usuario, rol)` arma el motivo cuando
    el problema es el rol.
    """
    fila = sesion.execute(
        select(Usuario, Rol.nombre)
        .join(Rol, Usuario.id_rol == Rol.id_rol)
        .where(Usuario.nombre_usuario == nombre_usuario)
    ).first()
    if fila is None or not fila[0].activo:
        raise PermisoDenegado(f"El usuario «{nombre_usuario}» no existe o no está activo.")
    usuario, rol = fila
    if rol not in roles:
        raise PermisoDenegado(mensaje_rol(nombre_usuario, rol))
    return usuario
