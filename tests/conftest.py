"""Configuración común de las pruebas."""

import os
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RUTA_DATASET = RAIZ / "data" / "raw" / "data.csv"

# Valores mínimos para que la configuración cargue aunque no exista .env
os.environ.setdefault("POSTGRES_PASSWORD", "solo-para-pruebas")
os.environ.setdefault("SEUDONIMO_CLAVE", "clave-de-pruebas")


@pytest.fixture
def ruta_dataset() -> Path:
    if not RUTA_DATASET.exists():
        pytest.skip("Falta el dataset: python scripts/descargar_datos.py")
    return RUTA_DATASET
