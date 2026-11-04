"""Conexión a PostgreSQL con SQLAlchemy."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine, text

from alerta_temprana.config import obtener_configuracion


@lru_cache
def obtener_motor() -> Engine:
    return create_engine(
        obtener_configuracion().url_base_datos,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )


def base_disponible() -> bool:
    """True si la base responde a una consulta simple."""
    try:
        with obtener_motor().connect() as conexion:
            conexion.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
