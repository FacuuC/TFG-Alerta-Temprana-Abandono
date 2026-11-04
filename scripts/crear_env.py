"""Crea el archivo .env a partir de .env.example con claves aleatorias.

Uso:  python scripts/crear_env.py
No sobrescribe un .env existente. Solo usa la biblioteca estándar.
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def main() -> int:
    destino = RAIZ / ".env"
    if destino.exists():
        print(".env ya existe; no se modifica.")
        return 0
    contenido = (RAIZ / ".env.example").read_text(encoding="utf-8")
    contenido = contenido.replace(
        "POSTGRES_PASSWORD=cambiar-esta-clave", f"POSTGRES_PASSWORD={secrets.token_urlsafe(24)}"
    )
    contenido = contenido.replace(
        "SEUDONIMO_CLAVE=cambiar-por-una-clave-larga-y-aleatoria", f"SEUDONIMO_CLAVE={secrets.token_hex(32)}"
    )
    destino.write_text(contenido, encoding="utf-8")
    print("Se creó .env con claves aleatorias. No lo subas al repositorio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
