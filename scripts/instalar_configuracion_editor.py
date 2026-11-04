"""Mueve la configuración de Claude Code y de VS Code a su lugar.

Uso (una sola vez, desde la raíz del repositorio):
    python scripts/instalar_configuracion_editor.py

La configuración llegó en la carpeta _configuracion_editor/ porque las carpetas
.claude y .vscode no se pueden escribir de forma remota. Este script crea:
    .claude/commands/hu.md          comando /hu HU-00X (planificar una historia)
    .claude/commands/revisar-hu.md  comando /revisar-hu HU-00X (verificar criterios)
    .claude/settings.json           impide que Claude Code lea .env
    .vscode/settings.json           intérprete .venv y pytest
    .vscode/extensions.json         extensiones recomendadas
y después borra _configuracion_editor/. No pisa archivos que ya existan.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "_configuracion_editor"
DESTINOS = {"claude": RAIZ / ".claude", "vscode": RAIZ / ".vscode"}


def main() -> int:
    if not ORIGEN.exists():
        print("No hay nada para instalar: _configuracion_editor/ no existe.")
        return 0
    for nombre, destino in DESTINOS.items():
        for archivo in (ORIGEN / nombre).rglob("*"):
            if archivo.is_file():
                final = destino / archivo.relative_to(ORIGEN / nombre)
                if final.exists():
                    print(f"Ya existe, se deja como está: {final.relative_to(RAIZ)}")
                    continue
                final.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(archivo, final)
                print(f"Creado: {final.relative_to(RAIZ)}")
    shutil.rmtree(ORIGEN)
    print("Listo. Se borró _configuracion_editor/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
