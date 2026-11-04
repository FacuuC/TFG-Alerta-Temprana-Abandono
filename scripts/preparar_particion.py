"""Genera y guarda la partición 60/20/20 (tarea 2.2).

Uso:  python scripts/preparar_particion.py [--forzar]

Escribe data/procesados/particion.csv (indice_original, conjunto). Si ya existe, no la
toca: la partición se fija una sola vez y la usan todos los momentos y scripts.
"""

from __future__ import annotations

import argparse
import sys

from alerta_temprana.config import RAIZ
from alerta_temprana.modelo import preparacion as P

RUTA_DATOS = RAIZ / "data" / "raw" / "data.csv"
RUTA_PARTICION = RAIZ / "data" / "procesados" / "particion.csv"
SEMILLA = 42  # igual a SEMILLA de .env.example; fija para que la partición sea reproducible


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--forzar", action="store_true", help="regenerar aunque exista (cambia todos los resultados)"
    )
    args = parser.parse_args()

    df = P.cargar_dataset(RUTA_DATOS)
    if RUTA_PARTICION.exists() and not args.forzar:
        conjunto = P.cargar_particion(RUTA_PARTICION)
        print(f"La partición ya existe ({RUTA_PARTICION.relative_to(RAIZ)}); no se modifica.")
    else:
        conjunto = P.crear_particion(df, SEMILLA)
        P.guardar_particion(conjunto, RUTA_PARTICION)
        print(f"Partición guardada en {RUTA_PARTICION.relative_to(RAIZ)}")

    resumen = df.groupby(conjunto)[P.OBJETIVO_BINARIO].agg(
        registros="size", abandonos="sum", proporcion="mean"
    )
    print(resumen.loc[list(P.CONJUNTOS)].round(4).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
