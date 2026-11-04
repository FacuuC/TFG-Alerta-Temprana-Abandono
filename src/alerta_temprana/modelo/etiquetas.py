"""Nombres y valores comprensibles para la ficha (HU-006, tarea 6.2; criterio 3).

Los códigos son los del archivo de UCI (verificados el 03/11; ver
docs/datos/anexo-codigos-realinho-2022.md). La traducción al español es propia.
Ejemplo de salida: «Materias aprobadas en el 1.er semestre: 2 de 6».
"""

from __future__ import annotations

from collections.abc import Mapping

from alerta_temprana.datos import variables as V

NOMBRES: dict[str, str] = {
    "estado_civil": "Estado civil",
    "nacionalidad": "Nacionalidad",
    "desplazado": "Vive fuera de su lugar de origen para estudiar",
    "genero": "Género",
    "edad_ingreso": "Edad al ingresar",
    "internacional": "Estudiante internacional",
    "nivel_educ_madre": "Nivel educativo de la madre",
    "nivel_educ_padre": "Nivel educativo del padre",
    "ocupacion_madre": "Ocupación de la madre",
    "ocupacion_padre": "Ocupación del padre",
    "becario": "Becario",
    "tasa_desempleo": "Desempleo del año de ingreso",
    "tasa_inflacion": "Inflación del año de ingreso",
    "variacion_pib": "Variación del PIB del año de ingreso",
    "modalidad_ingreso": "Modalidad de ingreso",
    "carrera": "Carrera",
    "turno_diurno": "Turno",
    "titulo_previo": "Estudios previos",
    "nota_titulo_previo": "Nota de los estudios previos",
}
_RENDIMIENTO = {
    "materias_acreditadas": "Materias acreditadas por equivalencia",
    "materias_inscriptas": "Materias inscriptas",
    "evaluaciones": "Evaluaciones rendidas",
    "materias_aprobadas": "Materias aprobadas",
    "nota_promedio": "Nota promedio",
    "materias_sin_evaluacion": "Materias sin evaluaciones",
}
_SEMESTRE = {1: "en el 1.er semestre", 2: "en el 2.º semestre"}
for _campo, _texto in _RENDIMIENTO.items():
    for _s, _sufijo in _SEMESTRE.items():
        NOMBRES[f"{_campo}_s{_s}"] = f"{_texto} {_sufijo}"

ESTADO_CIVIL = {
    1: "soltero/a",
    2: "casado/a",
    3: "viudo/a",
    4: "divorciado/a",
    5: "unión de hecho",
    6: "separado/a legalmente",
}

NACIONALIDAD = {
    1: "portuguesa",
    2: "alemana",
    6: "española",
    11: "italiana",
    13: "neerlandesa",
    14: "inglesa",
    17: "lituana",
    21: "angoleña",
    22: "caboverdiana",
    24: "guineana",
    25: "mozambiqueña",
    26: "santotomense",
    32: "turca",
    41: "brasileña",
    62: "rumana",
    100: "moldava",
    101: "mexicana",
    103: "ucraniana",
    105: "rusa",
    108: "cubana",
    109: "colombiana",
}

MODALIDAD_INGRESO = {
    1: "1.ª fase, contingente general",
    2: "Ordenanza N.º 612/93",
    5: "1.ª fase, contingente especial (Azores)",
    7: "con otro título superior",
    10: "Ordenanza N.º 854-B/99",
    15: "estudiante internacional",
    16: "1.ª fase, contingente especial (Madeira)",
    17: "2.ª fase, contingente general",
    18: "3.ª fase, contingente general",
    26: "Ordenanza N.º 533-A/99, b2 (otro plan)",
    27: "Ordenanza N.º 533-A/99, b3 (otra institución)",
    39: "mayores de 23 años",
    42: "pase",
    43: "cambio de carrera",
    44: "con diploma de especialización tecnológica",
    51: "cambio de institución o carrera",
    53: "con diploma de ciclo corto",
    57: "cambio de institución o carrera (internacional)",
}

CARRERA = {
    33: "Tecnologías de Producción de Biocombustibles",
    171: "Diseño de Animación y Multimedia",
    8014: "Servicio Social (nocturno)",
    9003: "Agronomía",
    9070: "Diseño de Comunicación",
    9085: "Enfermería Veterinaria",
    9119: "Ingeniería Informática",
    9130: "Equinocultura",
    9147: "Gestión",
    9238: "Servicio Social",
    9254: "Turismo",
    9500: "Enfermería",
    9556: "Higiene Oral",
    9670: "Gestión de Publicidad y Marketing",
    9773: "Periodismo y Comunicación",
    9853: "Educación Básica",
    9991: "Gestión (nocturno)",
}

TITULO_PREVIO = {
    1: "secundario completo",
    2: "superior: bachillerato",
    3: "superior: licenciatura",
    4: "superior: maestría",
    5: "superior: doctorado",
    6: "estudios superiores sin terminar",
    9: "12.º año incompleto",
    10: "11.º año incompleto",
    12: "otro: 11.º año",
    14: "10.º año",
    15: "10.º año incompleto",
    19: "básica, 3.er ciclo (9.º a 11.º año)",
    38: "básica, 2.º ciclo (6.º a 8.º año)",
    39: "curso de especialización tecnológica",
    40: "superior: licenciatura (1.er ciclo)",
    42: "curso técnico superior profesional",
    43: "superior: maestría (2.º ciclo)",
}

# Nivel educativo de madre y padre: códigos de UCI ordenados ↔ tabla A6 del anexo (1 a 34)
NIVEL_EDUCATIVO = {
    1: "secundario completo (12.º año)",
    2: "superior: bachillerato",
    3: "superior: licenciatura",
    4: "superior: maestría",
    5: "superior: doctorado",
    6: "estudios superiores sin terminar",
    9: "12.º año incompleto",
    10: "11.º año incompleto",
    11: "7.º año (plan anterior)",
    12: "otro: 11.º año",
    13: "2.º año del curso complementario de secundario",
    14: "10.º año",
    18: "curso general de comercio",
    19: "básica, 3.er ciclo (9.º a 11.º año)",
    20: "curso complementario de secundario",
    22: "curso técnico-profesional",
    25: "curso complementario de secundario incompleto",
    26: "7.º año",
    27: "2.º ciclo del curso general de secundario",
    29: "9.º año incompleto",
    30: "8.º año",
    31: "curso general de administración y comercio",
    33: "curso complementario de contabilidad y administración",
    34: "sin dato",
    35: "no sabe leer ni escribir",
    36: "sabe leer, sin 4.º año completo",
    37: "básica, 1.er ciclo (4.º/5.º año)",
    38: "básica, 2.º ciclo (6.º a 8.º año)",
    39: "curso de especialización tecnológica",
    40: "superior: licenciatura (1.er ciclo)",
    41: "estudios superiores especializados",
    42: "curso técnico superior profesional",
    43: "superior: maestría (2.º ciclo)",
    44: "superior: doctorado (3.er ciclo)",
}

# Ocupación: los códigos siguen la Clasificación Internacional Uniforme de Ocupaciones
# (CIUO-08): 1 a 9 son grandes grupos y 1XY es el subgrupo XY. En la ficha alcanza el
# gran grupo, que es comprensible y no depende de una traducción fina.
GRANDES_GRUPOS_OCUPACION = {
    1: "directores y gerentes",
    2: "profesionales científicos e intelectuales",
    3: "técnicos y profesionales de nivel medio",
    4: "personal de apoyo administrativo",
    5: "trabajadores de los servicios y vendedores",
    6: "agricultores y trabajadores agropecuarios calificados",
    7: "oficiales, operarios y artesanos",
    8: "operadores de instalaciones y máquinas",
    9: "ocupaciones elementales",
}


def texto_ocupacion(codigo: int) -> str:
    if codigo == 0:
        return "estudiante"
    if codigo == 90:
        return "otra situación"
    if codigo == 99:
        return "sin dato"
    if codigo == 10 or 101 <= codigo <= 103:
        return "fuerzas armadas"
    if 1 <= codigo <= 9:
        return GRANDES_GRUPOS_OCUPACION[codigo]
    if 110 <= codigo <= 199:
        return GRANDES_GRUPOS_OCUPACION[(codigo // 10) % 10]
    raise KeyError(codigo)


CODIGOS: dict[str, Mapping[int, str]] = {
    "estado_civil": ESTADO_CIVIL,
    "nacionalidad": NACIONALIDAD,
    "modalidad_ingreso": MODALIDAD_INGRESO,
    "carrera": CARRERA,
    "titulo_previo": TITULO_PREVIO,
    "nivel_educ_madre": NIVEL_EDUCATIVO,
    "nivel_educ_padre": NIVEL_EDUCATIVO,
}


def _decimal(valor: float, decimales: int = 1) -> str:
    return f"{valor:.{decimales}f}".replace(".", ",")


def texto_valor(variable: str, fila: Mapping[str, float]) -> str:
    """Valor comprensible de una variable para un estudiante (fila con todas sus variables)."""
    valor = fila[variable]
    if variable in CODIGOS:
        return CODIGOS[variable].get(int(valor), f"código {int(valor)}")
    if variable in ("ocupacion_madre", "ocupacion_padre"):
        return texto_ocupacion(int(valor))
    if variable == "genero":
        return "masculino" if int(valor) == 1 else "femenino"
    if variable == "turno_diurno":
        return "diurno" if int(valor) == 1 else "nocturno"
    if variable in ("desplazado", "internacional", "becario"):
        return "sí" if int(valor) == 1 else "no"
    if variable == "edad_ingreso":
        return f"{int(valor)} años"
    if variable in ("tasa_desempleo", "tasa_inflacion"):
        return f"{_decimal(valor)} %"
    if variable == "variacion_pib":
        return f"{_decimal(valor, 2)} %"
    if variable == "nota_titulo_previo":
        return f"{_decimal(valor)} (escala de 0 a 200)"
    if variable.startswith("materias_aprobadas_s"):
        semestre = variable[-1]
        inscriptas = int(fila[f"materias_inscriptas_s{semestre}"])
        if inscriptas == 0:
            return f"{int(valor)} (sin materias inscriptas)"
        return f"{int(valor)} de {inscriptas}"
    if variable.startswith("nota_promedio_s"):
        semestre = variable[-1]
        if float(valor) == 0 and int(fila[f"materias_aprobadas_s{semestre}"]) == 0:
            return "sin notas registradas"
        return f"{_decimal(valor)} (escala de 0 a 20)"
    if variable.startswith(tuple(_RENDIMIENTO)):
        return str(int(valor))
    raise KeyError(f"Variable sin formato definido: {variable}")


def texto_factor(variable: str, fila: Mapping[str, float]) -> str:
    """Texto completo de un factor, por ejemplo «Materias aprobadas en el 1.er semestre: 2 de 6»."""
    return f"{NOMBRES[variable]}: {texto_valor(variable, fila)}"


assert set(NOMBRES) == set(V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_2S])
