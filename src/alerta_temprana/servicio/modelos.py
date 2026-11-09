"""Modelos de la plataforma: registro en MODELO y lectura del habilitado (HU-003, tarea 3.1).

- `registrar_modelos` lleva a la tabla MODELO lo que dejó el entrenamiento en
  `modelos/<momento>/v<version>/metadatos.json` (03-modelo-de-datos.md, «Datos
  iniciales»). Agrega las versiones que falten y no modifica las que ya están: si un
  modelo se deshabilita en la base, sigue deshabilitado. No recalcula métricas ni lee
  etiquetas: las métricas de prueba ya están en los metadatos (evaluación final de HU-002).
- `cargar_habilitado` devuelve el modelo habilitado de un momento con su pipeline. Los
  umbrales para clasificar son los **exactos** de `metadatos.json`; los de MODELO están
  redondeados por el tipo NUMERIC(5,4) (decisión del 04/11, «Umbrales sin redondeo»).
  Antes de usarlo se controla la huella SHA-256 del pipeline y que sus variables sean
  exactamente las del momento (regla de «sin información futura»).

Los modelos se leen, nunca se reentrenan ni se escriben (modelo congelado de cierre_1s).
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from sklearn.pipeline import Pipeline
from sqlalchemy import select
from sqlalchemy.orm import Session

from alerta_temprana.datos import variables as V
from alerta_temprana.db.tablas import Modelo
from alerta_temprana.modelo.persistencia import cargar_modelo, carpeta_modelo

registro = logging.getLogger(__name__)


class ModeloNoDisponible(Exception):
    """El modelo habilitado no se puede usar (falta el archivo, no coincide la huella, etc.)."""


@dataclass(frozen=True)
class ModeloCargado:
    id_modelo: int
    version: str
    momento: V.Momento
    pipeline: Pipeline
    metadatos: dict
    umbral_alto: float  # exacto, de metadatos.json
    umbral_medio: float  # exacto, de metadatos.json


def _numerico(valor: float | None) -> Decimal | None:
    return None if valor is None else Decimal(str(round(float(valor), 4)))


def _leer_metadatos(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def registrar_modelos(sesion: Session, raiz_modelos: Path) -> list[str]:
    """Agrega a MODELO las versiones de `modelos/` que falten. Devuelve las agregadas
    («cierre_1s v1.0»). Se puede ejecutar varias veces: no duplica ni modifica filas."""
    momentos = {m.value for m in V.Momento}
    existentes = set(sesion.execute(select(Modelo.momento, Modelo.version)).all())
    habilitados = set(sesion.scalars(select(Modelo.momento).where(Modelo.habilitado)))
    agregados: list[str] = []
    for ruta in sorted(Path(raiz_modelos).glob("*/v*/metadatos.json")):
        meta = _leer_metadatos(ruta)
        momento, version = meta.get("momento"), str(meta.get("version"))
        if momento not in momentos or (momento, version) in existentes:
            continue
        habilitado = bool(meta.get("habilitado", False))
        if habilitado and momento in habilitados:
            # Un solo modelo habilitado por momento: el cambio de modelo es de HU-014
            registro.warning(
                "%s v%s está habilitado en sus metadatos, pero ya hay otro modelo habilitado para "
                "ese momento: se registra deshabilitado.",
                momento,
                version,
            )
            habilitado = False
        prueba = meta.get("prueba", {})
        sesion.add(
            Modelo(
                version=version,
                momento=momento,
                fecha=datetime.fromisoformat(meta["fecha"]),
                auc_roc=_numerico(prueba.get("auc_roc")),
                precision=_numerico(prueba.get("precision_alerta")),
                sensibilidad=_numerico(prueba.get("sensibilidad_alerta")),
                umbral_alto=_numerico(meta["umbral_alto"]),
                umbral_medio=_numerico(meta["umbral_medio"]),
                habilitado=habilitado,
            )
        )
        existentes.add((momento, version))
        if habilitado:
            habilitados.add(momento)
        agregados.append(f"{momento} v{version}")
    sesion.commit()
    return agregados


def buscar_habilitado(sesion: Session, momento: V.Momento | str) -> Modelo | None:
    """Fila de MODELO habilitada para el momento, o None si no hay."""
    return sesion.scalars(
        select(Modelo).where(Modelo.momento == V.Momento(momento).value, Modelo.habilitado)
    ).first()


def sha256_archivo(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


_cache: dict[tuple[str, str], tuple[Pipeline, dict]] = {}
_candado_cache = threading.Lock()


def _leer_pipeline(raiz_modelos: Path, momento: V.Momento, version: str) -> tuple[Pipeline, dict]:
    """Pipeline y metadatos, comprobados. Se guardan en memoria por ruta y huella."""
    carpeta = carpeta_modelo(Path(raiz_modelos), momento, version)
    ruta_pipeline, ruta_meta = carpeta / "pipeline.joblib", carpeta / "metadatos.json"
    if not ruta_pipeline.exists() or not ruta_meta.exists():
        raise ModeloNoDisponible(f"El modelo habilitado v{version} ({momento.value}) no está en {carpeta}.")
    huella = sha256_archivo(ruta_pipeline)
    clave = (str(ruta_pipeline.resolve()), huella)
    with _candado_cache:
        if clave in _cache:
            return _cache[clave]
        meta = _leer_metadatos(ruta_meta)
        esperada = meta.get("sha256_pipeline")
        if esperada and esperada != huella:
            raise ModeloNoDisponible(
                f"El archivo del modelo v{version} ({momento.value}) no coincide con la huella "
                "SHA-256 de sus metadatos: no se usa."
            )
        if meta.get("momento") != momento.value or str(meta.get("version")) != version:
            raise ModeloNoDisponible(
                f"Los metadatos de {carpeta} no corresponden a v{version} ({momento.value})."
            )
        if meta.get("variables") != V.VARIABLES_POR_MOMENTO[momento]:
            raise ModeloNoDisponible(
                f"Las variables del modelo v{version} no son las del momento {momento.value}."
            )
        pipeline, meta = cargar_modelo(Path(raiz_modelos), momento, version)
        _cache[clave] = (pipeline, meta)
        return pipeline, meta


def cargar_habilitado(sesion: Session, momento: V.Momento | str, raiz_modelos: Path) -> ModeloCargado | None:
    """Modelo habilitado del momento, listo para predecir, o None si no hay ninguno.

    Lanza ModeloNoDisponible si hay uno habilitado pero no se puede usar.
    """
    momento = V.Momento(momento)
    fila = buscar_habilitado(sesion, momento)
    if fila is None:
        return None
    pipeline, meta = _leer_pipeline(raiz_modelos, momento, fila.version)
    return ModeloCargado(
        id_modelo=fila.id_modelo,
        version=fila.version,
        momento=momento,
        pipeline=pipeline,
        metadatos=meta,
        umbral_alto=float(meta["umbral_alto"]),
        umbral_medio=float(meta["umbral_medio"]),
    )
