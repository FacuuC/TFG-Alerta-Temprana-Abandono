"""Umbrales y niveles de urgencia (HU-004, tareas 4.1 y 4.2).

Reglas del documento (Objetivos y CRISP-DM, fase 5):
- umbral alto: el nivel alto no supera la capacidad supuesta del Programa de Tutorías
  (15 % de los estudiantes);
- umbral medio: entre alto y medio se detecta al menos el 80 % de los abandonos.
Ambos se fijan con el conjunto de VALIDACIÓN.
"""

from __future__ import annotations

import numpy as np

NIVELES = ("alto", "medio", "bajo")


def umbral_alto(probabilidades: np.ndarray, capacidad: float) -> float:
    """Menor probabilidad t tal que la proporción de estudiantes con p >= t no supere `capacidad`."""
    p = np.asarray(probabilidades, dtype=float)
    candidatos = np.unique(p)[::-1]  # de mayor a menor
    elegido = None
    for t in candidatos:
        if np.mean(p >= t) <= capacidad:
            elegido = t
        else:
            break
    if elegido is None:
        raise ValueError("Ningún umbral deja el nivel alto dentro de la capacidad (hay empates en el máximo)")
    return float(elegido)


def umbral_medio(probabilidades: np.ndarray, y: np.ndarray, deteccion: float) -> float:
    """Mayor probabilidad t tal que, entre los abandonos, la proporción con p >= t sea al menos `deteccion`."""
    p = np.asarray(probabilidades, dtype=float)
    positivos = np.sort(p[np.asarray(y) == 1])
    if positivos.size == 0:
        raise ValueError("No hay abandonos para fijar el umbral medio")
    indice = int(np.floor((1 - deteccion) * positivos.size + 1e-9))
    t = float(positivos[indice])
    assert np.mean(positivos >= t) >= deteccion
    return t


def clasificar(probabilidad: float, alto: float, medio: float) -> str:
    """Nivel de urgencia: alto si p >= alto; medio si medio <= p < alto; bajo en otro caso."""
    if probabilidad >= alto:
        return "alto"
    if probabilidad >= medio:
        return "medio"
    return "bajo"


def clasificar_vector(probabilidades: np.ndarray, alto: float, medio: float) -> np.ndarray:
    p = np.asarray(probabilidades, dtype=float)
    return np.where(p >= alto, "alto", np.where(p >= medio, "medio", "bajo"))


def comprobar(
    probabilidades: np.ndarray, y: np.ndarray, alto: float, medio: float
) -> dict[str, float | bool]:
    """Las tres comprobaciones del documento sobre un conjunto (en el informe: validación; en la evaluación final: prueba)."""
    niveles = clasificar_vector(probabilidades, alto, medio)
    y = np.asarray(y)
    proporcion_alto = float(np.mean(niveles == "alto"))
    deteccion = float(np.mean(np.isin(niveles[y == 1], ["alto", "medio"])))
    tasa = {n: float(y[niveles == n].mean()) if np.any(niveles == n) else float("nan") for n in NIVELES}
    return {
        "proporcion_alto": proporcion_alto,
        "deteccion_alto_medio": deteccion,
        "tasa_abandono_alto": tasa["alto"],
        "tasa_abandono_medio": tasa["medio"],
        "tasa_abandono_bajo": tasa["bajo"],
        "proporcion_medio": float(np.mean(niveles == "medio")),
        "proporcion_bajo": float(np.mean(niveles == "bajo")),
        "decreciente": bool(tasa["alto"] > tasa["medio"] > tasa["bajo"]),
    }
