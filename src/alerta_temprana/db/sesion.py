"""Conexión a PostgreSQL con SQLAlchemy."""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from alerta_temprana.config import obtener_configuracion


@lru_cache
def obtener_motor() -> Engine:
    return create_engine(
        obtener_configuracion().url_base_datos,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )


@lru_cache
def obtener_fabrica_sesiones() -> sessionmaker[Session]:
    return sessionmaker(bind=obtener_motor(), expire_on_commit=False)


def obtener_sesion() -> Iterator[Session]:
    """Sesión por pedido (dependencia de FastAPI; las pruebas la reemplazan)."""
    with obtener_fabrica_sesiones()() as sesion:
        yield sesion


def base_disponible() -> bool:
    """True si la base responde a una consulta simple."""
    try:
        with obtener_motor().connect() as conexion:
            conexion.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
