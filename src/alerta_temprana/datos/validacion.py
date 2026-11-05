"""Validación de los archivos de carga (HU-001, criterios 2 y 3; tarea 1.3).

Único lugar donde se definen las columnas obligatorias, los rangos y los códigos
aceptados. Hay dos niveles de problema:

- **De la carga completa** (criterio 2, `CargaRechazada`): el archivo no está en
  UTF-8, no está separado por «;», le falta una columna obligatoria, tiene columnas
  repetidas, una columna usa coma decimal o más de la mitad de los valores no vacíos
  de una columna no son numéricos (cambio de formato de la exportación).
- **De un registro** (criterio 3, `ErrorRegistro`): valor faltante, valor no numérico
  suelto, valor no entero, fuera de rango, código desconocido o legajo repetido. El
  registro no se incorpora y va al informe de errores.

Formato del archivo (decisión P2): CSV separado por «;», UTF-8 (se acepta el BOM del
«CSV UTF-8» de Excel), punto decimal y columnas con los nombres de la plataforma.
"""

from __future__ import annotations

import io
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from alerta_temprana.datos import variables as V
from alerta_temprana.modelo.etiquetas import CODIGOS, texto_ocupacion

COLUMNA_LEGAJO = "legajo"
# Identificatorias que puede traer la exportación: se descartan (el legajo, después de seudonimizar)
COLUMNAS_IDENTIFICATORIAS: tuple[str, ...] = ("legajo", "documento", "apellido_nombre")
SEPARADOR = ";"


# --- Reglas por variable --------------------------------------------------------


@dataclass(frozen=True)
class Rango:
    """Valores numéricos aceptados. Son amplios respecto de lo observado en el análisis
    exploratorio (reportes/informe_exploratorio.md, sección 1): solo se rechaza lo
    inverosímil. Ninguno supera la capacidad del tipo de la columna (Tabla 32)."""

    minimo: float
    maximo: float
    entero: bool = False

    def acepta(self, valor: float) -> bool:
        return self.minimo <= valor <= self.maximo

    def describir(self) -> str:
        return f"de {_numero(self.minimo)} a {_numero(self.maximo)}"


@dataclass(frozen=True)
class Codigos:
    """Códigos conocidos de una variable categórica (los del archivo de UCI)."""

    acepta: Callable[[int], bool]


def _ocupacion_conocida(codigo: int) -> bool:
    try:
        texto_ocupacion(codigo)
    except KeyError:
        return False
    return True


def _codigos_de(tabla: Mapping[int, str]) -> Codigos:
    conocidos = frozenset(tabla)
    return Codigos(acepta=lambda codigo: codigo in conocidos)


_MATERIAS = Rango(0, 40, entero=True)  # observado: hasta 26
_EVALUACIONES = Rango(0, 80, entero=True)  # observado: hasta 45
_NOTA_SEMESTRE = Rango(0, 20)  # escala de 0 a 20 (observado: hasta 18,88)

REGLAS: dict[str, Rango | Codigos] = {
    # Categóricas: códigos conocidos (docs/datos/anexo-codigos-realinho-2022.md)
    **{variable: _codigos_de(tabla) for variable, tabla in CODIGOS.items()},
    "ocupacion_madre": Codigos(acepta=_ocupacion_conocida),  # estructura CIUO-08
    "ocupacion_padre": Codigos(acepta=_ocupacion_conocida),
    # Binarias
    **{variable: Rango(0, 1, entero=True) for variable in V.BINARIAS},
    # Numéricas de la inscripción
    "edad_ingreso": Rango(15, 80, entero=True),  # observado: 17 a 70
    "nota_titulo_previo": Rango(0, 200),  # escala de 0 a 200 (observado: 95 a 190)
    "tasa_desempleo": Rango(0, 100),  # % (observado: 7,6 a 16,2); NUMERIC(4,1)
    "tasa_inflacion": Rango(-50, 50),  # % (observado: -0,8 a 3,7); NUMERIC(3,1)
    "variacion_pib": Rango(-50, 50),  # % (observado: -4,06 a 3,51); NUMERIC(4,2)
    # Rendimiento de cada semestre
    **{
        f"{campo}_s{semestre}": (
            _NOTA_SEMESTRE
            if campo == "nota_promedio"
            else _EVALUACIONES
            if campo == "evaluaciones"
            else _MATERIAS
        )
        for campo in V.CAMPOS_RENDIMIENTO
        for semestre in (1, 2)
    },
}
assert set(REGLAS) == set(V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_2S]), "Cada variable necesita una regla"


def columnas_obligatorias(momento: V.Momento) -> list[str]:
    """El legajo (para seudonimizar) y las variables del momento (19, 25 o 31)."""
    return [COLUMNA_LEGAJO, *V.VARIABLES_POR_MOMENTO[momento]]


# --- Problemas que se informan --------------------------------------------------


@dataclass(frozen=True)
class ProblemaColumna:
    columna: str
    motivo: str


class CargaRechazada(Exception):
    """Rechazo de la carga completa (HU-001, criterio 2). No se incorpora ningún registro."""

    def __init__(self, mensaje: str, problemas: list[ProblemaColumna] | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.problemas = problemas or []

    @property
    def columnas(self) -> list[str]:
        return list(dict.fromkeys(p.columna for p in self.problemas))


@dataclass(frozen=True)
class ErrorRegistro:
    """Una línea del informe de errores (HU-001, criterio 3). Nunca lleva el legajo."""

    fila: int  # número de línea en el archivo (el encabezado es la línea 1)
    codigo_estudiante: str | None
    columna: str
    motivo: str


@dataclass
class ResultadoValidacion:
    validos: pd.DataFrame  # columnas obligatorias con valores numéricos; índice = línea del archivo
    errores: list[ErrorRegistro] = field(default_factory=list)

    @property
    def filas_rechazadas(self) -> set[int]:
        return {e.fila for e in self.errores}


# --- Lectura ----------------------------------------------------------------------


def leer_archivo(contenido: bytes) -> pd.DataFrame:
    """Lee el CSV como texto, sin convertir valores.

    Devuelve un DataFrame de cadenas (sin espacios en los extremos) cuyo índice es el
    número de línea en el archivo; las líneas vacías se ignoran. Los nombres de las
    columnas se limpian de espacios y tabuladores. El contenido nunca se escribe en disco.
    """
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise CargaRechazada("El archivo no está en UTF-8. Exportalo como «CSV UTF-8».") from error
    if not texto.strip():
        raise CargaRechazada("El archivo está vacío.")
    try:
        crudo = pd.read_csv(
            io.StringIO(texto),
            sep=SEPARADOR,
            header=None,
            dtype=str,
            keep_default_na=False,
            skip_blank_lines=False,
        )
    except pd.errors.ParserError as error:
        raise CargaRechazada(f"El archivo no tiene una estructura de tabla válida: {error}") from error
    crudo = crudo.fillna("")
    crudo.index = crudo.index + 1  # número de línea (1 = encabezado)
    encabezado = [str(c).strip() for c in crudo.iloc[0]]
    datos = crudo.iloc[1:].apply(lambda col: col.str.strip())
    datos = datos[(datos != "").any(axis=1)]  # sin líneas vacías
    datos.columns = encabezado
    return datos


# --- Estructura (criterio 2) ------------------------------------------------------

_COMA_DECIMAL = re.compile(r"^[+-]?\d+,\d+$")


def _no_numericos(valores: pd.Series) -> pd.Series:
    """Máscara de los valores no vacíos que no se pueden leer como número."""
    no_vacios = valores != ""
    return no_vacios & pd.to_numeric(valores.where(no_vacios), errors="coerce").isna()


def _sugerencia_de_momento(faltantes: set[str], presentes: set[str], momento: V.Momento) -> str:
    """Si faltan exactamente las columnas que agrega el momento elegido respecto de uno
    anterior, el archivo probablemente es de ese momento anterior."""
    orden = list(V.Momento)
    for anterior in orden[: orden.index(momento)]:
        agregadas = set(V.VARIABLES_POR_MOMENTO[momento]) - set(V.VARIABLES_POR_MOMENTO[anterior])
        if faltantes == agregadas and set(columnas_obligatorias(anterior)) <= presentes:
            elegido, otro = V.ETIQUETA_MOMENTO[momento], V.ETIQUETA_MOMENTO[anterior]
            return (
                f" Faltan exactamente las columnas que «{elegido}» agrega a «{otro}»: "
                f"el archivo parece de «{otro}». Revisá el momento elegido."
            )
    return ""


def validar_estructura(datos: pd.DataFrame, momento: V.Momento) -> None:
    """Lanza CargaRechazada si el archivo no tiene la estructura esperada para el momento."""
    columnas = list(datos.columns)
    if len(columnas) == 1 and "," in columnas[0]:
        raise CargaRechazada(
            "El archivo no está separado por «;» (parece separado por «,»). "
            "Exportalo con «;» como separador.",
            [ProblemaColumna(c.strip(), "separador distinto de «;»") for c in columnas[0].split(",")],
        )

    problemas: list[ProblemaColumna] = []
    repetidas = sorted({c for c in columnas if columnas.count(c) > 1})
    problemas += [ProblemaColumna(c, "columna repetida") for c in repetidas]

    obligatorias = columnas_obligatorias(momento)
    faltantes = [c for c in obligatorias if c not in columnas]
    problemas += [ProblemaColumna(c, "falta la columna obligatoria") for c in faltantes]

    coma_decimal: list[str] = []
    for columna in obligatorias:
        if columna == COLUMNA_LEGAJO or columna not in columnas or columna in repetidas:
            continue
        valores = datos[columna]
        if valores.str.match(_COMA_DECIMAL).any():
            coma_decimal.append(columna)
            problemas.append(ProblemaColumna(columna, "usa coma decimal; el archivo debe usar punto"))
            continue
        no_vacios = int((valores != "").sum())
        if no_vacios and _no_numericos(valores).sum() > no_vacios / 2:
            problemas.append(ProblemaColumna(columna, "más de la mitad de los valores no son numéricos"))

    if not problemas:
        if datos.empty:
            raise CargaRechazada("El archivo no tiene registros.")
        return

    partes = []
    if faltantes:
        partes.append(
            "faltan columnas obligatorias: "
            + ", ".join(faltantes)
            + "."
            + _sugerencia_de_momento(set(faltantes), set(columnas), momento)
        )
    if repetidas:
        partes.append("columnas repetidas: " + ", ".join(repetidas) + ".")
    for columna in coma_decimal:
        partes.append(f"la columna {columna} usa coma decimal; el archivo debe usar punto.")
    otro_formato = [p.columna for p in problemas if p.motivo.startswith("más de la mitad")]
    if otro_formato:
        partes.append("columnas con otro formato (valores no numéricos): " + ", ".join(otro_formato) + ".")
    raise CargaRechazada("Se rechazó la carga completa: " + " ".join(partes), problemas)


# --- Registros (criterio 3) -------------------------------------------------------


def validar_registros(datos: pd.DataFrame, momento: V.Momento, codigos: pd.Series) -> ResultadoValidacion:
    """Valida cada registro. `codigos` es el código seudonimizado de cada línea (o None si
    falta el legajo): el informe de errores usa el código, nunca el legajo."""
    errores: list[ErrorRegistro] = []

    def anotar(mascara: pd.Series, columna: str, motivo: str) -> None:
        for fila in mascara[mascara].index:
            errores.append(ErrorRegistro(int(fila), codigos.get(fila), columna, motivo))

    legajos = datos[COLUMNA_LEGAJO]
    anotar(legajos == "", COLUMNA_LEGAJO, "valor faltante")
    anotar((legajos != "") & legajos.duplicated(keep=False), COLUMNA_LEGAJO, "legajo repetido en el archivo")

    numericos = pd.DataFrame(index=datos.index)
    for variable in V.VARIABLES_POR_MOMENTO[momento]:
        texto = datos[variable]
        valores = pd.to_numeric(texto.where(texto != ""), errors="coerce").astype(float)
        numericos[variable] = valores
        finitos = pd.Series(np.isfinite(valores.to_numpy()), index=valores.index)
        anotar(texto == "", variable, "valor faltante")
        anotar((texto != "") & ~finitos, variable, "valor no numérico")  # texto suelto, «inf», «nan»

        regla = REGLAS[variable]
        if isinstance(regla, Codigos) or regla.entero:
            no_entero = finitos & (valores % 1 != 0)
            anotar(no_entero, variable, "valor no entero")
            finitos = finitos & ~no_entero
        if isinstance(regla, Rango):
            anotar(
                finitos & ~valores.between(regla.minimo, regla.maximo),
                variable,
                f"fuera de rango ({regla.describir()})",
            )
        else:
            desconocido = [
                bool(ok) and not regla.acepta(int(v)) for v, ok in zip(valores, finitos, strict=True)
            ]
            anotar(pd.Series(desconocido, index=valores.index), variable, "código desconocido")

    errores.sort(key=lambda e: (e.fila, e.columna))
    rechazadas = {e.fila for e in errores}
    validos = numericos.loc[[f for f in numericos.index if f not in rechazadas]]
    validos.insert(0, "codigo_estudiante", codigos.loc[validos.index])
    return ResultadoValidacion(validos=validos, errores=errores)


def _numero(valor: float) -> str:
    return str(int(valor)) if float(valor).is_integer() else f"{valor}".replace(".", ",")
