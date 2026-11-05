"""Genera los archivos de prueba de HU-001 (tests/fixtures/*.csv).

Son datos **sintéticos** (no salen del dataset): 10 estudiantes ficticios con valores
válidos y variantes con errores. Se versionan; para regenerarlos:

    python tests/fixtures/generar_fixtures.py
"""

from __future__ import annotations

import random
from pathlib import Path

from alerta_temprana.datos import variables as V

CARPETA = Path(__file__).resolve().parent
CANTIDAD = 10
IDENTIFICATORIAS = ["legajo", "documento", "apellido_nombre"]


def _estudiante(numero: int, generador: random.Random) -> dict[str, object]:
    fila: dict[str, object] = {
        "legajo": f"T{numero:04d}",
        "documento": str(99000000 + numero),
        "apellido_nombre": f"Estudiante de prueba {numero:02d}",
        "estado_civil": generador.choice([1, 1, 1, 2, 4]),
        "nacionalidad": generador.choice([1, 1, 1, 41]),
        "desplazado": generador.randint(0, 1),
        "genero": generador.randint(0, 1),
        "edad_ingreso": generador.randint(17, 40),
        "internacional": 0,
        "nivel_educ_madre": generador.choice([1, 19, 37, 38]),
        "nivel_educ_padre": generador.choice([1, 19, 37, 38]),
        "ocupacion_madre": generador.choice([0, 4, 5, 9, 191]),
        "ocupacion_padre": generador.choice([0, 5, 7, 9, 193]),
        "becario": generador.randint(0, 1),
        "tasa_desempleo": generador.choice([7.6, 10.8, 13.9, 16.2]),
        "tasa_inflacion": generador.choice([-0.8, 0.6, 1.4, 3.7]),
        "variacion_pib": generador.choice([-4.06, 0.32, 1.74, 3.51]),
        "modalidad_ingreso": generador.choice([1, 17, 39, 43]),
        "carrera": generador.choice([9238, 9500, 9773, 9991]),
        "turno_diurno": generador.choice([1, 1, 0]),
        "titulo_previo": generador.choice([1, 1, 39]),
        "nota_titulo_previo": round(generador.uniform(100, 180), 1),
        # Excluidas: vienen en la exportación y se descartan (criterio 4)
        "necesidades_especiales": 0,
        "deudor": generador.randint(0, 1),
        "aranceles_al_dia": 1,
        "orden_postulacion": generador.randint(1, 6),
        "nota_admision": round(generador.uniform(100, 180), 1),
    }
    for semestre in (1, 2):
        inscriptas = generador.randint(5, 7)
        fila |= {
            f"materias_acreditadas_s{semestre}": 0,
            f"materias_inscriptas_s{semestre}": inscriptas,
            f"evaluaciones_s{semestre}": inscriptas + generador.randint(0, 3),
            f"materias_aprobadas_s{semestre}": generador.randint(0, inscriptas),
            f"nota_promedio_s{semestre}": round(generador.uniform(10, 16), 6),
            f"materias_sin_evaluacion_s{semestre}": 0,
        }
    return fila


def _columnas(momento: V.Momento) -> list[str]:
    semestres = V.VARIABLES_POR_MOMENTO[momento][len(V.VARIABLES_INSCRIPCION) :]
    return IDENTIFICATORIAS + list(V.VARIABLES_INSCRIPCION) + list(V.VARIABLES_EXCLUIDAS) + semestres


def _escribir(nombre: str, filas: list[dict], columnas: list[str], sep: str = ";") -> None:
    lineas = [sep.join(columnas)]
    lineas += [sep.join(str(f.get(c, "")) for c in columnas) for f in filas]
    (CARPETA / nombre).write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main() -> None:
    generador = random.Random(42)
    filas = [_estudiante(n, generador) for n in range(1, CANTIDAD + 1)]

    # Válidos, uno por momento (los mismos 10 estudiantes)
    for momento in V.Momento:
        _escribir(f"{momento.value}_valida.csv", filas, _columnas(momento))

    columnas_inscripcion = _columnas(V.Momento.INSCRIPCION)

    # Criterio 2: estructura
    _escribir("sin_columna.csv", filas, [c for c in columnas_inscripcion if c != "carrera"])
    _escribir("separado_por_coma.csv", filas, columnas_inscripcion, sep=",")
    con_texto = [f | {"genero": "Masculino" if f["genero"] else "Femenino"} for f in filas]
    _escribir("con_texto.csv", con_texto, columnas_inscripcion)
    coma_decimal = [f | {"nota_titulo_previo": str(f["nota_titulo_previo"]).replace(".", ",")} for f in filas]
    _escribir("coma_decimal.csv", coma_decimal, columnas_inscripcion)

    # Criterio 3: tres registros con errores (líneas 3, 6 y 9 del archivo)
    con_errores = [dict(f) for f in filas]
    con_errores[1]["edad_ingreso"] = ""  # faltante
    con_errores[4]["nota_titulo_previo"] = 250  # fuera de rango (0 a 200)
    con_errores[7]["carrera"] = 1234  # código desconocido
    _escribir("registros_con_errores.csv", con_errores, columnas_inscripcion)

    # Un valor no numérico suelto: se rechaza solo ese registro (línea 4)
    suelto = [dict(f) for f in filas]
    suelto[2]["edad_ingreso"] = "veinte"
    _escribir("valor_no_numerico_suelto.csv", suelto, columnas_inscripcion)

    # «CSV UTF-8» de Excel: con BOM y espacios en los nombres de las columnas
    encabezado = ";".join(f" {c}\t" if c == "turno_diurno" else f" {c} " for c in columnas_inscripcion)
    datos = [";".join(str(f[c]) for c in columnas_inscripcion) for f in filas]
    (CARPETA / "con_bom_y_espacios.csv").write_text(
        "\n".join([encabezado, *datos]) + "\n", encoding="utf-8-sig"
    )


if __name__ == "__main__":
    main()
