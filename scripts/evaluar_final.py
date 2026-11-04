"""Evaluación final sobre el conjunto de PRUEBA, una sola vez (tareas 2.4 y 2.5).

Uso (lo ejecuta una persona, en PowerShell, con el entorno activado):

    python scripts/evaluar_final.py
    python scripts/evaluar_final.py --ensayo [--salida CARPETA]      # con validación, sin tocar prueba
    python scripts/evaluar_final.py --repetir --motivo "..."         # solo si ya se usó la prueba

Orden, con todo lo que puede fallar ANTES de leer la prueba:
1. Se niega si la prueba ya se usó (registro, informe previo o métricas de prueba en los
   metadatos), salvo --repetir con un motivo.
2. Carga los tres modelos (v1.0), controla sus variables y calcula el SHA-256 de cada pipeline.
3. Vuelve a ajustar la alternativa no elegida de cada momento con entrenamiento y controla
   que reproduzca su AUC-ROC de validación registrado (±0,0005). Si no, se detiene.
4. Lee las etiquetas de prueba: pide la confirmación humana («USAR PRUEBA») y deja
   constancia en reportes/uso_conjunto_prueba.json.
5. Calcula las métricas, las comprobaciones de umbrales, los subgrupos, el AUC-ROC sin
   «sigue cursando» y SHAP; decide la habilitación.
6. Escribe reportes/informe_evaluacion.md y completa metadatos.json de cada modelo (el
   pipeline no se toca).

Con --ensayo hace 2, 3, 5 y 6 sobre VALIDACIÓN, sin candado, sin registrar usos ni modificar
modelos, y escribe el informe fuera del repositorio con el título
«ENSAYO (validación) — no son resultados de prueba».
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from sklearn.metrics import roc_auc_score

from alerta_temprana.config import RAIZ
from alerta_temprana.datos import variables as V
from alerta_temprana.modelo import candado_prueba as C
from alerta_temprana.modelo import evaluacion as E
from alerta_temprana.modelo import preparacion as P
from alerta_temprana.modelo import umbrales as U
from alerta_temprana.modelo.explicaciones import importancia_global, valores_shap_por_variable
from alerta_temprana.modelo.informe_evaluacion import armar_informe
from alerta_temprana.modelo.persistencia import actualizar_metadatos, cargar_modelo, carpeta_modelo

SEMILLA = 42
CAPACIDAD = 0.15
DETECCION = 0.80
RUTA_DATOS = RAIZ / "data" / "raw" / "data.csv"
RUTA_PARTICION = RAIZ / "data" / "procesados" / "particion.csv"
RUTA_MODELOS = RAIZ / "modelos"
RUTA_INFORME = RAIZ / "reportes" / "informe_evaluacion.md"


def ruta_permitida_para_ensayo(ruta: Path, raiz: Path = RAIZ) -> bool:
    """El informe de ensayo va fuera del repositorio o en una ruta que Git ignora."""
    ruta = ruta.resolve()
    if not ruta.is_relative_to(raiz.resolve()):
        return True
    resultado = subprocess.run(
        ["git", "check-ignore", "-q", str(ruta)], cwd=raiz, capture_output=True, check=False
    )
    return resultado.returncode == 0


def _modelos_con_prueba(version: str) -> list[str]:
    con_prueba = []
    for m in V.Momento:
        _, meta = cargar_modelo(RUTA_MODELOS, m, version)
        if meta.get("prueba") is not None:
            con_prueba.append(f"{m.value}/v{version}")
    return con_prueba


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", default="1.0")
    parser.add_argument("--ensayo", action="store_true", help="usar validación en lugar de prueba (no registra nada)")
    parser.add_argument("--salida", type=Path, help="carpeta del informe de ensayo (fuera del repositorio)")
    parser.add_argument("--repetir", action="store_true", help="repetir la evaluación sobre prueba (requiere --motivo)")
    parser.add_argument("--motivo", help="motivo de la repetición (queda en el registro y en el informe)")
    args = parser.parse_args()
    if args.salida and not args.ensayo:
        parser.error("--salida solo se usa con --ensayo")
    if args.ensayo and args.repetir:
        parser.error("--repetir no se usa con --ensayo")

    salida_ensayo = None
    if args.ensayo:
        salida_ensayo = (args.salida or Path(tempfile.gettempdir()) / "alerta_temprana_ensayo").resolve()
        if not ruta_permitida_para_ensayo(salida_ensayo):
            print(f"La salida del ensayo ({salida_ensayo}) está dentro del repositorio y Git no la ignora.")
            return 2

    # 1. Uso único
    if not args.ensayo:
        try:
            E.verificar_uso_previo(
                C.usos_registrados(), RUTA_INFORME.exists(), _modelos_con_prueba(args.version),
                args.repetir, args.motivo,
            )
        except E.UsoRepetidoDePrueba as error:
            print(error)
            return 2

    # 2. Modelos
    df = P.cargar_dataset(RUTA_DATOS)
    conjunto = P.cargar_particion(RUTA_PARTICION)
    ent = P.dividir(df, conjunto, "entrenamiento")
    val = P.dividir(df, conjunto, "validacion")
    modelos = {}
    for m in V.Momento:
        pipeline, meta = cargar_modelo(RUTA_MODELOS, m, args.version)
        variables = V.VARIABLES_POR_MOMENTO[m]
        if meta["variables"] != variables or list(pipeline.feature_names_in_) != variables:
            raise SystemExit(f"El modelo de {m.value} no usa exactamente las variables de su momento.")
        sha = E.sha256(carpeta_modelo(RUTA_MODELOS, m, args.version) / "pipeline.joblib")
        modelos[m] = (pipeline, meta, sha)
        print(f"{m.value}: {meta['algoritmo']}, SHA-256 {sha[:16]}…")

    # 3. Alternativas (antes de leer la prueba)
    alternativas = {}
    for m, (_, meta, _) in modelos.items():
        variables = V.VARIABLES_POR_MOMENTO[m]
        alt = E.describir_alternativa(meta)
        pipe_alt = E.ajustar_alternativa(
            alt, m, SEMILLA, ent[variables], ent[P.OBJETIVO_BINARIO].to_numpy()
        )
        auc_val = float(roc_auc_score(val[P.OBJETIVO_BINARIO], pipe_alt.predict_proba(val[variables])[:, 1]))
        try:
            E.comprobar_alternativa(alt["auc_roc_validacion"], auc_val)
        except E.AlternativaNoReproducible as error:
            print(f"{m.value}: {error}")
            return 3
        alternativas[m] = (alt, pipe_alt, auc_val)
        print(f"{m.value}: alternativa {alt['algoritmo']} reproducida (validación {auc_val:.4f}; registrado {alt['auc_roc_validacion']:.4f})")

    # 4. Datos a evaluar
    ahora = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
    if args.ensayo:
        evaluados = val
    else:
        evaluados = P.dividir(df, conjunto, "prueba", con_objetivo=True)  # confirmación humana
        detalle_uso = {
            "modelos": [f"{m.value}/v{args.version}" for m in V.Momento],
            "sha256": {m.value: modelos[m][2] for m in V.Momento},
            "motivo_repeticion": args.motivo,
        }
        C.registrar_uso({**detalle_uso, "estado": "iniciado"})
    y = evaluados[P.OBJETIVO_BINARIO].to_numpy()
    nombre_conjunto = "validación" if args.ensayo else "prueba"

    # 5. Cálculos
    resultados: list[E.ResultadoMomento] = []
    probabilidad_c1s = None
    for m, (pipeline, meta, sha) in modelos.items():
        variables = V.VARIABLES_POR_MOMENTO[m]
        p = pipeline.predict_proba(evaluados[variables])[:, 1]
        alt, pipe_alt, auc_val_alt = alternativas[m]
        p_alt = pipe_alt.predict_proba(evaluados[variables])[:, 1]
        metricas = E.metricas_alerta(y, p, meta["umbral_medio"])
        habilitado, motivo = E.decidir_habilitacion(m, metricas["auc_roc"], conjunto=nombre_conjunto)
        resultados.append(
            E.ResultadoMomento(
                momento=m, version=args.version, sha256=sha, fecha_entrenamiento=meta["fecha"],
                algoritmo=meta["algoritmo"], hiperparametros=meta["hiperparametros"],
                umbral_alto=meta["umbral_alto"], umbral_medio=meta["umbral_medio"],
                auc_validacion=meta["validacion"]["auc_roc"], metricas=metricas,
                comprobacion=U.comprobar(p, y, meta["umbral_alto"], meta["umbral_medio"]),
                alternativa={
                    "algoritmo": alt["algoritmo"], "hiperparametros": alt["hiperparametros"],
                    "auc_validacion_registrado": alt["auc_roc_validacion"],
                    "auc_validacion_recalculado": auc_val_alt,
                    "metricas": E.metricas_alerta(y, p_alt, meta["umbral_medio"]),
                },
                habilitado=habilitado, motivo_habilitacion=motivo,
            )
        )
        if m is V.Momento.CIERRE_1S:
            probabilidad_c1s = p

    c1s_pipeline, c1s_meta, _ = modelos[V.Momento.CIERRE_1S]
    variables_c1s = V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_1S]
    shap_c1s = valores_shap_por_variable(c1s_pipeline, evaluados[variables_c1s], ent[variables_c1s])
    importancia = importancia_global(shap_c1s)
    resultado = E.ResultadoEvaluacion(
        fecha=ahora, ensayo=args.ensayo, momentos=resultados,
        subgrupos=E.metricas_por_subgrupo(evaluados, y, probabilidad_c1s, c1s_meta["umbral_medio"]),
        cursando=E.auc_sin_cursando(evaluados[V.OBJETIVO], y, probabilidad_c1s),
        importancia=importancia, demograficas=E.revision_demografica(importancia),
        capacidad=CAPACIDAD, deteccion=DETECCION, motivo_repeticion=args.motivo,
    )

    # 6. Informe y registro
    texto = armar_informe(resultado)
    if args.ensayo:
        salida_ensayo.mkdir(parents=True, exist_ok=True)
        ruta = salida_ensayo / "informe_evaluacion_ENSAYO.md"
        ruta.write_text(texto, encoding="utf-8")
        print(f"ENSAYO con validación (no son resultados de prueba): {ruta}")
        return 0

    RUTA_INFORME.write_text(texto, encoding="utf-8")
    for r in resultados:
        cursando = resultado.cursando if r.momento is V.Momento.CIERRE_1S else None
        actualizar_metadatos(RUTA_MODELOS, r.momento, args.version, **E.metadatos_de_prueba(r, ahora, cursando))
    C.registrar_uso({**detalle_uso, "estado": "completado", "informe": "reportes/informe_evaluacion.md"})
    print(pd.DataFrame(
        [{"momento": r.momento.value, "auc_roc": round(r.metricas["auc_roc"], 4),
          "precision": round(r.metricas["precision_alerta"], 3),
          "sensibilidad": round(r.metricas["sensibilidad_alerta"], 3), "habilitado": r.habilitado}
         for r in resultados]
    ).to_string(index=False))
    print(f"Informe en {RUTA_INFORME.relative_to(RAIZ)}; metadatos actualizados; uso registrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
