"""Fuente única de verdad sobre las variables del conjunto de datos.

Define, para el archivo de Realinho et al. (2021) publicado en UCI:
- la correspondencia entre cada columna original (en inglés) y su nombre en la
  plataforma (Tabla 32 del documento, diccionario de datos);
- las variables excluidas y su motivo;
- las variables disponibles en cada momento de predicción (19, 25 y 31).

Cualquier módulo que necesite listas de variables las toma de acá. Si una
decisión cambia (por ejemplo, una exclusión), se cambia solo en este archivo
y en docs/proyecto/04-datos.md.
"""

from __future__ import annotations

import re
from enum import Enum


class Momento(str, Enum):  # noqa: UP042  (StrEnum no existe en Python 3.10)
    """Momentos de predicción del primer año (grupo A, confirmado el 17/10)."""

    INSCRIPCION = "inscripcion"  # M0: antes del inicio de clases
    CIERRE_1S = "cierre_1s"  # M1: cierre del primer semestre (meta AUC-ROC > 0,80)
    CIERRE_2S = "cierre_2s"  # M2: cierre del segundo semestre


ETIQUETA_MOMENTO: dict[Momento, str] = {
    Momento.INSCRIPCION: "Inscripción",
    Momento.CIERRE_1S: "Cierre del 1.er semestre",
    Momento.CIERRE_2S: "Cierre del 2.º semestre",
}


def normalizar_nombre(columna: str) -> str:
    """Normaliza un encabezado del CSV original para compararlo sin errores.

    El archivo de UCI tiene detalles que rompen una comparación exacta: un
    tabulador al final de «Daytime/evening attendance», mayúsculas distintas
    según la versión («Marital status» / «Marital Status») y la errata
    «Nacionality». Se pasa a minúsculas, se quitan espacios y tabuladores en
    los extremos y se colapsan los espacios internos.
    """
    return re.sub(r"\s+", " ", columna.strip()).lower()


# --- Variables que usa el modelo (Tabla 32, entidad ESTUDIANTE) --------------
# nombre en la plataforma -> nombre original normalizado (normalizar_nombre)
VARIABLES_INSCRIPCION: dict[str, str] = {
    # Demográficas
    "estado_civil": "marital status",
    "nacionalidad": "nacionality",
    "desplazado": "displaced",
    "genero": "gender",
    "edad_ingreso": "age at enrollment",
    "internacional": "international",
    # Socioeconómicas
    "nivel_educ_madre": "mother's qualification",
    "nivel_educ_padre": "father's qualification",
    "ocupacion_madre": "mother's occupation",
    "ocupacion_padre": "father's occupation",
    "becario": "scholarship holder",
    # Macroeconómicas (un valor por año de ingreso)
    "tasa_desempleo": "unemployment rate",
    "tasa_inflacion": "inflation rate",
    "variacion_pib": "gdp",
    # Académicas de la inscripción
    "modalidad_ingreso": "application mode",
    "carrera": "course",
    "turno_diurno": "daytime/evening attendance",
    "titulo_previo": "previous qualification",
    "nota_titulo_previo": "previous qualification (grade)",
}

# Entidad RENDIMIENTO_SEMESTRE: campo -> sufijo original entre paréntesis
CAMPOS_RENDIMIENTO: dict[str, str] = {
    "materias_acreditadas": "credited",
    "materias_inscriptas": "enrolled",
    "evaluaciones": "evaluations",
    "materias_aprobadas": "approved",
    "nota_promedio": "grade",
    "materias_sin_evaluacion": "without evaluations",
}


def _rendimiento(semestre: int) -> dict[str, str]:
    ordinal = {1: "1st", 2: "2nd"}[semestre]
    return {
        f"{campo}_s{semestre}": f"curricular units {ordinal} sem ({sufijo})"
        for campo, sufijo in CAMPOS_RENDIMIENTO.items()
    }


VARIABLES_SEMESTRE_1: dict[str, str] = _rendimiento(1)
VARIABLES_SEMESTRE_2: dict[str, str] = _rendimiento(2)

# --- Variables excluidas (decisiones del 14/10 y del 19/10) -------------------
VARIABLES_EXCLUIDAS: dict[str, tuple[str, str]] = {
    # nombre en la plataforma: (nombre original normalizado, motivo)
    "necesidades_especiales": (
        "educational special needs",
        "Dato sensible: puede revelar información de salud (Ley 25.326, arts. 2 y 7).",
    ),
    "deudor": (
        "debtor",
        "Sin equivalente: el grado es gratuito (Ley 24.521, art. 2 bis).",
    ),
    "aranceles_al_dia": (
        "tuition fees up to date",
        "Sin equivalente: el grado es gratuito (Ley 24.521, art. 2 bis).",
    ),
    "orden_postulacion": (
        "application order",
        "Sin equivalente: el ingreso es libre e irrestricto (Ley 24.521, art. 7).",
    ),
    "nota_admision": (
        "admission grade",
        "Sin equivalente: el ingreso es libre e irrestricto (Ley 24.521, art. 7).",
    ),
}

# --- Variable objetivo ---------------------------------------------------------
OBJETIVO_ORIGINAL = "target"
OBJETIVO = "situacion_final"
# Valores del archivo original -> valores en la plataforma
SITUACION_FINAL: dict[str, str] = {
    "Dropout": "abandono",
    "Enrolled": "cursando",  # «sigue cursando»: se agrupa como NO abandono
    "Graduate": "graduado",
}
# Variable binaria del modelo: 1 = abandono, 0 = no abandono (graduado o cursando)
CLASE_POSITIVA = "abandono"

# --- Variables por momento (sin información posterior a la alerta) -------------
VARIABLES_POR_MOMENTO: dict[Momento, list[str]] = {
    Momento.INSCRIPCION: list(VARIABLES_INSCRIPCION),
    Momento.CIERRE_1S: list(VARIABLES_INSCRIPCION) + list(VARIABLES_SEMESTRE_1),
    Momento.CIERRE_2S: list(VARIABLES_INSCRIPCION) + list(VARIABLES_SEMESTRE_1) + list(VARIABLES_SEMESTRE_2),
}

# Variables categóricas codificadas con números: van con one-hot (CRISP-DM, fase 3)
CATEGORICAS: list[str] = [
    "estado_civil",
    "nacionalidad",
    "nivel_educ_madre",
    "nivel_educ_padre",
    "ocupacion_madre",
    "ocupacion_padre",
    "modalidad_ingreso",
    "carrera",
    "titulo_previo",
]
# Variables binarias (0/1): se usan tal cual
BINARIAS: list[str] = ["desplazado", "genero", "internacional", "becario", "turno_diurno"]

# Subgrupos para la evaluación de sesgos (solo sobre el modelo de cierre_1s)
SUBGRUPOS: dict[str, str] = {
    "genero": "Género",
    "edad_ingreso": "Edad de ingreso (hasta 20, 21 a 25, más de 25)",
    "becario": "Condición de becario",
}
CORTES_EDAD: list[tuple[str, int, int]] = [
    ("hasta 20", 0, 20),
    ("21 a 25", 21, 25),
    ("más de 25", 26, 200),
]


def tramo_edad(edad: float) -> str:
    """Tramo de edad de ingreso según CORTES_EDAD («hasta 20», «21 a 25», «más de 25»)."""
    for nombre, desde, hasta in CORTES_EDAD:
        if desde <= edad <= hasta:
            return nombre
    raise ValueError(f"Edad fuera de los cortes: {edad}")

# --- Mapa completo original -> plataforma (para renombrar el CSV) --------------
MAPA_ORIGINAL_A_PLATAFORMA: dict[str, str] = {
    **{orig: nuevo for nuevo, orig in VARIABLES_INSCRIPCION.items()},
    **{orig: nuevo for nuevo, orig in VARIABLES_SEMESTRE_1.items()},
    **{orig: nuevo for nuevo, orig in VARIABLES_SEMESTRE_2.items()},
    **{orig: nuevo for nuevo, (orig, _) in VARIABLES_EXCLUIDAS.items()},
    OBJETIVO_ORIGINAL: OBJETIVO,
}

# El archivo de UCI tiene 36 predictoras + Target = 37 columnas
COLUMNAS_ORIGINALES_ESPERADAS: int = 37
REGISTROS_ESPERADOS: int = 4424
# Distribución publicada (Realinho et al., 2022, p. 7)
DISTRIBUCION_ESPERADA: dict[str, int] = {"Graduate": 2209, "Dropout": 1421, "Enrolled": 794}


def renombrar_columnas(columnas: list[str]) -> dict[str, str]:
    """Devuelve {columna original exacta: nombre en la plataforma}.

    Lanza ValueError si falta alguna columna esperada o si aparece una que no
    está en el mapa, para que el problema se vea en el primer uso.
    """
    resultado: dict[str, str] = {}
    desconocidas: list[str] = []
    for col in columnas:
        clave = normalizar_nombre(col)
        if clave == "nationality":  # por si una versión corrige la errata
            clave = "nacionality"
        if clave in MAPA_ORIGINAL_A_PLATAFORMA:
            resultado[col] = MAPA_ORIGINAL_A_PLATAFORMA[clave]
        else:
            desconocidas.append(col)
    faltantes = set(MAPA_ORIGINAL_A_PLATAFORMA.values()) - set(resultado.values())
    if desconocidas or faltantes:
        raise ValueError(f"Columnas no reconocidas: {desconocidas}. Columnas faltantes: {sorted(faltantes)}")
    return resultado


# Comprobaciones de consistencia con el documento (se ejecutan al importar)
assert len(VARIABLES_POR_MOMENTO[Momento.INSCRIPCION]) == 19
assert len(VARIABLES_POR_MOMENTO[Momento.CIERRE_1S]) == 25
assert len(VARIABLES_POR_MOMENTO[Momento.CIERRE_2S]) == 31
assert len(MAPA_ORIGINAL_A_PLATAFORMA) == COLUMNAS_ORIGINALES_ESPERADAS
assert set(CATEGORICAS) | set(BINARIAS) <= set(VARIABLES_INSCRIPCION)
