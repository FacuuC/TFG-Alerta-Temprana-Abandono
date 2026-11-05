"""Tablas de la base de datos según el DER del prototipo (Figura 4; tarea 1.2).

Nombres de tablas y campos como en el diccionario de datos (Tabla 32) y en
docs/proyecto/03-modelo-de-datos.md. Los tipos de las entidades que no están en la
Tabla 32 son la propuesta de ese archivo.

La entidad ESTUDIANTE guarda solo el código seudonimizado y las variables de la
inscripción: no hay columnas para legajo, documento, nombre ni para las variables
excluidas (HU-001, criterio 4).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from alerta_temprana.datos.variables import Momento

_MOMENTOS = ", ".join(f"'{m.value}'" for m in Momento)
_ESTADOS = "'pendiente', 'contactado', 'en_acompanamiento'"


class Base(DeclarativeBase):
    pass


class Rol(Base):
    __tablename__ = "rol"

    id_rol: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), unique=True)


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_rol: Mapped[int] = mapped_column(SmallInteger, ForeignKey("rol.id_rol"))
    nombre_usuario: Mapped[str] = mapped_column(String(40), unique=True)
    hash_contrasena: Mapped[str | None] = mapped_column(String(255), nullable=True)  # HU-009 (Sprint 2)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Carga(Base):
    __tablename__ = "carga"
    __table_args__ = (CheckConstraint(f"momento IN ({_MOMENTOS})", name="ck_carga_momento"),)

    id_carga: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(Integer, ForeignKey("usuario.id_usuario"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    momento: Mapped[str] = mapped_column(String(12))
    registros_validos: Mapped[int] = mapped_column(Integer)
    registros_rechazados: Mapped[int] = mapped_column(Integer)


class Estudiante(Base):
    """Tabla 32. `situacion_final` solo existe en datos históricos: en las cargas queda nula."""

    __tablename__ = "estudiante"
    __table_args__ = (
        CheckConstraint(
            "situacion_final IS NULL OR situacion_final IN ('abandono', 'cursando', 'graduado')",
            name="ck_estudiante_situacion_final",
        ),
    )

    codigo_estudiante: Mapped[str] = mapped_column(String(12), primary_key=True)
    id_carga: Mapped[int] = mapped_column(Integer, ForeignKey("carga.id_carga"))
    estado_civil: Mapped[int] = mapped_column(SmallInteger)
    nacionalidad: Mapped[int] = mapped_column(SmallInteger)
    desplazado: Mapped[bool] = mapped_column(Boolean)
    genero: Mapped[bool] = mapped_column(Boolean)  # 1 masculino, 0 femenino
    edad_ingreso: Mapped[int] = mapped_column(SmallInteger)
    internacional: Mapped[bool] = mapped_column(Boolean)
    nivel_educ_madre: Mapped[int] = mapped_column(SmallInteger)
    nivel_educ_padre: Mapped[int] = mapped_column(SmallInteger)
    ocupacion_madre: Mapped[int] = mapped_column(SmallInteger)
    ocupacion_padre: Mapped[int] = mapped_column(SmallInteger)
    becario: Mapped[bool] = mapped_column(Boolean)
    tasa_desempleo: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    tasa_inflacion: Mapped[Decimal] = mapped_column(Numeric(3, 1))
    variacion_pib: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    modalidad_ingreso: Mapped[int] = mapped_column(SmallInteger)
    carrera: Mapped[int] = mapped_column(SmallInteger)
    turno_diurno: Mapped[bool] = mapped_column(Boolean)  # 1 diurno, 0 nocturno
    titulo_previo: Mapped[int] = mapped_column(SmallInteger)
    nota_titulo_previo: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    situacion_final: Mapped[str | None] = mapped_column(String(10), nullable=True)


class RendimientoSemestre(Base):
    __tablename__ = "rendimiento_semestre"
    __table_args__ = (
        UniqueConstraint("codigo_estudiante", "semestre", name="uq_rendimiento_estudiante_semestre"),
        CheckConstraint("semestre IN (1, 2)", name="ck_rendimiento_semestre"),
    )

    id_rendimiento: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_estudiante: Mapped[str] = mapped_column(String(12), ForeignKey("estudiante.codigo_estudiante"))
    id_carga: Mapped[int] = mapped_column(Integer, ForeignKey("carga.id_carga"))
    semestre: Mapped[int] = mapped_column(SmallInteger)
    materias_acreditadas: Mapped[int] = mapped_column(SmallInteger)
    materias_inscriptas: Mapped[int] = mapped_column(SmallInteger)
    evaluaciones: Mapped[int] = mapped_column(SmallInteger)
    materias_aprobadas: Mapped[int] = mapped_column(SmallInteger)
    nota_promedio: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    materias_sin_evaluacion: Mapped[int] = mapped_column(SmallInteger)


class Modelo(Base):
    __tablename__ = "modelo"
    __table_args__ = (
        CheckConstraint(f"momento IN ({_MOMENTOS})", name="ck_modelo_momento"),
        # Un solo modelo habilitado por momento
        Index(
            "uq_modelo_habilitado_por_momento",
            "momento",
            unique=True,
            postgresql_where=text("habilitado"),
        ),
    )

    id_modelo: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(10))
    momento: Mapped[str] = mapped_column(String(12))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    auc_roc: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    precision: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    sensibilidad: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    umbral_alto: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    umbral_medio: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    habilitado: Mapped[bool] = mapped_column(Boolean, default=False)


class MetricaSubgrupo(Base):
    __tablename__ = "metrica_subgrupo"

    id_metrica: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_modelo: Mapped[int] = mapped_column(Integer, ForeignKey("modelo.id_modelo"))
    subgrupo: Mapped[str] = mapped_column(String(20))
    valor: Mapped[str] = mapped_column(String(20))
    auc_roc: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    sensibilidad: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    precision: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)


class Prediccion(Base):
    __tablename__ = "prediccion"
    __table_args__ = (CheckConstraint("nivel IN ('alto', 'medio', 'bajo')", name="ck_prediccion_nivel"),)

    id_prediccion: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_estudiante: Mapped[str] = mapped_column(String(12), ForeignKey("estudiante.codigo_estudiante"))
    id_modelo: Mapped[int] = mapped_column(Integer, ForeignKey("modelo.id_modelo"))
    id_carga: Mapped[int] = mapped_column(Integer, ForeignKey("carga.id_carga"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    probabilidad: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    nivel: Mapped[str] = mapped_column(String(5))
    vigente: Mapped[bool] = mapped_column(Boolean)


class FactorExplicativo(Base):
    __tablename__ = "factor_explicativo"
    __table_args__ = (CheckConstraint("orden BETWEEN 1 AND 5", name="ck_factor_orden"),)

    id_factor: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_prediccion: Mapped[int] = mapped_column(Integer, ForeignKey("prediccion.id_prediccion"))
    orden: Mapped[int] = mapped_column(SmallInteger)
    variable: Mapped[str] = mapped_column(String(40))
    valor: Mapped[str] = mapped_column(String(40))
    contribucion: Mapped[Decimal] = mapped_column(Numeric(8, 4))  # valor SHAP (positivo = aumenta el riesgo)


class Alerta(Base):
    __tablename__ = "alerta"
    __table_args__ = (CheckConstraint(f"estado IN ({_ESTADOS})", name="ck_alerta_estado"),)

    id_alerta: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_estudiante: Mapped[str] = mapped_column(String(12), ForeignKey("estudiante.codigo_estudiante"))
    id_prediccion: Mapped[int] = mapped_column(Integer, ForeignKey("prediccion.id_prediccion"))
    estado: Mapped[str] = mapped_column(String(20))
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CambioEstado(Base):
    __tablename__ = "cambio_estado"
    __table_args__ = (
        CheckConstraint(f"estado_anterior IN ({_ESTADOS})", name="ck_cambio_estado_anterior"),
        CheckConstraint(f"estado_nuevo IN ({_ESTADOS})", name="ck_cambio_estado_nuevo"),
    )

    id_cambio: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_alerta: Mapped[int] = mapped_column(Integer, ForeignKey("alerta.id_alerta"))
    id_usuario: Mapped[int] = mapped_column(Integer, ForeignKey("usuario.id_usuario"))
    estado_anterior: Mapped[str] = mapped_column(String(20))
    estado_nuevo: Mapped[str] = mapped_column(String(20))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
