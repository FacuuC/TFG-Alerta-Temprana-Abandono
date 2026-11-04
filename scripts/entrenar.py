"""Entrena y elige el modelo de un momento con el conjunto de validación (tareas 2.3, 2.4 etapa A y 4.1).

Uso:  python scripts/entrenar.py --momento cierre_1s [--version 1.0]

Hace, solo con entrenamiento y validación:
1. regresión logística de referencia y grilla acotada de XGBoost;
2. elección por AUC-ROC de validación (XGBoost solo si supera a la referencia);
3. umbrales alto y medio sobre las probabilidades de validación;
4. comprobaciones de los umbrales en validación e importancia global SHAP;
5. guarda el pipeline elegido en modelos/<momento>/v<version>/ (sin habilitar) y el
   informe en reportes/validacion_<momento>.md.

NO usa el conjunto de prueba. Las métricas de prueba y la habilitación las agrega
scripts/evaluar_final.py, una sola vez.
"""

from __future__ import annotations

import argparse
import json
import sys

from sklearn.metrics import precision_score, recall_score

from alerta_temprana import formato as F
from alerta_temprana.config import RAIZ
from alerta_temprana.datos import variables as V
from alerta_temprana.modelo import preparacion as P
from alerta_temprana.modelo import umbrales as U
from alerta_temprana.modelo.entrenamiento import GRILLA_XGBOOST, entrenar_momento
from alerta_temprana.modelo.etiquetas import NOMBRES
from alerta_temprana.modelo.explicaciones import importancia_global, valores_shap_por_variable
from alerta_temprana.modelo.persistencia import guardar_modelo

SEMILLA = 42
CAPACIDAD = 0.15  # supuesto del caso modelado (Objetivos)
DETECCION = 0.80
RUTA_DATOS = RAIZ / "data" / "raw" / "data.csv"
RUTA_PARTICION = RAIZ / "data" / "procesados" / "particion.csv"


_pct = F.porcentaje
_num = F.decimal


def _alternativa_no_elegida(resultado) -> dict:
    """El candidato que no se eligió (la referencia o el mejor XGBoost), para informarlo en prueba."""
    mejor_xgb = max(resultado.grilla, key=lambda c: c.auc_validacion)
    alternativa = resultado.referencia if resultado.elegido is mejor_xgb else mejor_xgb
    return {
        "algoritmo": alternativa.algoritmo,
        "hiperparametros": alternativa.hiperparametros,
        "auc_roc_validacion": round(alternativa.auc_validacion, 4),
    }


def _aviso_borde(resultado) -> list[str]:
    """Si el mejor XGBoost queda en un extremo de la grilla, se informa (no se extiende la grilla)."""
    mejor = max(resultado.grilla, key=lambda c: c.auc_validacion).hiperparametros
    en_borde = [
        f"{clave} = {mejor[clave]}"
        for clave, valores in GRILLA_XGBOOST.items()
        if mejor[clave] in (min(valores), max(valores))
    ]
    if not en_borde:
        return ["El mejor XGBoost quedó dentro de la grilla (ningún hiperparámetro en un extremo)."]
    return [
        f"El mejor XGBoost quedó en el borde de la grilla en: {', '.join(en_borde)}. Se informa y no se",
        "extiende la grilla, para usar la misma en los tres momentos.",
    ]


def _parrafo_grilla(momento: V.Momento) -> list[str]:
    if momento is V.Momento.CIERRE_1S:
        return [
            "La primera grilla (profundidad 3 a 5, tasa 0,05 y 0,1, 200 y 400 árboles) dejó su mejor",
            "resultado en el borde (profundidad 3, 200 árboles, tasa 0,1; AUC-ROC 0,8833, por debajo de la",
            "referencia). Por eso se extendió hacia modelos más simples. La regla de elección no cambió.",
        ]
    return [
        "Se usa la misma grilla que en el cierre del 1.er semestre (extendida el 03/11, antes de entrenar",
        "este momento), sin cambios: la grilla es la misma para los tres momentos.",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--momento", required=True, choices=[m.value for m in V.Momento])
    parser.add_argument("--version", default="1.0")
    args = parser.parse_args()
    momento = V.Momento(args.momento)

    df = P.cargar_dataset(RUTA_DATOS)
    conjunto = P.cargar_particion(RUTA_PARTICION)
    ent, val = P.dividir(df, conjunto, "entrenamiento"), P.dividir(df, conjunto, "validacion")

    print(f"Entrenando {momento.value}: {len(ent)} de entrenamiento, {len(val)} de validación…")
    resultado = entrenar_momento(ent, val, momento, SEMILLA)
    elegido = resultado.elegido

    x_val = val[V.VARIABLES_POR_MOMENTO[momento]]
    y_val = val[P.OBJETIVO_BINARIO].to_numpy()
    p_val = elegido.pipeline.predict_proba(x_val)[:, 1]
    alto = U.umbral_alto(p_val, CAPACIDAD)
    medio = U.umbral_medio(p_val, y_val, DETECCION)
    if medio > alto:
        raise SystemExit(f"El umbral medio ({medio:.4f}) quedó por encima del alto ({alto:.4f}); revisar.")
    control = U.comprobar(p_val, y_val, alto, medio)
    alerta_val = (p_val >= medio).astype(int)
    precision_val = float(precision_score(y_val, alerta_val))
    sensibilidad_val = float(recall_score(y_val, alerta_val))

    shap_val = valores_shap_por_variable(elegido.pipeline, x_val, ent[V.VARIABLES_POR_MOMENTO[momento]])
    importancia = importancia_global(shap_val)

    metadatos = {
        "algoritmo": elegido.algoritmo,
        "hiperparametros": elegido.hiperparametros,
        "semilla": SEMILLA,
        "particion": "data/procesados/particion.csv (60/20/20 estratificada)",
        "validacion": {
            "auc_roc": round(elegido.auc_validacion, 4),
            "auc_roc_referencia": round(resultado.referencia.auc_validacion, 4),
            "precision_alerta": round(precision_val, 4),
            "sensibilidad_alerta": round(sensibilidad_val, 4),
            **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in control.items()},
        },
        # Sin redondear: el umbral medio es la probabilidad exacta de un abandono, y redondearlo
        # hacia arriba lo deja afuera (la detección bajaba de 80,0 % a 79,6 %; corregido el 04/11).
        "umbral_alto": float(alto),
        "umbral_medio": float(medio),
        "capacidad_tutorias": CAPACIDAD,
        "deteccion_minima": DETECCION,
        "alternativa_no_elegida": _alternativa_no_elegida(resultado),
        "prueba": None,  # lo completa scripts/evaluar_final.py
    }
    carpeta = guardar_modelo(RAIZ / "modelos", momento, args.version, elegido.pipeline, metadatos)

    # Informe de validación
    reportes = RAIZ / "reportes"
    reportes.mkdir(exist_ok=True)
    grilla = resultado.tabla_grilla()
    lineas = [
        f"# Informe de validación: {V.ETIQUETA_MOMENTO[momento]} (modelo v{args.version})",
        "",
        "Generado por `scripts/entrenar.py`. Usa **solo entrenamiento y validación**; el conjunto de",
        "prueba no se usó para nada de lo que aparece acá.",
        "",
        f"- Registros: {len(ent)} de entrenamiento y {len(val)} de validación; proporción de abandono "
        f"{_pct(ent[P.OBJETIVO_BINARIO].mean())} y {_pct(y_val.mean())}.",
        f"- Variables del momento: {len(V.VARIABLES_POR_MOMENTO[momento])}.",
        "- Desbalance: pesos de clase (`class_weight=balanced` en la regresión logística y "
        "`scale_pos_weight` en XGBoost), sin casos sintéticos.",
        "",
        "## Elección del modelo (AUC-ROC en validación)",
        "",
        "| Modelo | AUC-ROC validación |",
        "|---|---|",
        f"| Regresión logística (referencia) | {_num(resultado.referencia.auc_validacion)} |",
        f"| Mejor XGBoost de la grilla | {_num(max(c.auc_validacion for c in resultado.grilla))} |",
        "",
        f"**Elegido: {elegido.algoritmo.replace('_', ' ')}** "
        f"({'supera' if elegido.algoritmo == 'xgboost' else 'XGBoost no supera'} a la referencia).",
        f"Hiperparámetros: `{json.dumps(elegido.hiperparametros)}`.",
        "",
        *_parrafo_grilla(momento),
        "",
        *_aviso_borde(resultado),
        "",
        f"### Grilla de XGBoost ({len(resultado.grilla)} combinaciones: "
        + ", ".join(f"{k} {v}" for k, v in GRILLA_XGBOOST.items())
        + ")",
        "",
        "| max_depth | learning_rate | n_estimators | AUC-ROC validación |",
        "|---|---|---|---|",
    ]
    for _, fila in grilla.iterrows():
        lineas.append(
            f"| {int(fila['max_depth'])} | {_num(fila['learning_rate'], 2)} | {int(fila['n_estimators'])} | "
            f"{_num(fila['auc_validacion'])} |"
        )
    lineas += [
        "",
        "## Umbrales (fijados con validación)",
        "",
        f"- Umbral alto: **{_num(alto)}** (nivel alto ≤ {_pct(CAPACIDAD)} de los estudiantes).",
        f"- Umbral medio: **{_num(medio)}** (alto + medio detectan ≥ {_pct(DETECCION)} de los abandonos).",
        "",
        "| Comprobación en validación | Valor | Regla |",
        "|---|---|---|",
        f"| Estudiantes en nivel alto | {_pct(control['proporcion_alto'])} | ≤ {_pct(CAPACIDAD)} |",
        f"| Abandonos detectados (alto + medio) | {_pct(control['deteccion_alto_medio'])} | ≥ {_pct(DETECCION)} |",
        f"| Abandono observado por nivel (alto / medio / bajo) | {_pct(control['tasa_abandono_alto'])} / "
        f"{_pct(control['tasa_abandono_medio'])} / {_pct(control['tasa_abandono_bajo'])} | decreciente: "
        f"{'sí' if control['decreciente'] else 'no'} |",
        f"| Estudiantes en nivel medio / bajo | {_pct(control['proporcion_medio'])} / {_pct(control['proporcion_bajo'])} | — |",
        f"| Precisión y sensibilidad de la alerta (alto + medio) | {_num(precision_val, 3)} / {_num(sensibilidad_val, 3)} | — |",
        "",
        "## Variables que más pesan en promedio (SHAP, validación)",
        "",
        "Media del valor absoluto de SHAP por variable. Muestra cuánto pesa cada variable en las",
        "estimaciones del modelo, no las causas del abandono.",
        "",
        "| Variable | Peso medio |",
        "|---|---|",
    ]
    for variable, peso in importancia.head(10).items():
        lineas.append(f"| {NOMBRES[variable]} | {_num(peso, 3)} |")
    lineas += [
        "",
        f"Modelo guardado en `{carpeta.relative_to(RAIZ).as_posix()}` (sin habilitar hasta la evaluación final).",
    ]
    (reportes / f"validacion_{momento.value}.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print(
        f"Elegido: {elegido.algoritmo} — AUC validación {elegido.auc_validacion:.4f} "
        f"(referencia {resultado.referencia.auc_validacion:.4f})"
    )
    print(f"Umbrales: alto {alto:.4f}, medio {medio:.4f}; control en validación: {control}")
    print(f"Guardado en {carpeta.relative_to(RAIZ)}; informe en reportes/validacion_{momento.value}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
