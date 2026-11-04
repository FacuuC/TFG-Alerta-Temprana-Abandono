"""Fija en requirements.txt las versiones instaladas en el entorno actual.

Uso (después de una instalación que funcione y de pasar las pruebas):
    python scripts/fijar_versiones.py

Reemplaza cada rango (por ejemplo «xgboost>=3.0,<4») por la versión exacta
instalada («xgboost==3.x.y»), conservando los comentarios. Así la imagen de
Docker y cualquier otra instalación usan exactamente las mismas versiones.
Solo fija las dependencias directas: sirven igual en Windows y en Linux.
"""

from __future__ import annotations

import importlib.metadata as md
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PATRON = re.compile(r"^(?P<nombre>[A-Za-z0-9_.\-]+)(?P<extras>\[[^\]]+\])?\s*(?P<resto>.*)$")


def main() -> int:
    ruta = RAIZ / "requirements.txt"
    lineas_nuevas: list[str] = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.strip() or linea.lstrip().startswith(("#", "-")):
            lineas_nuevas.append(linea)
            continue
        coincidencia = PATRON.match(linea.strip())
        if not coincidencia:
            lineas_nuevas.append(linea)
            continue
        nombre, extras = coincidencia["nombre"], coincidencia["extras"] or ""
        try:
            version = md.version(nombre)
        except md.PackageNotFoundError:
            print(f"No está instalado: {nombre}. Instalá las dependencias antes de fijarlas.")
            return 1
        lineas_nuevas.append(f"{nombre}{extras}=={version}")
        print(f"{nombre}{extras}=={version}")
    ruta.write_text("\n".join(lineas_nuevas) + "\n", encoding="utf-8")
    print("\nrequirements.txt actualizado. Hacé un commit con este cambio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
