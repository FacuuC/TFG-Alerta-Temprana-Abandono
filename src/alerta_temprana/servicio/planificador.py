"""Planificador: recálculo del riesgo al terminar cada carga (HU-003, tarea 3.2).

Figura 9: al terminar una carga válida, el planificador dispara el recálculo y el servicio
de predicción guarda predicciones y factores. Se engancha a `registrar_carga`
(servicio/carga.py), así funciona igual desde la pantalla y desde la API, sin que nadie
lo pida a mano (criterio 1).

- **En el momento de la carga** se comprueba si hay un modelo habilitado para el momento.
  Si no hay, no se calcula nada y el resultado de la carga dice el motivo, que ve el Área
  de Sistemas en la pantalla o en la respuesta de la API (criterio 5). También queda en el
  registro de la aplicación.
- Si hay, el cálculo corre **en segundo plano** en un único hilo: la pantalla no se
  bloquea y dos cargas seguidas se calculan en orden, sin pisarse.
- `estado(id_carga)` informa «en curso», «completado» (con modelo y cantidades), «sin
  modelo» o «error». El estado vive en memoria; después de reiniciar la aplicación se
  reconstruye desde la base lo que haya quedado guardado (`resumen_de_carga`).
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from alerta_temprana.datos import variables as V
from alerta_temprana.servicio import prediccion
from alerta_temprana.servicio.modelos import ModeloNoDisponible, buscar_habilitado, cargar_habilitado

registro = logging.getLogger(__name__)

EN_CURSO = "en_curso"
COMPLETADO = "completado"
SIN_MODELO = "sin_modelo"
ERROR = "error"
TERMINALES = (COMPLETADO, SIN_MODELO, ERROR)


@dataclass
class EstadoRecalculo:
    id_carga: int
    momento: str
    estado: str
    mensaje: str
    resumen: dict | None = field(default=None)

    def como_dict(self) -> dict:
        return asdict(self)


def _etiqueta(momento: V.Momento | str) -> str:
    return V.ETIQUETA_MOMENTO[V.Momento(momento)]


def mensaje_completado(version: str, momento: str, estudiantes: int) -> str:
    return f"Completado: modelo v{version} ({_etiqueta(momento)}) · {estudiantes} estudiantes"


def mensaje_sin_modelo(momento: V.Momento | str) -> str:
    return (
        f"No se calcularon riesgos: no hay un modelo habilitado para el momento «{_etiqueta(momento)}». "
        "La carga quedó registrada; las estimaciones anteriores siguen vigentes."
    )


def mensaje_error(motivo: str) -> str:
    return (
        f"No se pudo calcular el riesgo: {motivo} "
        "La carga quedó registrada; las estimaciones anteriores siguen vigentes."
    )


class Planificador:
    def __init__(self, fabrica_sesiones: sessionmaker[Session], raiz_modelos: Path) -> None:
        self._fabrica = fabrica_sesiones
        self._raiz_modelos = Path(raiz_modelos)
        self._ejecutor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="recalculo")
        self._estados: dict[int, EstadoRecalculo] = {}
        self._futuros: dict[int, Future] = {}
        self._candado = threading.Lock()

    # --- Enganche de registrar_carga --------------------------------------------------

    def al_terminar_carga(self, id_carga: int, momento: V.Momento, codigos: list[str]) -> dict:
        momento = V.Momento(momento)
        try:
            with self._fabrica() as sesion:
                habilitado = buscar_habilitado(sesion, momento) is not None
        except Exception as error:  # la carga ya está guardada: se informa, no se propaga
            registro.exception("No se pudo consultar el modelo habilitado (carga %s)", id_carga)
            return self._guardar(
                EstadoRecalculo(
                    id_carga,
                    momento.value,
                    ERROR,
                    mensaje_error(f"la base de datos no respondió ({type(error).__name__})."),
                )
            ).como_dict()
        if not habilitado:
            registro.warning(
                "Carga %s: sin modelo habilitado para %s; no se calcularon riesgos", id_carga, momento.value
            )
            return self._guardar(
                EstadoRecalculo(id_carga, momento.value, SIN_MODELO, mensaje_sin_modelo(momento))
            ).como_dict()
        estado = self._guardar(
            EstadoRecalculo(id_carga, momento.value, EN_CURSO, "Cálculo del riesgo en curso…")
        )
        futuro = self._ejecutor.submit(self._recalcular, id_carga, momento, list(codigos))
        with self._candado:
            self._futuros[id_carga] = futuro
        return estado.como_dict()

    # --- Trabajo en segundo plano -----------------------------------------------------

    def _recalcular(self, id_carga: int, momento: V.Momento, codigos: list[str]) -> EstadoRecalculo:
        try:
            with self._fabrica() as sesion:
                modelo = cargar_habilitado(sesion, momento, self._raiz_modelos)
                if modelo is None:  # se deshabilitó entre la carga y el cálculo
                    return self._guardar(
                        EstadoRecalculo(id_carga, momento.value, SIN_MODELO, mensaje_sin_modelo(momento))
                    )
                resumen = prediccion.recalcular(sesion, modelo, id_carga, codigos)
        except (ModeloNoDisponible, prediccion.DatosIncompletos) as error:
            registro.error("Carga %s: %s", id_carga, error)
            return self._guardar(EstadoRecalculo(id_carga, momento.value, ERROR, mensaje_error(str(error))))
        except Exception as error:
            registro.exception("Carga %s: falló el recálculo del riesgo", id_carga)
            return self._guardar(
                EstadoRecalculo(
                    id_carga, momento.value, ERROR, mensaje_error(f"error interno ({type(error).__name__}).")
                )
            )
        registro.info(
            "Carga %s: riesgo calculado con %s v%s para %s estudiantes",
            id_carga,
            momento.value,
            resumen.version,
            resumen.estudiantes,
        )
        return self._guardar(
            EstadoRecalculo(
                id_carga,
                momento.value,
                COMPLETADO,
                mensaje_completado(resumen.version, momento.value, resumen.estudiantes),
                resumen.como_dict(),
            )
        )

    # --- Consulta ---------------------------------------------------------------------

    def _guardar(self, estado: EstadoRecalculo) -> EstadoRecalculo:
        with self._candado:
            self._estados[estado.id_carga] = estado
        return estado

    def estado(self, id_carga: int) -> EstadoRecalculo | None:
        """Estado del recálculo de una carga. Si no está en memoria (por ejemplo, después de
        reiniciar la aplicación), se arma con lo que quedó guardado en la base."""
        with self._candado:
            if id_carga in self._estados:
                return self._estados[id_carga]
        with self._fabrica() as sesion:
            resumen = prediccion.resumen_de_carga(sesion, id_carga)
        if resumen is None:
            return None
        return EstadoRecalculo(
            id_carga,
            resumen["momento"],
            COMPLETADO,
            mensaje_completado(resumen["version"], resumen["momento"], resumen["estudiantes"]),
            resumen | {"fecha": resumen["fecha"].isoformat()},
        )

    def esperar(self, id_carga: int, tiempo: float | None = None) -> EstadoRecalculo | None:
        """Espera a que termine el recálculo de una carga (para las pruebas y los scripts)."""
        with self._candado:
            futuro = self._futuros.get(id_carga)
        if futuro is not None:
            futuro.result(timeout=tiempo)
        return self.estado(id_carga)

    def cerrar(self) -> None:
        self._ejecutor.shutdown(wait=True)


@lru_cache
def obtener_planificador() -> Planificador:
    """Planificador de la aplicación (uno por proceso)."""
    from alerta_temprana.config import obtener_configuracion
    from alerta_temprana.db.sesion import obtener_fabrica_sesiones

    return Planificador(obtener_fabrica_sesiones(), obtener_configuracion().ruta_modelos)
