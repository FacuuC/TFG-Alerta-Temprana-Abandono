"""Genera las 6 fichas del cuestionario a tutores y docentes (HU-006, tarea 6.4; objetivo 4).

Uso:  python scripts/generar_fichas_cuestionario.py [--version 1.0]

1. Carga el modelo de cierre_1s (versión indicada) y sus umbrales, fijados en validación.
2. Calcula probabilidad, nivel y los 5 factores SHAP de los estudiantes de PRUEBA.
   No calcula ninguna métrica sobre prueba ni toma decisiones con ella: eso queda para
   scripts/evaluar_final.py.
3. Elige 2 casos por nivel al azar con la semilla fija (decisión P7) y los ordena
   alto, bajo, medio, alto, medio, bajo (orden de las secciones del formulario).
4. Guarda reportes/cuestionario/caso_N.png y casos.csv, y marca el modelo como congelado.

Los códigos de las fichas se calculan con SEUDONIMO_CLAVE (del entorno o de .env).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from alerta_temprana.config import RAIZ
from alerta_temprana.datos import variables as V
from alerta_temprana.datos.seudonimizacion import codigo_estudiante, legajo_sintetico
from alerta_temprana.modelo import preparacion as P
from alerta_temprana.modelo.etiquetas import CARRERA, texto_factor
from alerta_temprana.modelo.explicaciones import principales_factores, valores_shap_por_variable
from alerta_temprana.modelo.ficha_imagen import DatosFicha, dibujar_ficha
from alerta_temprana.modelo.persistencia import actualizar_metadatos, cargar_modelo
from alerta_temprana.modelo.umbrales import clasificar_vector

SEMILLA = 42
ORDEN_NIVELES = ["alto", "bajo", "medio", "alto", "medio", "bajo"]
MOMENTO = V.Momento.CIERRE_1S


def _clave() -> str:
    clave = os.environ.get("SEUDONIMO_CLAVE")
    if clave:
        return clave
    from alerta_temprana.config import obtener_configuracion

    return obtener_configuracion().seudonimo_clave


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", default="1.0")
    args = parser.parse_args()

    df = P.cargar_dataset(RAIZ / "data" / "raw" / "data.csv")
    conjunto = P.cargar_particion(RAIZ / "data" / "procesados" / "particion.csv")
    ent, pru = P.dividir(df, conjunto, "entrenamiento"), P.dividir(df, conjunto, "prueba")
    pipeline, meta = cargar_modelo(RAIZ / "modelos", MOMENTO, args.version)
    variables = V.VARIABLES_POR_MOMENTO[MOMENTO]

    probabilidades = pipeline.predict_proba(pru[variables])[:, 1]
    niveles = pd.Series(
        clasificar_vector(probabilidades, meta["umbral_alto"], meta["umbral_medio"]), index=pru.index
    )

    rng = np.random.default_rng(SEMILLA)
    elegidos: dict[str, list[int]] = {}
    for nivel in ("alto", "medio", "bajo"):
        candidatos = np.sort(niveles[niveles == nivel].index.to_numpy())
        elegidos[nivel] = list(rng.choice(candidatos, size=2, replace=False))
    orden = [elegidos[n].pop(0) for n in ORDEN_NIVELES]

    casos = pru.loc[orden]
    shap_casos = valores_shap_por_variable(pipeline, casos[variables], ent[variables])
    clave = _clave()
    hoy = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    fecha = hoy.strftime("%d/%m/%Y")
    salida = RAIZ / "reportes" / "cuestionario"
    filas = []
    for numero, indice in enumerate(orden, start=1):
        fila = casos.loc[indice]
        factores = principales_factores(shap_casos.loc[indice], 5)
        textos = [(texto_factor(f.variable, fila), f.contribucion) for f in factores]
        probabilidad = float(pipeline.predict_proba(casos.loc[[indice], variables])[:, 1][0])
        datos = DatosFicha(
            codigo=codigo_estudiante(legajo_sintetico(indice), clave),
            probabilidad=probabilidad,
            nivel=str(niveles.loc[indice]),
            carrera=CARRERA[int(fila["carrera"])],
            turno="Diurno" if int(fila["turno_diurno"]) == 1 else "Nocturno",
            fecha=fecha,
            modelo=f"modelo v{args.version} (1.er semestre)",
            factores=textos,
            titulo_extra=f"Caso {numero}",
        )
        dibujar_ficha(datos, salida / f"caso_{numero}.png")
        registro = {
            "caso": numero,
            "codigo": datos.codigo,
            "indice_original": int(indice),
            "nivel": datos.nivel,
            "probabilidad": round(probabilidad, 4),
        }
        for f, (texto, contribucion) in zip(factores, textos, strict=True):
            registro[f"factor_{f.orden}"] = texto
            registro[f"contribucion_{f.orden}"] = round(contribucion, 4)
        filas.append(registro)
        print(f"Caso {numero}: {datos.codigo} nivel {datos.nivel} p={probabilidad:.2f}")

    pd.DataFrame(filas).to_csv(salida / "casos.csv", index=False, encoding="utf-8")
    actualizar_metadatos(RAIZ / "modelos", MOMENTO, args.version, congelado_para_cuestionario=hoy.isoformat())
    print(f"Fichas en {salida.relative_to(RAIZ)}; el modelo v{args.version} queda congelado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
