"""Seudonimización de estudiantes (HU-001, criterio 4; decisión P1 del 03/11).

El código es `EST-` + los primeros 8 caracteres hexadecimales (en mayúscula) del
HMAC-SHA256 del legajo con la clave secreta SEUDONIMO_CLAVE. El mismo legajo da siempre
el mismo código, así las cargas sucesivas actualizan al mismo estudiante, y sin la clave
no se puede recalcular. La plataforma no guarda el legajo ni una tabla de correspondencia.
"""

from __future__ import annotations

import hashlib
import hmac

PREFIJO = "EST-"
LARGO_HEX = 8  # 12 caracteres en total: VARCHAR(12) de la Tabla 32


def codigo_estudiante(legajo: str, clave: str) -> str:
    if not clave:
        raise ValueError("Falta la clave de seudonimización (SEUDONIMO_CLAVE)")
    huella = hmac.new(clave.encode("utf-8"), str(legajo).strip().encode("utf-8"), hashlib.sha256).hexdigest()
    return PREFIJO + huella[:LARGO_HEX].upper()


def legajo_sintetico(indice_original: int) -> str:
    """Legajo ficticio y estable para los registros del dataset (los archivos de carga simulados)."""
    return f"L{int(indice_original) + 1:05d}"
