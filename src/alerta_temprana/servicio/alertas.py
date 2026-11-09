"""Alertas tempranas al recalcular (HU-004, tarea 4.2; decisión P3 del 05/11).

Una alerta por estudiante:
- nivel alto o medio y sin alerta → se crea en «pendiente» con la predicción nueva;
- ya tiene alerta (cualquier nivel) → pasa a apuntar a la predicción vigente y
  **conserva su estado** (HU-007, criterio 4). Si baja a nivel bajo, la alerta sigue con
  su estado y su nivel actual y sale del filtro por defecto del listado («Alto y medio»);
- nivel bajo y sin alerta → no se crea nada.

Crear una alerta no es un cambio de estado: CAMBIO_ESTADO se registra en HU-007.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session

from alerta_temprana.db.tablas import Alerta

ESTADO_INICIAL = "pendiente"
NIVELES_CON_ALERTA = ("alto", "medio")

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
