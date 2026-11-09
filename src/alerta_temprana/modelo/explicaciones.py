"""Explicaciones individuales con SHAP (HU-006, tarea 6.1).

Los valores SHAP muestran cuánto pesa cada variable en la estimación de un estudiante
(en la escala log-odds del modelo): positivo aumenta el riesgo estimado, negativo lo
disminuye. NO indican causas del abandono.

Las columnas one-hot de una misma variable se suman, para que los factores sean
variables comprensibles («Carrera») y no columnas técnicas («carrera_9500»).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap
from sklearn.pipeline import Pipeline

from alerta_temprana.modelo.preparacion import variable_de_cada_columna


@dataclass(frozen=True)
class Factor:
    orden: int
    variable: str
    contribucion: float  # valor SHAP sumado por variable

    @property
    def aumenta_riesgo(self) -> bool:
        return self.contribucion > 0


def valores_shap_por_variable(
    pipeline: Pipeline, x: pd.DataFrame, fondo: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Matriz estudiantes × variables originales con el valor SHAP de cada variable.

    `fondo` es el conjunto de referencia (entrenamiento) que usa el explicador lineal
    cuando el modelo elegido es la regresión logística; XGBoost no lo necesita, y la
    plataforma, que no tiene los datos de entrenamiento, no lo pasa.
    """
    preprocesador = pipeline.named_steps["preprocesador"]
    modelo = pipeline.named_steps["modelo"]
    xt = preprocesador.transform(x)
    if modelo.__class__.__name__ == "XGBClassifier":
        explicador = shap.TreeExplainer(modelo)
    else:
        if fondo is None:
            raise ValueError(
                "La explicación de una regresión logística necesita el conjunto de entrenamiento "
                "como referencia (fondo)."
            )
        fondo_t = preprocesador.transform(fondo)
        explicador = shap.LinearExplainer(modelo, shap.maskers.Independent(fondo_t, max_samples=len(fondo_t)))
    valores = np.asarray(explicador.shap_values(xt))
    if valores.ndim == 3:  # algunas versiones devuelven una matriz por clase
        valores = valores[..., 1]
    origen = variable_de_cada_columna(preprocesador)
    por_columna = pd.DataFrame(valores, index=x.index, columns=origen)
    return por_columna.T.groupby(level=0, sort=False).sum().T


def principales_factores(fila_shap: pd.Series, cantidad: int = 5) -> list[Factor]:
    """Los `cantidad` factores con mayor peso absoluto, de mayor a menor."""
    orden = fila_shap.abs().sort_values(ascending=False).index[:cantidad]
    return [Factor(i + 1, variable, float(fila_shap[variable])) for i, variable in enumerate(orden)]


def importancia_global(shap_por_variable: pd.DataFrame) -> pd.Series:
    """Media del valor absoluto de SHAP por variable (para el informe, no para la ficha)."""
    return shap_por_variable.abs().mean().sort_values(ascending=False)
