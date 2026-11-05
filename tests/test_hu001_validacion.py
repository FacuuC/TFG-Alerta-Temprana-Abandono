"""HU-001, tarea 1.3: estructura (criterio 2) y registros (criterio 3), sin base de datos.

Archivos sintéticos en tests/fixtures/ (generar_fixtures.py).
"""

import json

import pytest

from alerta_temprana.datos import variables as V
from alerta_temprana.datos.carga import informe_errores_csv, procesar_archivo
from alerta_temprana.datos.validacion import REGLAS, CargaRechazada, Codigos, columnas_obligatorias

CLAVE = "clave-de-pruebas"
M = V.Momento


def _leer(ruta_fixtures, nombre: str) -> bytes:
    return (ruta_fixtures / nombre).read_bytes()


def _con_cambio_bytes(contenido: bytes, linea: int, columna: str, valor: str) -> bytes:
    """Copia de un archivo con un valor cambiado (`linea` es la línea del archivo, 2 = primer registro)."""
    lineas = contenido.decode("utf-8").splitlines()
    encabezado = lineas[0].split(";")
    celdas = lineas[linea - 1].split(";")
    celdas[encabezado.index(columna)] = valor
    lineas[linea - 1] = ";".join(celdas)
    return ("\n".join(lineas) + "\n").encode("utf-8")


def _con_cambio(ruta_fixtures, nombre: str, linea: int, columna: str, valor: str) -> bytes:
    return _con_cambio_bytes(_leer(ruta_fixtures, nombre), linea, columna, valor)


# --- Criterio 1: archivo válido ---------------------------------------------------


@pytest.mark.parametrize("momento", list(M))
def test_archivo_valido_incorpora_todos_e_informa_la_cantidad(ruta_fixtures, momento):
    resultado = procesar_archivo(_leer(ruta_fixtures, f"{momento.value}_valida.csv"), momento, CLAVE)
    assert resultado.registros_validos == 10
    assert resultado.registros_rechazados == 0
    assert resultado.errores == []
    assert len(resultado.estudiantes) == 10
    assert len(resultado.rendimientos) == 10 * {M.INSCRIPCION: 0, M.CIERRE_1S: 1, M.CIERRE_2S: 2}[momento]


def test_columnas_obligatorias_son_legajo_y_las_del_momento():
    for momento in M:
        assert columnas_obligatorias(momento) == ["legajo", *V.VARIABLES_POR_MOMENTO[momento]]


# --- Criterio 2: rechazo de la carga completa ---------------------------------------


def test_sin_columna_obligatoria_rechaza_e_indica_la_columna(ruta_fixtures):
    with pytest.raises(CargaRechazada) as error:
        procesar_archivo(_leer(ruta_fixtures, "sin_columna.csv"), M.INSCRIPCION, CLAVE)
    assert error.value.columnas == ["carrera"]
    assert "carrera" in error.value.mensaje


def test_separado_por_coma_rechaza_con_mensaje_explicito(ruta_fixtures):
    with pytest.raises(CargaRechazada) as error:
        procesar_archivo(_leer(ruta_fixtures, "separado_por_coma.csv"), M.INSCRIPCION, CLAVE)
    assert "no está separado por «;»" in error.value.mensaje
    assert "carrera" in error.value.columnas


def test_columna_con_texto_es_cambio_de_formato_y_rechaza_todo(ruta_fixtures):
    """Punto 1 de la aprobación: más de la mitad de los valores no numéricos → criterio 2."""
    with pytest.raises(CargaRechazada) as error:
        procesar_archivo(_leer(ruta_fixtures, "con_texto.csv"), M.INSCRIPCION, CLAVE)
    assert error.value.columnas == ["genero"]
    assert "otro formato" in error.value.mensaje


def test_coma_decimal_rechaza_con_mensaje_explicito(ruta_fixtures):
    """Punto 1: la coma decimal se detecta aparte, aunque sea un solo valor."""
    with pytest.raises(CargaRechazada) as error:
        procesar_archivo(_leer(ruta_fixtures, "coma_decimal.csv"), M.INSCRIPCION, CLAVE)
    assert error.value.columnas == ["nota_titulo_previo"]
    assert "la columna nota_titulo_previo usa coma decimal; el archivo debe usar punto" in error.value.mensaje

    un_solo_valor = _con_cambio(ruta_fixtures, "inscripcion_valida.csv", 5, "tasa_desempleo", "10,8")
    with pytest.raises(CargaRechazada) as error:
        procesar_archivo(un_solo_valor, M.INSCRIPCION, CLAVE)
    assert error.value.columnas == ["tasa_desempleo"]


def test_mitad_exacta_no_numerica_no_es_cambio_de_formato(ruta_fixtures):
    """Punto 1: el umbral es «más de la mitad»; 5 de 10 se rechazan registro por registro."""
    contenido = _leer(ruta_fixtures, "inscripcion_valida.csv")
    for linea in range(2, 7):  # 5 de los 10 registros
        contenido = _con_cambio_bytes(contenido, linea, "becario", "si")
    resultado = procesar_archivo(contenido, M.INSCRIPCION, CLAVE)
    assert resultado.registros_validos == 5
    assert {e.motivo for e in resultado.errores} == {"valor no numérico"}

    contenido = _con_cambio_bytes(contenido, 7, "becario", "si")  # 6 de 10: más de la mitad
    with pytest.raises(CargaRechazada) as error:
        procesar_archivo(contenido, M.INSCRIPCION, CLAVE)
    assert error.value.columnas == ["becario"]


def test_columnas_faltantes_del_momento_sugieren_revisar_el_momento(ruta_fixtures):
    """Punto 4: archivo de inscripción cargado como cierre del 1.er semestre."""
    with pytest.raises(CargaRechazada) as error:
        procesar_archivo(_leer(ruta_fixtures, "inscripcion_valida.csv"), M.CIERRE_1S, CLAVE)
    assert set(error.value.columnas) == set(V.VARIABLES_SEMESTRE_1)
    assert "Revisá el momento elegido" in error.value.mensaje
    assert "parece de «Inscripción»" in error.value.mensaje

    with pytest.raises(CargaRechazada) as error:
        procesar_archivo(_leer(ruta_fixtures, "cierre_1s_valida.csv"), M.CIERRE_2S, CLAVE)
    assert "parece de «Cierre del 1.er semestre»" in error.value.mensaje


def test_otra_columna_faltante_no_sugiere_el_momento(ruta_fixtures):
    """Punto 4: si falta algo más que las columnas del momento, no se sugiere cambiarlo."""
    with pytest.raises(CargaRechazada) as error:
        procesar_archivo(_leer(ruta_fixtures, "sin_columna.csv"), M.CIERRE_1S, CLAVE)
    assert "Revisá el momento elegido" not in error.value.mensaje


def test_bom_y_espacios_en_los_nombres_de_columnas_se_aceptan(ruta_fixtures):
    """Punto 3: «CSV UTF-8» de Excel (con BOM) y encabezados con espacios o tabuladores."""
    contenido = _leer(ruta_fixtures, "con_bom_y_espacios.csv")
    assert contenido.startswith(b"\xef\xbb\xbf")
    resultado = procesar_archivo(contenido, M.INSCRIPCION, CLAVE)
    assert resultado.registros_validos == 10
    assert list(resultado.estudiantes.columns) == ["codigo_estudiante", *V.VARIABLES_INSCRIPCION]


def test_archivo_que_no_es_utf8_rechaza(ruta_fixtures):
    contenido = _leer(ruta_fixtures, "inscripcion_valida.csv").decode("utf-8").encode("utf-16")
    with pytest.raises(CargaRechazada, match="UTF-8"):
        procesar_archivo(contenido, M.INSCRIPCION, CLAVE)


def test_archivo_vacio_o_sin_registros_rechaza(ruta_fixtures):
    with pytest.raises(CargaRechazada, match="vacío"):
        procesar_archivo(b"", M.INSCRIPCION, CLAVE)
    encabezado = _leer(ruta_fixtures, "inscripcion_valida.csv").decode("utf-8").splitlines()[0]
    with pytest.raises(CargaRechazada, match="no tiene registros"):
        procesar_archivo((encabezado + "\n").encode("utf-8"), M.INSCRIPCION, CLAVE)


def test_columna_repetida_rechaza(ruta_fixtures):
    lineas = _leer(ruta_fixtures, "inscripcion_valida.csv").decode("utf-8").splitlines()
    lineas = [linea + ";" + linea.split(";")[18] for linea in lineas]  # repite «carrera»
    with pytest.raises(CargaRechazada) as error:
        procesar_archivo("\n".join(lineas).encode("utf-8"), M.INSCRIPCION, CLAVE)
    assert error.value.columnas == ["carrera"]


# --- Criterio 3: registros con errores ----------------------------------------------


def test_tres_registros_con_errores_no_se_incorporan_y_van_al_informe(ruta_fixtures):
    resultado = procesar_archivo(_leer(ruta_fixtures, "registros_con_errores.csv"), M.INSCRIPCION, CLAVE)
    assert resultado.registros_validos == 7
    assert resultado.registros_rechazados == 3
    assert [(e.fila, e.columna, e.motivo) for e in resultado.errores] == [
        (3, "edad_ingreso", "valor faltante"),
        (6, "nota_titulo_previo", "fuera de rango (de 0 a 200)"),
        (9, "carrera", "código desconocido"),
    ]
    rechazados = {e.codigo_estudiante for e in resultado.errores}
    assert not rechazados & set(resultado.estudiantes["codigo_estudiante"])


def test_valor_no_numerico_suelto_rechaza_solo_ese_registro(ruta_fixtures):
    """Punto 1: un valor suelto con texto es un error del registro (criterio 3)."""
    resultado = procesar_archivo(_leer(ruta_fixtures, "valor_no_numerico_suelto.csv"), M.INSCRIPCION, CLAVE)
    assert resultado.registros_validos == 9
    assert [(e.fila, e.columna, e.motivo) for e in resultado.errores] == [
        (4, "edad_ingreso", "valor no numérico")
    ]


@pytest.mark.parametrize(
    ("columna", "valor", "motivo"),
    [
        ("edad_ingreso", "14", "fuera de rango (de 15 a 80)"),
        ("edad_ingreso", "20.5", "valor no entero"),
        ("genero", "2", "fuera de rango (de 0 a 1)"),
        ("ocupacion_madre", "50", "código desconocido"),
        ("tasa_inflacion", "60", "fuera de rango (de -50 a 50)"),
        ("nota_titulo_previo", "inf", "valor no numérico"),
    ],
)
def test_motivos_de_rechazo_por_registro(ruta_fixtures, columna, valor, motivo):
    contenido = _con_cambio(ruta_fixtures, "inscripcion_valida.csv", 2, columna, valor)
    resultado = procesar_archivo(contenido, M.INSCRIPCION, CLAVE)
    assert [(e.fila, e.columna, e.motivo) for e in resultado.errores] == [(2, columna, motivo)]


def test_rango_de_las_notas_del_semestre(ruta_fixtures):
    contenido = _con_cambio(ruta_fixtures, "cierre_1s_valida.csv", 2, "nota_promedio_s1", "20.5")
    resultado = procesar_archivo(contenido, M.CIERRE_1S, CLAVE)
    assert [(e.columna, e.motivo) for e in resultado.errores] == [
        ("nota_promedio_s1", "fuera de rango (de 0 a 20)")
    ]


def test_legajo_faltante_o_repetido(ruta_fixtures):
    contenido = _con_cambio(ruta_fixtures, "inscripcion_valida.csv", 2, "legajo", "")
    contenido = _con_cambio_bytes(contenido, 4, "legajo", "T0005")  # repite el de la línea 6
    resultado = procesar_archivo(contenido, M.INSCRIPCION, CLAVE)
    assert [(e.fila, e.codigo_estudiante is None, e.motivo) for e in resultado.errores] == [
        (2, True, "valor faltante"),
        (4, False, "legajo repetido en el archivo"),
        (6, False, "legajo repetido en el archivo"),
    ]
    assert resultado.registros_validos == 7


def test_informe_de_errores_csv_sin_legajo(ruta_fixtures):
    resultado = procesar_archivo(_leer(ruta_fixtures, "registros_con_errores.csv"), M.INSCRIPCION, CLAVE)
    informe = informe_errores_csv(resultado.errores)
    assert informe.startswith(b"\xef\xbb\xbf")
    texto = informe.decode("utf-8-sig")
    assert texto.splitlines()[0] == "fila;codigo_estudiante;columna;motivo"
    assert len(texto.splitlines()) == 4
    assert "T000" not in texto  # ningún legajo
    assert "EST-" in texto


# --- Reglas -------------------------------------------------------------------------


def test_cada_variable_del_modelo_tiene_una_regla():
    assert set(REGLAS) == set(V.VARIABLES_POR_MOMENTO[M.CIERRE_2S])


@pytest.mark.datos
def test_los_codigos_del_dataset_son_conocidos(ruta_dataset):
    """Todos los códigos de las categóricas del archivo de UCI pasan la validación."""
    fuente = json.loads((ruta_dataset.parent / "fuente.json").read_text(encoding="utf-8"))
    for variable, codigos in fuente["valores_codificados"].items():
        regla = REGLAS[variable]
        assert isinstance(regla, Codigos)
        assert all(regla.acepta(int(c)) for c in codigos), variable


@pytest.mark.datos
def test_el_dataset_completo_respeta_los_rangos(ruta_dataset):
    """Controles de calidad sin la variable objetivo: ningún registro real queda fuera de rango."""
    from alerta_temprana.modelo.preparacion import cargar_variables_sin_objetivo

    df = cargar_variables_sin_objetivo(ruta_dataset)
    assert V.OBJETIVO not in df.columns
    for variable, regla in REGLAS.items():
        valores = df[variable]
        if isinstance(regla, Codigos):
            assert valores.map(lambda v, r=regla: r.acepta(int(v))).all(), variable
        else:
            assert valores.between(regla.minimo, regla.maximo).all(), variable
            if regla.entero:
                assert (valores % 1 == 0).all(), variable
