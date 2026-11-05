"""Registro de una carga en la base (HU-001; tareas 1.3 y 1.4).

`registrar_carga` es la única entrada para cargar datos: la usan la pantalla de carga
(Dash) y la API (`POST /api/cargas`), así las dos respetan las mismas reglas:

1. El usuario de prueba tiene que tener el rol del Área de Sistemas (decisión P5). El
   selector de usuario del Sprint 1 no es un control de acceso: sin inicio de sesión
   cualquiera puede elegir otro usuario (HU-009, Sprint 2).
2. El archivo se procesa en memoria (datos/carga.py) y nunca se escribe en disco.
3. Todo se guarda en una transacción: la fila de CARGA con el momento y el usuario
   (criterio 5), los estudiantes nuevos y los rendimientos semestrales que falten.
   Un estudiante que ya existe no se duplica ni se modifica, y un rendimiento ya
   cargado no se sobrescribe (no hay edición de datos cargados).
4. Al terminar, se avisa a las funciones registradas con `registrar_al_terminar_carga`
   (punto de enganche para el recálculo de HU-003).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from alerta_temprana.config import obtener_configuracion
from alerta_temprana.datos import variables as V
from alerta_temprana.datos.carga import procesar_archivo
from alerta_temprana.datos.validacion import ErrorRegistro
from alerta_temprana.db.inicializacion import ROL_AREA_SISTEMAS
from alerta_temprana.db.tablas import Carga, Estudiante, RendimientoSemestre, Rol, Usuario

_BINARIAS = set(V.BINARIAS)
_DECIMALES = {"tasa_desempleo", "tasa_inflacion", "variacion_pib", "nota_titulo_previo", "nota_promedio"}


class PermisoDenegado(Exception):
    """El usuario de prueba elegido no puede hacer cargas."""


@dataclass
class ResultadoCarga:
    id_carga: int
    momento: str
    fecha: datetime
    usuario: str
    registros_validos: int
    registros_rechazados: int
    estudiantes_nuevos: int
    estudiantes_existentes: int
    rendimientos_agregados: int
    errores: list[ErrorRegistro] = field(default_factory=list)
    columnas_descartadas: dict[str, list[str]] = field(default_factory=dict)
    al_terminar: list[object] = field(default_factory=list)  # lo que devuelvan las funciones de HU-003

    def como_dict(self) -> dict:
        datos = asdict(self)
        datos["fecha"] = self.fecha.isoformat()
        return datos


# --- Punto de enganche para el recálculo (HU-003) ------------------------------------

AlTerminarCarga = Callable[[int, V.Momento], object]
_al_terminar_carga: list[AlTerminarCarga] = []


def registrar_al_terminar_carga(funcion: AlTerminarCarga) -> AlTerminarCarga:
    """Registra una función que se llama con (id_carga, momento) después de cada carga
    guardada. Se puede usar como decorador."""
    if funcion not in _al_terminar_carga:
        _al_terminar_carga.append(funcion)
    return funcion


def quitar_al_terminar_carga(funcion: AlTerminarCarga) -> None:
    if funcion in _al_terminar_carga:
        _al_terminar_carga.remove(funcion)


# --- Usuario --------------------------------------------------------------------------


def comprobar_usuario_de_carga(sesion: Session, nombre_usuario: str) -> Usuario:
    """El usuario tiene que existir, estar activo y ser del Área de Sistemas."""
    fila = sesion.execute(
        select(Usuario, Rol.nombre)
        .join(Rol, Usuario.id_rol == Rol.id_rol)
        .where(Usuario.nombre_usuario == nombre_usuario)
    ).first()
    if fila is None or not fila[0].activo:
        raise PermisoDenegado(f"El usuario «{nombre_usuario}» no existe o no está activo.")
    usuario, rol = fila
    if rol != ROL_AREA_SISTEMAS:
        raise PermisoDenegado(
            f"La carga de datos es del Área de Sistemas de Información; «{nombre_usuario}» tiene el rol «{rol}»."
        )
    return usuario


# --- Carga ----------------------------------------------------------------------------


def _valor(columna: str, valor: float) -> object:
    """Valor numérico del DataFrame -> tipo de la columna (BOOLEAN, SMALLINT o NUMERIC)."""
    if columna in _BINARIAS:
        return bool(int(valor))
    if columna in _DECIMALES:
        return float(valor)
    return int(valor)


def _filas(tabla, columnas: list[str]) -> list[dict]:
    return [
        {c: (_valor(c, fila[c]) if c in columnas else fila[c]) for c in tabla.columns}
        for _, fila in tabla.iterrows()
    ]


def registrar_carga(
    sesion: Session,
    contenido: bytes,
    momento: V.Momento | str,
    nombre_usuario: str,
    clave: str | None = None,
) -> ResultadoCarga:
    """Valida, seudonimiza y guarda una carga.

    Lanza PermisoDenegado si el usuario no es del Área de Sistemas y CargaRechazada si
    hay que rechazar la carga completa (en los dos casos no se guarda nada).
    """
    momento = V.Momento(momento)
    usuario = comprobar_usuario_de_carga(sesion, nombre_usuario)
    clave = clave if clave is not None else obtener_configuracion().seudonimo_clave
    procesado = procesar_archivo(contenido, momento, clave)
    del contenido  # el archivo original no se conserva

    codigos = list(procesado.estudiantes["codigo_estudiante"])
    existentes = set(
        sesion.scalars(select(Estudiante.codigo_estudiante).where(Estudiante.codigo_estudiante.in_(codigos)))
    )
    rendimientos_existentes = set(
        sesion.execute(
            select(RendimientoSemestre.codigo_estudiante, RendimientoSemestre.semestre).where(
                RendimientoSemestre.codigo_estudiante.in_(codigos)
            )
        ).all()
    )

    try:
        carga = Carga(
            id_usuario=usuario.id_usuario,
            fecha=datetime.now(UTC),
            momento=momento.value,
            registros_validos=procesado.registros_validos,
            registros_rechazados=procesado.registros_rechazados,
        )
        sesion.add(carga)
        sesion.flush()

        nuevos = procesado.estudiantes[~procesado.estudiantes["codigo_estudiante"].isin(existentes)]
        filas_estudiantes = _filas(nuevos, list(V.VARIABLES_INSCRIPCION))
        for fila in filas_estudiantes:
            fila["id_carga"] = carga.id_carga
        if filas_estudiantes:
            sesion.execute(insert(Estudiante), filas_estudiantes)

        rendimientos = procesado.rendimientos
        faltan = [
            (codigo, int(semestre)) not in rendimientos_existentes
            for codigo, semestre in zip(
                rendimientos["codigo_estudiante"], rendimientos["semestre"], strict=True
            )
        ]
        filas_rendimiento = _filas(rendimientos[faltan], list(V.CAMPOS_RENDIMIENTO))
        for fila in filas_rendimiento:
            fila["id_carga"] = carga.id_carga
            fila["semestre"] = int(fila["semestre"])
        if filas_rendimiento:
            sesion.execute(insert(RendimientoSemestre), filas_rendimiento)
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise

    resultado = ResultadoCarga(
        id_carga=carga.id_carga,
        momento=momento.value,
        fecha=carga.fecha,
        usuario=nombre_usuario,
        registros_validos=procesado.registros_validos,
        registros_rechazados=procesado.registros_rechazados,
        estudiantes_nuevos=len(filas_estudiantes),
        estudiantes_existentes=procesado.registros_validos - len(filas_estudiantes),
        rendimientos_agregados=len(filas_rendimiento),
        errores=procesado.errores,
        columnas_descartadas=procesado.columnas_descartadas,
    )
    resultado.al_terminar = [funcion(carga.id_carga, momento) for funcion in list(_al_terminar_carga)]
    return resultado


def listar_cargas(sesion: Session, limite: int = 20) -> list[dict]:
    """Cargas anteriores, de la más reciente a la más antigua."""
    filas = sesion.execute(
        select(Carga, Usuario.nombre_usuario)
        .join(Usuario, Carga.id_usuario == Usuario.id_usuario)
        .order_by(Carga.fecha.desc(), Carga.id_carga.desc())
        .limit(limite)
    ).all()
    return [
        {
            "id_carga": carga.id_carga,
            "fecha": carga.fecha,
            "momento": carga.momento,
            "usuario": nombre_usuario,
            "registros_validos": carga.registros_validos,
            "registros_rechazados": carga.registros_rechazados,
        }
        for carga, nombre_usuario in filas
    ]
