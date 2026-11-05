"""Genera los archivos de carga simulados en data/cargas/ (HU-001; decisión P2).

Uso:  python scripts/generar_cargas.py

Escribe exportacion_inscripcion.csv, exportacion_cierre_1s.csv y exportacion_cierre_2s.csv
con los estudiantes del conjunto de prueba (partición guardada), sin la situación final
y con identificadores sintéticos. Después comprueba que los tres pasen la validación de la
carga sin registros rechazados. No toca la base de datos.
"""

from __future__ import annotations

import sys

from alerta_temprana.config import RAIZ, obtener_configuracion
from alerta_temprana.datos.carga import procesar_archivo
from alerta_temprana.datos.cargas_simuladas import generar_cargas
from alerta_temprana.datos.variables import ETIQUETA_MOMENTO


def main() -> int:
    rutas = generar_cargas(
        RAIZ / "data" / "raw" / "data.csv",
        RAIZ / "data" / "procesados" / "particion.csv",
        RAIZ / "data" / "cargas",
    )
    clave = obtener_configuracion().seudonimo_clave
    correcto = True
    for momento, ruta in rutas.items():
        resultado = procesar_archivo(ruta.read_bytes(), momento, clave)
        print(
            f"{ETIQUETA_MOMENTO[momento]:<26} {ruta.relative_to(RAIZ)}: "
            f"{resultado.registros_validos} válidos, {resultado.registros_rechazados} rechazados"
        )
        correcto &= resultado.registros_rechazados == 0
    if not correcto:
        print("Hay registros rechazados: revisá los rangos de datos/validacion.py.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
