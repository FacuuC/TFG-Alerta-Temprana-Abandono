"""Guarda los umbrales exactos (sin redondear) en metadatos.json (corrección del 04/11).

Uso:  python scripts/corregir_umbrales.py [--version 1.0]

`entrenar.py` guardaba los umbrales redondeados a 6 decimales. El umbral medio es la
probabilidad exacta de un abandono de validación; redondeado hacia arriba, ese estudiante
quedaba debajo y alto + medio detectaban el 79,6 % en lugar del 80,0 % (inscripción y
cierre_1s). Este script:

1. recalcula los dos umbrales con las probabilidades de VALIDACIÓN (misma regla que entrenar.py);
2. comprueba que, redondeados a 6 decimales, son los guardados (es decir, que el modelo es
   el mismo); si no, se detiene sin cambiar nada;
3. reemplaza solo `umbral_alto` y `umbral_medio` y deja constancia en `correccion_umbrales`.

No usa el conjunto de prueba ni modifica `pipeline.joblib`. Si los umbrales ya son exactos, no hace nada.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

import numpy as np

from alerta_temprana.config import RAIZ
from alerta_temprana.datos import variables as V
from alerta_temprana.modelo import preparacion as P
from alerta_temprana.modelo import umbrales as U
from alerta_temprana.modelo.persistencia import actualizar_metadatos, cargar_modelo


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", default="1.0")
    args = parser.parse_args()

    df = P.cargar_dataset(RAIZ / "data" / "raw" / "data.csv")
    val = P.dividir(df, P.cargar_particion(RAIZ / "data" / "procesados" / "particion.csv"), "validacion")
    y = val[P.OBJETIVO_BINARIO].to_numpy()

    for momento in V.Momento:
        pipeline, meta = cargar_modelo(RAIZ / "modelos", momento, args.version)
        p = pipeline.predict_proba(val[V.VARIABLES_POR_MOMENTO[momento]])[:, 1]
        alto = U.umbral_alto(p, meta["capacidad_tutorias"])
        medio = U.umbral_medio(p, y, meta["deteccion_minima"])
        guardados = {"umbral_alto": meta["umbral_alto"], "umbral_medio": meta["umbral_medio"]}
        if guardados == {"umbral_alto": alto, "umbral_medio": medio}:
            print(f"{momento.value}: los umbrales ya son exactos; sin cambios.")
            continue
        if round(alto, 6) != round(guardados["umbral_alto"], 6) or round(medio, 6) != round(guardados["umbral_medio"], 6):
            print(f"{momento.value}: los umbrales recalculados no coinciden con los guardados; no se cambia nada.")
            return 1
        deteccion_antes = float(np.mean(p[y == 1] >= guardados["umbral_medio"]))
        deteccion_despues = float(np.mean(p[y == 1] >= medio))
        actualizar_metadatos(
            RAIZ / "modelos", momento, args.version,
            umbral_alto=float(alto),
            umbral_medio=float(medio),
            correccion_umbrales={
                "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
                "motivo": "Los umbrales se habían guardado redondeados a 6 decimales; se guardan los valores "
                "exactos calculados con validación. El pipeline no cambia.",
                "anteriores": guardados,
                "deteccion_validacion_antes": round(deteccion_antes, 4),
                "deteccion_validacion_despues": round(deteccion_despues, 4),
            },
        )
        print(
            f"{momento.value}: alto {guardados['umbral_alto']} -> {alto!r}; medio {guardados['umbral_medio']} -> {medio!r}; "
            f"detección en validación {deteccion_antes:.4f} -> {deteccion_despues:.4f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
