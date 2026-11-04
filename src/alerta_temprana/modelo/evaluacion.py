"""Evaluación final (tareas 2.4 y 2.5; CRISP-DM, fase 5, etapa B).

Funciones puras que usa scripts/evaluar_final.py. Ninguna lee datos: reciben las
etiquetas y probabilidades ya calculadas, así se pueden probar con datos simulados.

Reglas del documento:
- alerta = nivel alto o medio (probabilidad >= umbral medio);
- el modelo de cierre_1s se habilita solo si su AUC-ROC en prueba supera 0,80; los de
  inscripción y cierre_2s se habilitan con el desempeño obtenido, que queda informado;
- subgrupos (género, edad de ingreso, becario) y AUC-ROC sin «sigue cursando», solo para
  cierre_1s;
- la prueba se usa una sola vez y no se reajusta nada con ella.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline

from alerta_temprana.datos import variables as V
from alerta_temprana.modelo.entrenamiento import pipeline_regresion_logistica, pipeline_xgboost

AUC_MINIMO_CIERRE_1S = 0.80  # meta del objetivo 1 (igual a config.auc_minimo_cierre_1s)
TOLERANCIA_AUC_ALTERNATIVA = 0.0005  # el reajuste puede variar en el 4.º decimal entre sistemas
VARIABLES_DEMOGRAFICAS = ["genero", "edad_ingreso", "estado_civil", "nacionalidad", "desplazado", "internacional"]
PUESTOS_PESO_ALTO = 5  # «peso alto»: estar entre las 5 variables con mayor media |SHAP|


class UsoRepetidoDePrueba(RuntimeError):
    """La evaluación final ya se hizo y no se pidió repetirla en forma explícita."""


class AlternativaNoReproducible(RuntimeError):
    """El reajuste de la alternativa no reproduce su AUC-ROC de validación registrado."""


# --- Guardas que se controlan ANTES de leer la prueba ------------------------------------


def verificar_uso_previo(
    usos: list[dict],
    informe_existe: bool,
    modelos_con_prueba: list[str],
    repetir: bool,
    motivo: str | None,
) -> None:
    """Se niega a evaluar de nuevo sobre prueba salvo `--repetir` con un motivo escrito."""
    antecedentes = []
    if usos:
        antecedentes.append(f"{len(usos)} uso(s) registrado(s) del conjunto de prueba")
    if informe_existe:
        antecedentes.append("ya existe reportes/informe_evaluacion.md")
    if modelos_con_prueba:
        antecedentes.append(f"modelos con métricas de prueba: {', '.join(modelos_con_prueba)}")
    if not antecedentes:
        return
    if not repetir:
        raise UsoRepetidoDePrueba(
            "La evaluación final sobre prueba ya se hizo (" + "; ".join(antecedentes) + "). "
            'El conjunto de prueba se usa una sola vez. Para repetirla a sabiendas: --repetir --motivo "..."'
        )
    if not motivo or not motivo.strip():
        raise UsoRepetidoDePrueba("Para repetir la evaluación hay que dejar el motivo: --motivo \"...\"")


def comprobar_alternativa(
    auc_registrado: float, auc_recalculado: float, tolerancia: float = TOLERANCIA_AUC_ALTERNATIVA
) -> float:
    """Diferencia entre el AUC-ROC de validación registrado y el recalculado; error si supera la tolerancia."""
    diferencia = abs(auc_recalculado - auc_registrado)
    if diferencia > tolerancia:
        raise AlternativaNoReproducible(
            f"AUC-ROC de validación de la alternativa: registrado {auc_registrado:.4f}, recalculado "
            f"{auc_recalculado:.4f} (diferencia {diferencia:.4f} > {tolerancia}). Se detiene antes de leer la prueba."
        )
    return diferencia


def describir_alternativa(metadatos: dict) -> dict:
    """Algoritmo, hiperparámetros y AUC de validación del candidato no elegido.

    Los modelos nuevos lo traen en `alternativa_no_elegida`. El de cierre_1s v1.0 (congelado
    antes de agregar ese campo) eligió XGBoost, así que su alternativa es la regresión
    logística, con el AUC de validación registrado en `validacion.auc_roc_referencia`.
    """
    if "alternativa_no_elegida" in metadatos:
        alt = metadatos["alternativa_no_elegida"]
        return {
            "algoritmo": alt["algoritmo"],
            "hiperparametros": alt["hiperparametros"],
            "auc_roc_validacion": alt["auc_roc_validacion"],
        }
    if metadatos["algoritmo"] != "xgboost":
        raise ValueError("Falta `alternativa_no_elegida` en los metadatos de un modelo de regresión logística")
    return {
        "algoritmo": "regresion_logistica",
        "hiperparametros": {"class_weight": "balanced"},
        "auc_roc_validacion": metadatos["validacion"]["auc_roc_referencia"],
    }


def ajustar_alternativa(
    alternativa: dict, momento: V.Momento, semilla: int, x_ent: pd.DataFrame, y_ent: np.ndarray
) -> Pipeline:
    """Ajusta la alternativa con entrenamiento, con los mismos constructores que modelo/entrenamiento.py."""
    if alternativa["algoritmo"] == "regresion_logistica":
        pipe = pipeline_regresion_logistica(momento, semilla)
    else:
        hiper = {k: v for k, v in alternativa["hiperparametros"].items() if k != "scale_pos_weight"}
        peso_positivo = float((y_ent == 0).sum() / (y_ent == 1).sum())  # igual que en entrenar_momento
        pipe = pipeline_xgboost(momento, semilla, peso_positivo, **hiper)
    return pipe.fit(x_ent, y_ent)


def sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


# --- Métricas ------------------------------------------------------------------------------


def _auc(y: np.ndarray, p: np.ndarray) -> float:
    return float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else float("nan")


def metricas_alerta(y: np.ndarray, p: np.ndarray, umbral_medio: float) -> dict:
    """AUC-ROC, precisión y sensibilidad de la alerta (alto + medio) y la matriz de confusión."""
    y = np.asarray(y).astype(int)
    alerta = (np.asarray(p) >= umbral_medio).astype(int)
    vn, fp, fn, vp = confusion_matrix(y, alerta, labels=[0, 1]).ravel()
    return {
        "n": int(y.size),
        "abandonos": int(y.sum()),
        "auc_roc": _auc(y, p),
        "precision_alerta": float(precision_score(y, alerta, zero_division=np.nan)),
        "sensibilidad_alerta": float(recall_score(y, alerta, zero_division=np.nan)),
        "verdaderos_positivos": int(vp),
        "falsos_positivos": int(fp),
        "falsos_negativos": int(fn),
        "verdaderos_negativos": int(vn),
    }


def grupos_de_subgrupo(datos: pd.DataFrame) -> dict[str, pd.Series]:
    """Etiqueta de cada estudiante en los tres subgrupos del documento."""
    return {
        "Género": datos["genero"].map({0: "femenino", 1: "masculino"}),
        "Edad de ingreso": datos["edad_ingreso"].map(V.tramo_edad),
        "Becario": datos["becario"].map({0: "no", 1: "sí"}),
    }


ORDEN_GRUPOS = {
    "Género": ["femenino", "masculino"],
    "Edad de ingreso": [c[0] for c in V.CORTES_EDAD],
    "Becario": ["no", "sí"],
}


def metricas_por_subgrupo(datos: pd.DataFrame, y: np.ndarray, p: np.ndarray, umbral_medio: float) -> pd.DataFrame:
    """AUC-ROC, sensibilidad y precisión por género, tramo de edad y condición de becario.

    Un subgrupo con una sola clase queda con AUC-ROC no definido (NaN), sin romper el cálculo.
    """
    y = np.asarray(y)
    p = np.asarray(p)
    filas = []
    for subgrupo, etiquetas in grupos_de_subgrupo(datos).items():
        etiquetas = etiquetas.to_numpy()
        for grupo in ORDEN_GRUPOS[subgrupo]:
            mascara = etiquetas == grupo
            if not mascara.any():
                continue
            m = metricas_alerta(y[mascara], p[mascara], umbral_medio)
            filas.append({"subgrupo": subgrupo, "grupo": grupo, **m})
    return pd.DataFrame(filas)


def auc_sin_cursando(situacion_final: pd.Series | np.ndarray, y: np.ndarray, p: np.ndarray) -> dict:
    """AUC-ROC con todos y sin quienes siguen cursando (control de la etiqueta)."""
    situacion = np.asarray(situacion_final)
    sin = situacion != "cursando"
    return {
        "auc_roc_con_cursando": _auc(np.asarray(y), np.asarray(p)),
        "auc_roc_sin_cursando": _auc(np.asarray(y)[sin], np.asarray(p)[sin]),
        "n_con_cursando": int(situacion.size),
        "n_sin_cursando": int(sin.sum()),
    }


def revision_demografica(importancia: pd.Series, puestos: int = PUESTOS_PESO_ALTO) -> pd.DataFrame:
    """Puesto y peso medio (SHAP) de cada variable demográfica; «peso alto» si está entre las primeras."""
    ranking = importancia.sort_values(ascending=False)
    puesto = {v: i + 1 for i, v in enumerate(ranking.index)}
    filas = [
        {
            "variable": v,
            "puesto": puesto[v],
            "peso_medio": float(ranking[v]),
            "peso_alto": puesto[v] <= puestos,
        }
        for v in VARIABLES_DEMOGRAFICAS
        if v in puesto
    ]
    return pd.DataFrame(filas).sort_values("puesto").reset_index(drop=True)


def decidir_habilitacion(
    momento: V.Momento, auc_roc: float, auc_minimo: float = AUC_MINIMO_CIERRE_1S, conjunto: str = "prueba"
) -> tuple[bool, str]:
    """cierre_1s: solo si AUC-ROC > mínimo (estricto). inscripcion y cierre_2s: siempre, con el desempeño informado."""
    auc_txt = f"{auc_roc:.4f}".replace(".", ",")
    minimo_txt = f"{auc_minimo:.2f}".replace(".", ",")
    if momento is V.Momento.CIERRE_1S:
        if auc_roc > auc_minimo:
            return True, f"AUC-ROC en {conjunto} {auc_txt} > {minimo_txt}: alcanza la meta y se habilita."
        return False, f"AUC-ROC en {conjunto} {auc_txt} ≤ {minimo_txt}: no alcanza la meta y no se habilita."
    return True, f"Se habilita con el desempeño obtenido (AUC-ROC en {conjunto} {auc_txt}), que queda informado."


# --- Resultado que consume el informe ------------------------------------------------------


@dataclass
class ResultadoMomento:
    momento: V.Momento
    version: str
    sha256: str
    fecha_entrenamiento: str
    algoritmo: str
    hiperparametros: dict
    umbral_alto: float
    umbral_medio: float
    auc_validacion: float
    metricas: dict
    comprobacion: dict
    alternativa: dict  # algoritmo, hiperparametros, auc_validacion_registrado/recalculado, metricas
    habilitado: bool
    motivo_habilitacion: str


@dataclass
class ResultadoEvaluacion:
    fecha: datetime
    ensayo: bool  # True: se usó validación en lugar de prueba (no son resultados de prueba)
    momentos: list[ResultadoMomento]
    subgrupos: pd.DataFrame
    cursando: dict
    importancia: pd.Series
    demograficas: pd.DataFrame
    capacidad: float
    deteccion: float
    motivo_repeticion: str | None = None
    extra: dict = field(default_factory=dict)

    @property
    def conjunto(self) -> str:
        return "validación" if self.ensayo else "prueba"


def metadatos_de_prueba(r: ResultadoMomento, fecha: datetime, cursando: dict | None) -> dict:
    """Lo que se agrega a metadatos.json después de la evaluación final (tarea 2.5)."""

    def limpio(d: dict) -> dict:
        return {k: (None if isinstance(v, float) and np.isnan(v) else (round(v, 4) if isinstance(v, float) else v))
                for k, v in d.items()}

    prueba = {
        "fecha_evaluacion": fecha.isoformat(timespec="seconds"),
        **limpio(r.metricas),
        **limpio(r.comprobacion),
        "alternativa_no_elegida": {
            "algoritmo": r.alternativa["algoritmo"],
            **limpio(r.alternativa["metricas"]),
        },
    }
    if cursando is not None:
        prueba.update(limpio(cursando))
    return {
        "prueba": prueba,
        "habilitado": r.habilitado,
        "motivo_habilitacion": r.motivo_habilitacion,
        "fecha_evaluacion": fecha.isoformat(timespec="seconds"),
        "sha256_pipeline": r.sha256,
    }
