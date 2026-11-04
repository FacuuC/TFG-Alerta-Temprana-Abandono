"""Candado del conjunto de prueba (regla 1 de CLAUDE.md; CRISP-DM, fase 5).

El conjunto de prueba se usa UNA sola vez, para la evaluación final, y esa ejecución la
decide una persona. Este módulo lo hace cumplir en el código:

- `exigir_confirmacion_humana()` solo deja seguir si el proceso corre en una terminal
  interactiva y alguien escribe la frase de confirmación. Un agente (por ejemplo, Claude
  Code) ejecuta los comandos sin terminal interactiva, así que no puede pasar este paso,
  ni siquiera enviando la frase por una tubería.
- `registrar_uso()` deja constancia de cada uso en reportes/uso_conjunto_prueba.json
  (se versiona en Git), y `usos_registrados()` permite negarse a repetir.

`preparacion.dividir(..., "prueba")` devuelve los datos de prueba SIN la variable objetivo;
pedirla (`con_objetivo=True`) pasa por este candado.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from alerta_temprana.config import RAIZ

FRASE = "USAR PRUEBA"
REGISTRO = RAIZ / "reportes" / "uso_conjunto_prueba.json"


class UsoDePruebaNoAutorizado(PermissionError):
    """Se intentó usar la variable objetivo del conjunto de prueba sin confirmación humana."""


def exigir_confirmacion_humana(motivo: str) -> None:
    if not sys.stdin.isatty():
        raise UsoDePruebaNoAutorizado(
            "El conjunto de prueba solo se usa con confirmación de una persona, desde una "
            "terminal interactiva. Si sos Claude Code: no ejecutes este paso; pedile a Facundo "
            "que lo corra a mano."
        )
    print(
        f"\n{motivo}\nEl conjunto de prueba se usa una sola vez y sus resultados no se usan para ajustar nada."
    )
    respuesta = input(f'Para continuar, escribí "{FRASE}": ')
    if respuesta.strip() != FRASE:
        raise UsoDePruebaNoAutorizado("Cancelado: no se usó el conjunto de prueba.")


def usos_registrados(registro: Path = REGISTRO) -> list[dict]:
    if not registro.exists():
        return []
    return json.loads(registro.read_text(encoding="utf-8"))


def registrar_uso(detalle: dict, registro: Path = REGISTRO) -> None:
    usos = usos_registrados(registro)
    usos.append({"fecha": datetime.now(UTC).isoformat(timespec="seconds"), **detalle})
    registro.parent.mkdir(parents=True, exist_ok=True)
    registro.write_text(json.dumps(usos, ensure_ascii=False, indent=2), encoding="utf-8")
