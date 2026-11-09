"""Alertas tempranas: creación al recalcular y consulta para el listado.

Al recalcular (HU-004, tarea 4.2; decisión P3 del 05/11, modificada el 07/11), una
alerta por estudiante:
- nivel alto o medio y sin alerta → se crea en «pendiente» con la predicción nueva;
- ya tiene alerta (cualquier nivel) → pasa a apuntar a la predicción vigente y
  **conserva su estado** (HU-007, criterio 4). Si baja a nivel bajo, la alerta sigue con
  su estado y su nivel actual, y el listado la sigue mostrando (no hay filtro por defecto);
- nivel bajo y sin alerta → no se crea nada.

Crear una alerta no es un cambio de estado: CAMBIO_ESTADO se registra en HU-007.

La consulta del listado (HU-005, tarea 5.1) filtra y ordena en SQL: nivel alto, medio y
bajo y, dentro de cada nivel, probabilidad de mayor a menor. Cada fila tiene solo el
código seudonimizado y datos no identificatorios.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from sqlalchemy import case, insert, select, update
from sqlalchemy.orm import Session

from alerta_temprana.db.tablas import Alerta, Estudiante, Prediccion
from alerta_temprana.modelo.etiquetas import CARRERA
from alerta_temprana.modelo.umbrales import NIVELES

ESTADOS_SEGUIMIENTO = ("pendiente", "contactado", "en_acompanamiento")
ESTADO_INICIAL = "pendiente"
NIVELES_CON_ALERTA = ("alto", "medio")
TURNOS = ("diurno", "nocturno")

Accion = Literal["crear", "actualizar", "ninguna"]


def decidir_alerta(nivel: str, tiene_alerta: bool) -> Accion:
    if tiene_alerta:
        return "actualizar"
    if nivel in NIVELES_CON_ALERTA:
        return "crear"
    return "ninguna"


def actualizar_alertas(
    sesion: Session, predicciones: dict[str, tuple[int, str]], fecha: datetime
) -> tuple[int, int]:
    """Aplica la regla a {codigo_estudiante: (id_prediccion vigente, nivel)}.

    No hace commit: corre dentro de la transacción del recálculo. Devuelve (creadas,
    actualizadas).
    """
    if not predicciones:
        return 0, 0
    existentes = dict(
        sesion.execute(
            select(Alerta.codigo_estudiante, Alerta.id_alerta).where(
                Alerta.codigo_estudiante.in_(list(predicciones))
            )
        ).all()
    )
    nuevas, cambios = [], []
    for codigo, (id_prediccion, nivel) in predicciones.items():
        accion = decidir_alerta(nivel, codigo in existentes)
        if accion == "crear":
            nuevas.append(
                {
                    "codigo_estudiante": codigo,
                    "id_prediccion": id_prediccion,
                    "estado": ESTADO_INICIAL,
                    "fecha_creacion": fecha,
                }
            )
        elif accion == "actualizar":
            cambios.append({"id_alerta": existentes[codigo], "id_prediccion": id_prediccion})
    if nuevas:
        sesion.execute(insert(Alerta), nuevas)
    if cambios:
        sesion.execute(update(Alerta), cambios)  # por clave primaria; el estado no se toca
    return len(nuevas), len(cambios)


# --- Consulta del listado (HU-005, tarea 5.1) -------------------------------------------


@dataclass
class FiltrosAlertas:
    """Filtros del listado. Una lista vacía o un turno `None` no filtra (por defecto,
    todas las alertas, incluidas las de nivel bajo)."""

    carreras: list[int] = field(default_factory=list)
    turno: str | None = None
    niveles: list[str] = field(default_factory=list)
    estados: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _controlar("carrera", self.carreras, CARRERA)
        _controlar("turno", [self.turno] if self.turno else [], TURNOS)
        _controlar("nivel", self.niveles, NIVELES)
        _controlar("estado de seguimiento", self.estados, ESTADOS_SEGUIMIENTO)


def _controlar(nombre: str, valores: list, validos) -> None:
    desconocidos = [v for v in valores if v not in validos]
    if desconocidos:
        raise ValueError(f"Valor de {nombre} no válido: {', '.join(map(str, desconocidos))}")


# Columnas del listado (criterio 2): ninguna identifica al estudiante
COLUMNAS_LISTADO = ("id_alerta", "codigo_estudiante", "carrera", "turno", "nivel", "probabilidad", "estado")

_ORDEN_NIVEL = case({n: i for i, n in enumerate(NIVELES)}, value=Prediccion.nivel)


def consultar_alertas(sesion: Session, filtros: FiltrosAlertas | None = None) -> list[dict]:
    """Alertas con su predicción vigente, filtradas y en orden de urgencia (criterios 1 a 3).

    Orden: nivel alto, medio y bajo; dentro de cada nivel, probabilidad de mayor a menor
    (y el código, para que el orden sea estable). La carrera va con su nombre.
    """
    filtros = filtros or FiltrosAlertas()
    consulta = (
        select(
            Alerta.id_alerta,
            Alerta.codigo_estudiante,
            Estudiante.carrera,
            Estudiante.turno_diurno,
            Prediccion.nivel,
            Prediccion.probabilidad,
            Alerta.estado,
        )
        .join(Prediccion, Alerta.id_prediccion == Prediccion.id_prediccion)
        .join(Estudiante, Alerta.codigo_estudiante == Estudiante.codigo_estudiante)
        .order_by(_ORDEN_NIVEL, Prediccion.probabilidad.desc(), Alerta.codigo_estudiante)
    )
    if filtros.carreras:
        consulta = consulta.where(Estudiante.carrera.in_(filtros.carreras))
    if filtros.turno:
        consulta = consulta.where(Estudiante.turno_diurno.is_(filtros.turno == "diurno"))
    if filtros.niveles:
        consulta = consulta.where(Prediccion.nivel.in_(filtros.niveles))
    if filtros.estados:
        consulta = consulta.where(Alerta.estado.in_(filtros.estados))
    return [
        {
            "id_alerta": fila.id_alerta,
            "codigo_estudiante": fila.codigo_estudiante,
            "carrera": CARRERA.get(fila.carrera, str(fila.carrera)),
            "turno": "diurno" if fila.turno_diurno else "nocturno",
            "nivel": fila.nivel,
            "probabilidad": float(fila.probabilidad),
            "estado": fila.estado,
        }
        for fila in sesion.execute(consulta)
    ]


def resumir_alertas(alertas: list[dict]) -> dict[str, int]:
    """Contadores de las tarjetas sobre **las mismas** alertas que muestra el listado,
    así respetan el filtro activo."""
    niveles = Counter(a["nivel"] for a in alertas)
    return {
        "alto": niveles["alto"],
        "medio": niveles["medio"],
        "pendientes": sum(a["estado"] == ESTADO_INICIAL for a in alertas),
        "total": len(alertas),
    }
