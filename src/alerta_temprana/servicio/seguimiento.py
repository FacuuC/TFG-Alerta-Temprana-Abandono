"""Estado de seguimiento de las alertas (HU-007, tarea 7.1; decisión del 09/11).

`cambiar_estado` es la única entrada para cambiar el estado: la usan el listado, la ficha
y la API (`POST /api/alertas/{id}/estado`; decisión P4), así las tres respetan las mismas
reglas:

1. Solo Coordinación del Programa de Tutorías y Tutor/a pueden cambiar el estado; el
   servicio rechaza a los demás roles, igual que la carga con el Área de Sistemas
   (decisión P5). No es un control de acceso: sin inicio de sesión cualquiera puede elegir
   otro usuario de prueba (HU-009, Sprint 2).
2. Cada cambio actualiza ALERTA.estado y agrega una fila en CAMBIO_ESTADO (estado
   anterior, nuevo, usuario y fecha) en la misma transacción (criterio 2). La fecha se
   guarda en UTC; las pantallas la muestran en hora argentina.
3. Si el estado nuevo es igual al actual, no se registra nada. Se puede volver a
   «pendiente», y ese cambio también queda registrado.

La conservación del estado al recalcular (criterios 4 a 6) es la regla P3 de
servicio/alertas.py: el recálculo solo cambia la predicción de la alerta, nunca su estado,
y no escribe en CAMBIO_ESTADO.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from alerta_temprana.db.inicializacion import ROL_COORDINACION, ROL_TUTOR
from alerta_temprana.db.tablas import Alerta, CambioEstado, Usuario
from alerta_temprana.servicio.alertas import ESTADOS_SEGUIMIENTO
from alerta_temprana.servicio.usuarios import PermisoDenegado, comprobar_usuario

__all__ = [
    "ROLES_SEGUIMIENTO",
    "AlertaInexistente",
    "CambioRegistrado",
    "PermisoDenegado",
    "cambiar_estado",
    "historial_estados",
]

ROLES_SEGUIMIENTO = (ROL_COORDINACION, ROL_TUTOR)


class AlertaInexistente(Exception):
    """No hay ninguna alerta con ese identificador."""


@dataclass
class CambioRegistrado:
    """Resultado de `cambiar_estado`. Si el estado nuevo era igual al actual,
    `registrado` es False y `id_cambio` y `fecha` quedan en None."""

    id_alerta: int
    codigo_estudiante: str
    estado_anterior: str
    estado_nuevo: str
    usuario: str
    registrado: bool
    id_cambio: int | None = None
    fecha: datetime | None = None  # UTC

    def como_dict(self) -> dict:
        datos = asdict(self)
        datos["fecha"] = self.fecha.isoformat() if self.fecha else None
        return datos


def _mensaje_rol(nombre_usuario: str, rol: str) -> str:
    return (
        "El estado de seguimiento lo registran la Coordinación del Programa de Tutorías y los "
        f"tutores; «{nombre_usuario}» tiene el rol «{rol}»."
    )


def controlar_estado(estado: str) -> str:
    if estado not in ESTADOS_SEGUIMIENTO:
        raise ValueError(
            f"Estado de seguimiento no válido: {estado!r}. Valores posibles: {', '.join(ESTADOS_SEGUIMIENTO)}."
        )
    return estado


def cambiar_estado(
    sesion: Session, id_alerta: int, estado_nuevo: str, nombre_usuario: str
) -> CambioRegistrado:
    """Cambia el estado de seguimiento de una alerta y registra quién y cuándo.

    Lanza PermisoDenegado si el usuario no es de Coordinación ni Tutor/a, ValueError si el
    estado no es válido y AlertaInexistente si la alerta no existe. En esos casos no se
    guarda nada.
    """
    usuario = comprobar_usuario(sesion, nombre_usuario, ROLES_SEGUIMIENTO, _mensaje_rol)
    controlar_estado(estado_nuevo)
    try:
        # Bloquea la fila: dos cambios a la vez sobre la misma alerta quedan en orden y el
        # estado anterior de cada uno es el que realmente tenía
        alerta = sesion.scalars(
            select(Alerta)
            .where(Alerta.id_alerta == id_alerta)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).first()
        if alerta is None:
            raise AlertaInexistente(f"No se encontró la alerta {id_alerta}.")
        resultado = CambioRegistrado(
            id_alerta=alerta.id_alerta,
            codigo_estudiante=alerta.codigo_estudiante,
            estado_anterior=alerta.estado,
            estado_nuevo=estado_nuevo,
            usuario=nombre_usuario,
            registrado=alerta.estado != estado_nuevo,
        )
        if not resultado.registrado:
            sesion.rollback()  # nada que guardar; libera el bloqueo
            return resultado
        fecha = datetime.now(UTC)
        cambio = CambioEstado(
            id_alerta=alerta.id_alerta,
            id_usuario=usuario.id_usuario,
            estado_anterior=alerta.estado,
            estado_nuevo=estado_nuevo,
            fecha=fecha,
        )
        alerta.estado = estado_nuevo
        sesion.add(cambio)
        sesion.flush()
        resultado.id_cambio, resultado.fecha = cambio.id_cambio, fecha
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    return resultado


def historial_estados(sesion: Session, id_alerta: int) -> list[dict]:
    """Cambios de estado de una alerta, del más antiguo al más reciente (fecha en UTC)."""
    filas = sesion.execute(
        select(CambioEstado, Usuario.nombre_usuario)
        .join(Usuario, CambioEstado.id_usuario == Usuario.id_usuario)
        .where(CambioEstado.id_alerta == id_alerta)
        .order_by(CambioEstado.fecha, CambioEstado.id_cambio)
    ).all()
    return [
        {
            "id_cambio": cambio.id_cambio,
            "estado_anterior": cambio.estado_anterior,
            "estado_nuevo": cambio.estado_nuevo,
            "usuario": nombre_usuario,
            "fecha": cambio.fecha,
        }
        for cambio, nombre_usuario in filas
    ]
