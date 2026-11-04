"""Configuración de la plataforma.

Los valores se leen de variables de entorno o del archivo .env (que nunca se
sube al repositorio; ver .env.example). Los parámetros metodológicos tienen
valores por defecto iguales a los del documento del TFG.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ = Path(__file__).resolve().parents[2]


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=RAIZ / ".env", env_file_encoding="utf-8", extra="ignore")

    entorno: str = Field("desarrollo", alias="ENTORNO")

    # Base de datos
    postgres_user: str = Field("alerta", alias="POSTGRES_USER")
    postgres_password: str = Field(..., alias="POSTGRES_PASSWORD")
    postgres_db: str = Field("alerta_temprana", alias="POSTGRES_DB")
    db_host: str = Field("localhost", alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")

    # Seudonimización (HU-001): clave secreta del HMAC que genera los códigos
    seudonimo_clave: str = Field(..., alias="SEUDONIMO_CLAVE")

    # Rutas (relativas a la raíz del repositorio si no son absolutas)
    ruta_datos: Path = Field(RAIZ / "data", alias="RUTA_DATOS")
    ruta_modelos: Path = Field(RAIZ / "modelos", alias="RUTA_MODELOS")
    ruta_reportes: Path = Field(RAIZ / "reportes", alias="RUTA_REPORTES")

    # Parámetros metodológicos (Objetivos y CRISP-DM del documento)
    semilla: int = Field(42, alias="SEMILLA")
    capacidad_tutorias: float = Field(0.15, alias="CAPACIDAD_TUTORIAS")  # supuesto del caso modelado
    deteccion_minima: float = Field(0.80, alias="DETECCION_MINIMA")  # alto + medio
    auc_minimo_cierre_1s: float = Field(0.80, alias="AUC_MINIMO_CIERRE_1S")

    @property
    def url_base_datos(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.db_host}:{self.db_port}/{self.postgres_db}"
        )


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
