"""Configuración común de las pruebas."""

import os
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RUTA_DATASET = RAIZ / "data" / "raw" / "data.csv"
RUTA_FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Valores mínimos para que la configuración cargue aunque no exista .env. Si .env existe,
# no se fijan: las variables de entorno tienen prioridad sobre .env en pydantic-settings y
# pisarían la contraseña real de la base.
if not (RAIZ / ".env").exists():
    os.environ.setdefault("POSTGRES_PASSWORD", "solo-para-pruebas")
    os.environ.setdefault("SEUDONIMO_CLAVE", "clave-de-pruebas")


@pytest.fixture
def ruta_dataset() -> Path:
    if not RUTA_DATASET.exists():
        pytest.skip("Falta el dataset: python scripts/descargar_datos.py")
    return RUTA_DATASET


@pytest.fixture
def ruta_fixtures() -> Path:
    return RUTA_FIXTURES


# --- Base de datos de pruebas ---------------------------------------------------
# Las pruebas marcadas con @pytest.mark.db usan una base aparte (<POSTGRES_DB>_pruebas),
# que se crea si no existe y se vacía antes de cada prueba, para no mezclar con los datos
# de desarrollo.


@pytest.fixture(scope="session")
def motor_pruebas():
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    from alerta_temprana.config import obtener_configuracion
    from alerta_temprana.db.inicializacion import inicializar_base
    from alerta_temprana.db.tablas import Base

    configuracion = obtener_configuracion()
    url = make_url(configuracion.url_base_datos)
    if url.host == "localhost":
        # En Windows, «localhost» prueba primero IPv6 y la primera conexión puede tardar
        # minutos; la base de desarrollo se publica solo en 127.0.0.1 (compose.dev.yaml).
        url = url.set(host="127.0.0.1")
    nombre = f"{configuracion.postgres_db}_pruebas"
    administrador = create_engine(url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 3})
    try:
        with administrador.connect() as conexion:
            existe = conexion.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": nombre}
            ).first()
            if not existe:
                conexion.execute(text(f'CREATE DATABASE "{nombre}"'))
    except Exception as error:  # base apagada o sin permisos
        pytest.skip(f"PostgreSQL no disponible: {type(error).__name__}")
    finally:
        administrador.dispose()

    motor = create_engine(url.set(database=nombre))
    Base.metadata.drop_all(motor)  # el esquema siempre coincide con tablas.py
    inicializar_base(motor)
    yield motor
    motor.dispose()


@pytest.fixture
def sesion_db(motor_pruebas):
    """Sesión sobre la base de pruebas vacía (solo roles y usuarios de prueba)."""
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    from alerta_temprana.db.tablas import Base

    tablas = [t.name for t in Base.metadata.sorted_tables if t.name not in ("rol", "usuario")]
    with motor_pruebas.begin() as conexion:
        conexion.execute(text(f"TRUNCATE {', '.join(tablas)} RESTART IDENTITY CASCADE"))
    with Session(motor_pruebas, expire_on_commit=False) as sesion:
        yield sesion


# --- Recálculo del riesgo (HU-003) ------------------------------------------------------


@pytest.fixture
def sin_enganches():
    """registrar_carga sin funciones enganchadas (se restauran al terminar)."""
    from alerta_temprana.servicio import carga as servicio_carga

    anteriores = list(servicio_carga._al_terminar_carga)
    servicio_carga._al_terminar_carga.clear()
    yield
    servicio_carga._al_terminar_carga[:] = anteriores


@pytest.fixture
def planificador(motor_pruebas, sin_enganches):
    """Planificador sobre la base de pruebas, enganchado a registrar_carga como en app.py."""
    from sqlalchemy.orm import sessionmaker

    from alerta_temprana.servicio import carga as servicio_carga
    from alerta_temprana.servicio.planificador import Planificador

    plan = Planificador(sessionmaker(bind=motor_pruebas, expire_on_commit=False), RAIZ / "modelos")
    servicio_carga.registrar_al_terminar_carga(plan.al_terminar_carga)
    yield plan
    plan.cerrar()
