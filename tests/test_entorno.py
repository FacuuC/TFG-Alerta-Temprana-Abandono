"""El entorno tiene las bibliotecas del stack documentado (Herramientas de Software)."""

import importlib

import pytest


@pytest.mark.parametrize(
    "modulo", ["pandas", "sklearn", "xgboost", "shap", "fastapi", "dash", "sqlalchemy", "psycopg", "a2wsgi"]
)
def test_biblioteca_disponible(modulo):
    importlib.import_module(modulo)


def test_aplicacion_responde_salud():
    from fastapi.testclient import TestClient

    from alerta_temprana.app import app

    respuesta = TestClient(app).get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ok"
