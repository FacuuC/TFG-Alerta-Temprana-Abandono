"""Verifica que el entorno de desarrollo esté listo.

Uso:  python scripts/verificar_entorno.py
Revisa la versión de Python, las dependencias, el archivo .env, el dataset,
Docker y la conexión con la base. No modifica nada.
"""

from __future__ import annotations

import importlib
import importlib.metadata as md
import json
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

PAQUETES = [
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("scikit-learn", "sklearn"),
    ("xgboost", "xgboost"),
    ("shap", "shap"),
    ("fastapi", "fastapi"),
    ("dash", "dash"),
    ("dash-bootstrap-components", "dash_bootstrap_components"),
    ("a2wsgi", "a2wsgi"),
    ("sqlalchemy", "sqlalchemy"),
    ("psycopg", "psycopg"),
    ("pydantic-settings", "pydantic_settings"),
    ("pytest", "pytest"),
]

resultados: list[tuple[bool, str]] = []


def marcar(ok: bool, texto: str) -> None:
    resultados.append((ok, texto))
    print(f"[{'OK' if ok else '!!'}] {texto}")


def main() -> int:
    version = sys.version_info
    marcar(version >= (3, 12), f"Python {version.major}.{version.minor}.{version.micro} ({sys.executable})")
    if ".venv" not in sys.executable:
        print("     Aviso: no parece ser el entorno virtual .venv del proyecto.")

    for distribucion, modulo in PAQUETES:
        try:
            importlib.import_module(modulo)
            marcar(True, f"{distribucion} {md.version(distribucion)}")
        except Exception as error:
            marcar(False, f"{distribucion}: {error.__class__.__name__}: {error}")

    try:
        importlib.import_module("alerta_temprana.datos.variables")
        marcar(True, "paquete alerta_temprana importable (variables por momento: 19, 25 y 31)")
    except Exception as error:
        marcar(False, f"paquete alerta_temprana: {error}")

    marcar((RAIZ / ".env").exists(), ".env presente (si falta: python scripts/crear_env.py)")

    fuente = RAIZ / "data" / "raw" / "fuente.json"
    if fuente.exists():
        datos = json.loads(fuente.read_text(encoding="utf-8"))
        marcar(
            not datos.get("problemas"),
            f"dataset verificado: {datos['registros']} registros, SHA-256 {datos['sha256'][:12]}…",
        )
    else:
        marcar(False, "dataset sin descargar (python scripts/descargar_datos.py)")

    docker = shutil.which("docker")
    if docker:
        estado = subprocess.run(
            [docker, "info", "--format", "{{.ServerVersion}}"], capture_output=True, text=True
        )
        marcar(
            estado.returncode == 0,
            f"Docker {'en ejecución, versión ' + estado.stdout.strip() if estado.returncode == 0 else 'instalado pero el motor no responde (abrí Docker Desktop)'}",
        )
    else:
        marcar(False, "Docker no encontrado en el PATH")

    if (RAIZ / ".env").exists():
        try:
            from alerta_temprana.db.sesion import base_disponible

            marcar(
                base_disponible(),
                "conexión con PostgreSQL (requiere: docker compose -f compose.yaml -f compose.dev.yaml up -d db)",
            )
        except Exception as error:
            marcar(False, f"conexión con PostgreSQL: {error}")

    fallas = [t for ok, t in resultados if not ok]
    print(f"\n{len(resultados) - len(fallas)} de {len(resultados)} controles correctos.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
