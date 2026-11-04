"""Guardado y lectura de modelos versionados (tarea 2.5; decisión P6).

Estructura: modelos/<momento>/v<version>/
    pipeline.joblib   preprocesador + modelo (scikit-learn / XGBoost)
    metadatos.json    versión, fecha, algoritmo, hiperparámetros, semilla, métricas de
                      validación, umbrales y, después de la evaluación final, métricas de
                      prueba y habilitación.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

from alerta_temprana.datos import variables as V


def carpeta_modelo(raiz_modelos: Path, momento: V.Momento, version: str) -> Path:
    return raiz_modelos / momento.value / f"v{version}"


def guardar_modelo(
    raiz_modelos: Path,
    momento: V.Momento,
    version: str,
    pipeline: Pipeline,
    metadatos: dict,
    sobrescribir: bool = False,
) -> Path:
    carpeta = carpeta_modelo(raiz_modelos, momento, version)
    if (carpeta / "pipeline.joblib").exists() and not sobrescribir:
        raise FileExistsError(
            f"Ya existe {carpeta}. Una versión guardada no se modifica: usá otra versión "
            "o pasá sobrescribir=True a sabiendas."
        )
    carpeta.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, carpeta / "pipeline.joblib")
    datos = {
        "version": version,
        "momento": momento.value,
        "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
        "variables": V.VARIABLES_POR_MOMENTO[momento],
        "habilitado": False,
        **metadatos,
    }
    (carpeta / "metadatos.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return carpeta


def cargar_modelo(raiz_modelos: Path, momento: V.Momento, version: str) -> tuple[Pipeline, dict]:
    carpeta = carpeta_modelo(raiz_modelos, momento, version)
    pipeline = joblib.load(carpeta / "pipeline.joblib")
    metadatos = json.loads((carpeta / "metadatos.json").read_text(encoding="utf-8"))
    return pipeline, metadatos


def actualizar_metadatos(raiz_modelos: Path, momento: V.Momento, version: str, **cambios) -> dict:
    ruta = carpeta_modelo(raiz_modelos, momento, version) / "metadatos.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos.update(cambios)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return datos
