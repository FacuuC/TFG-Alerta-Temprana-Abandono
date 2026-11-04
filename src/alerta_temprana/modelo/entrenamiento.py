"""Modelado y elección del modelo con el conjunto de validación (tareas 2.3 y 2.4, etapa A).

Para cada momento se entrenan una regresión logística de referencia y XGBoost con una
grilla acotada. Ambos tratan el desbalance con pesos de clase (sin casos sintéticos).
La elección se hace con el AUC-ROC de VALIDACIÓN: XGBoost solo si supera a la referencia.
El conjunto de prueba no aparece en este módulo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from alerta_temprana.datos import variables as V
from alerta_temprana.modelo.preparacion import OBJETIVO_BINARIO, construir_preprocesador

# Grilla acotada de los tres hiperparámetros del documento. La primera versión
# (profundidad 3-5, tasa 0,05-0,1, árboles 200-400) dejó el mejor resultado en el borde
# (profundidad 3, 200 árboles, tasa 0,1), por eso se extendió hacia árboles más simples,
# menos árboles y una tasa menor (03/11, ver reportes/validacion_cierre_1s.md).
GRILLA_XGBOOST: dict[str, list] = {
    "max_depth": [2, 3, 4, 5],
    "learning_rate": [0.03, 0.05, 0.1],
    "n_estimators": [100, 200, 400],
}


@dataclass
class Candidato:
    algoritmo: str  # "regresion_logistica" o "xgboost"
    hiperparametros: dict
    auc_validacion: float
    pipeline: Pipeline = field(repr=False)


@dataclass
class ResultadoEntrenamiento:
    momento: V.Momento
    referencia: Candidato
    grilla: list[Candidato]
    elegido: Candidato

    def tabla_grilla(self) -> pd.DataFrame:
        filas = [{**c.hiperparametros, "auc_validacion": c.auc_validacion} for c in self.grilla]
        return pd.DataFrame(filas).sort_values("auc_validacion", ascending=False)


def _xy(df: pd.DataFrame, momento: V.Momento) -> tuple[pd.DataFrame, np.ndarray]:
    return df[V.VARIABLES_POR_MOMENTO[momento]], df[OBJETIVO_BINARIO].to_numpy()


def pipeline_regresion_logistica(momento: V.Momento, semilla: int) -> Pipeline:
    modelo = LogisticRegression(class_weight="balanced", max_iter=5000, random_state=semilla)
    return Pipeline([("preprocesador", construir_preprocesador(momento)), ("modelo", modelo)])


def pipeline_xgboost(momento: V.Momento, semilla: int, peso_positivo: float, **hiper) -> Pipeline:
    modelo = XGBClassifier(
        objective="binary:logistic",
        eval_metric="auc",
        tree_method="hist",
        scale_pos_weight=peso_positivo,
        random_state=semilla,
        n_jobs=1,  # reproducible entre equipos
        **hiper,
    )
    return Pipeline([("preprocesador", construir_preprocesador(momento)), ("modelo", modelo)])


def entrenar_momento(
    entrenamiento: pd.DataFrame, validacion: pd.DataFrame, momento: V.Momento, semilla: int
) -> ResultadoEntrenamiento:
    """Entrena la referencia y la grilla de XGBoost y elige con el AUC-ROC de validación."""
    x_ent, y_ent = _xy(entrenamiento, momento)
    x_val, y_val = _xy(validacion, momento)

    ref = pipeline_regresion_logistica(momento, semilla).fit(x_ent, y_ent)
    referencia = Candidato(
        "regresion_logistica",
        {"class_weight": "balanced"},
        float(roc_auc_score(y_val, ref.predict_proba(x_val)[:, 1])),
        ref,
    )

    peso_positivo = float((y_ent == 0).sum() / (y_ent == 1).sum())
    grilla: list[Candidato] = []
    claves = list(GRILLA_XGBOOST)
    for valores in product(*GRILLA_XGBOOST.values()):
        hiper = dict(zip(claves, valores, strict=True))
        pipe = pipeline_xgboost(momento, semilla, peso_positivo, **hiper).fit(x_ent, y_ent)
        auc = float(roc_auc_score(y_val, pipe.predict_proba(x_val)[:, 1]))
        grilla.append(Candidato("xgboost", {**hiper, "scale_pos_weight": round(peso_positivo, 4)}, auc, pipe))

    mejor_xgb = max(grilla, key=lambda c: c.auc_validacion)
    elegido = mejor_xgb if mejor_xgb.auc_validacion > referencia.auc_validacion else referencia
    return ResultadoEntrenamiento(momento, referencia, grilla, elegido)
