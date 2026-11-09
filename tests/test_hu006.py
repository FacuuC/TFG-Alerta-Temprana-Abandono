"""HU-006: ficha del estudiante con la explicación del riesgo (tarea 6.3).

Las pruebas con base siembran una alerta sintética con su predicción vigente y cinco
factores guardados como los guarda el servicio de predicción (valor sin formatear), sin
modelos ni dataset. El caso sembrado reproduce la ficha de EST-932B2E48 de la base de la
Demo (nivel alto, cierre del 2.º semestre).

El criterio 5 (valoración media del cuestionario ≥ 4) no se verifica: el cuestionario no
se aplica (decisión del 05/11; docs/pendientes-documento.md).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from alerta_temprana.app import app
from alerta_temprana.datos import variables as V
from alerta_temprana.db.sesion import obtener_sesion
from alerta_temprana.db.tablas import (
    Alerta,
    Carga,
    Estudiante,
    FactorExplicativo,
    Modelo,
    Prediccion,
    RendimientoSemestre,
    Usuario,
)
from alerta_temprana.servicio.ficha import consultar_ficha
from tests.test_hu003 import archivos_de_carga  # noqa: F401  (fixture de los archivos simulados)

FECHA_CALCULO = datetime(2026, 11, 9, 2, 57, tzinfo=UTC)  # 08/11/2026 23:57 en Argentina
FECHA_ALERTA = datetime(2026, 11, 8, 20, 0, tzinfo=UTC)
CODIGO = "EST-932B2E48"

# (variable, valor guardado, contribución), en el orden del recálculo
FACTORES = [
    ("materias_aprobadas_s2", "1", "1.4639"),
    ("carrera", "9853", "1.0150"),
    ("nivel_educ_madre", "34", "0.7051"),
    ("materias_aprobadas_s1", "3", "0.3741"),
    ("edad_ingreso", "20", "-0.2701"),
]
TEXTOS_ESPERADOS = [
    "Materias aprobadas en el 2.º semestre: 1 de 6",
    "Carrera: Educación Básica",
    "Nivel educativo de la madre: sin dato",
    "Materias aprobadas en el 1.er semestre: 3 de 6",
    "Edad al ingresar: 20 años",
]
SENTIDOS_ESPERADOS = ["aumenta", "aumenta", "aumenta", "aumenta", "disminuye"]


def _estudiante(id_carga: int) -> Estudiante:
    return Estudiante(
        codigo_estudiante=CODIGO,
        id_carga=id_carga,
        estado_civil=1,
        nacionalidad=1,
        desplazado=True,
        genero=False,
        edad_ingreso=20,
        internacional=False,
        nivel_educ_madre=34,
        nivel_educ_padre=19,
        ocupacion_madre=9,
        ocupacion_padre=9,
        becario=False,
        tasa_desempleo=Decimal("10.8"),
        tasa_inflacion=Decimal("1.4"),
        variacion_pib=Decimal("1.74"),
        modalidad_ingreso=1,
        carrera=9853,
        turno_diurno=True,
        titulo_previo=1,
        nota_titulo_previo=Decimal("130.0"),
    )


def _rendimiento(id_carga: int, semestre: int, aprobadas: int) -> RendimientoSemestre:
    return RendimientoSemestre(
        codigo_estudiante=CODIGO,
        id_carga=id_carga,
        semestre=semestre,
        materias_acreditadas=0,
        materias_inscriptas=6,
        evaluaciones=8,
        materias_aprobadas=aprobadas,
        nota_promedio=Decimal("11.50"),
        materias_sin_evaluacion=0,
    )


def _prediccion(id_modelo: int, id_carga: int, probabilidad: str, nivel: str, fecha: datetime) -> Prediccion:
    return Prediccion(
        codigo_estudiante=CODIGO,
        id_modelo=id_modelo,
        id_carga=id_carga,
        fecha=fecha,
        probabilidad=Decimal(probabilidad),
        nivel=nivel,
        vigente=True,
    )


def sembrar(sesion, momento: str = "cierre_2s", factores=FACTORES) -> int:
    """Alerta con su predicción vigente y sus factores; devuelve el id de la alerta."""
    usuario = sesion.scalar(select(Usuario).where(Usuario.nombre_usuario == "sistemas01"))
    carga = Carga(
        id_usuario=usuario.id_usuario,
        fecha=FECHA_CALCULO,
        momento=momento,
        registros_validos=1,
        registros_rechazados=0,
    )
    modelo = Modelo(
        version="1.0",
        momento=momento,
        fecha=FECHA_CALCULO,
        umbral_alto=Decimal("0.9164"),
        umbral_medio=Decimal("0.5951"),
        habilitado=True,
    )
    sesion.add_all([carga, modelo])
    sesion.flush()
    sesion.add(_estudiante(carga.id_carga))
    sesion.flush()
    sesion.add_all([_rendimiento(carga.id_carga, 1, 3), _rendimiento(carga.id_carga, 2, 1)])
    prediccion = _prediccion(modelo.id_modelo, carga.id_carga, "0.9805", "alto", FECHA_CALCULO)
    sesion.add(prediccion)
    sesion.flush()
    for orden, (variable, valor, contribucion) in enumerate(factores, start=1):
        sesion.add(
            FactorExplicativo(
                id_prediccion=prediccion.id_prediccion,
                orden=orden,
                variable=variable,
                valor=valor,
                contribucion=Decimal(contribucion),
            )
        )
    alerta = Alerta(
        codigo_estudiante=CODIGO,
        id_prediccion=prediccion.id_prediccion,
        estado="pendiente",
        fecha_creacion=FECHA_ALERTA,
    )
    sesion.add(alerta)
    sesion.commit()
    return alerta.id_alerta


# --- Criterio 1: probabilidad, nivel y fecha del cálculo ----------------------------------


@pytest.mark.db
def test_ficha_tiene_probabilidad_nivel_y_fecha_del_calculo(sesion_db):
    ficha = consultar_ficha(sesion_db, sembrar(sesion_db))
    assert ficha["codigo_estudiante"] == CODIGO
    assert ficha["probabilidad"] == 0.9805
    assert ficha["nivel"] == "alto"
    assert ficha["fecha_calculo"] == FECHA_CALCULO
    assert (ficha["version_modelo"], ficha["momento"]) == ("1.0", "cierre_2s")
    assert (ficha["carrera"], ficha["turno"]) == ("Educación Básica", "diurno")
    assert (ficha["estado"], ficha["fecha_creacion"]) == ("pendiente", FECHA_ALERTA)


@pytest.mark.db
def test_ficha_sin_datos_identificatorios(sesion_db):
    ficha = consultar_ficha(sesion_db, sembrar(sesion_db))
    assert not {"legajo", "documento", "apellido_nombre", "nombre"} & set(ficha)


@pytest.mark.db
def test_ficha_muestra_la_prediccion_vigente(sesion_db):
    """Después de un recálculo la alerta apunta a la predicción nueva (P3): la ficha la muestra."""
    id_alerta = sembrar(sesion_db)
    alerta = sesion_db.get(Alerta, id_alerta)
    anterior = sesion_db.get(Prediccion, alerta.id_prediccion)
    anterior.vigente = False
    sesion_db.flush()
    nueva = _prediccion(
        anterior.id_modelo, anterior.id_carga, "0.4200", "bajo", datetime(2026, 11, 10, tzinfo=UTC)
    )
    sesion_db.add(nueva)
    sesion_db.flush()
    for orden, (variable, valor, contribucion) in enumerate(FACTORES, start=1):
        sesion_db.add(
            FactorExplicativo(
                id_prediccion=nueva.id_prediccion,
                orden=orden,
                variable=variable,
                valor=valor,
                contribucion=-Decimal(contribucion),
            )
        )
    alerta.id_prediccion = nueva.id_prediccion
    sesion_db.commit()

    ficha = consultar_ficha(sesion_db, id_alerta)
    assert (ficha["probabilidad"], ficha["nivel"], ficha["vigente"]) == (0.42, "bajo", True)
    assert ficha["fecha_calculo"] == datetime(2026, 11, 10, tzinfo=UTC)
    assert [f["sentido"] for f in ficha["factores"]] == ["disminuye"] * 4 + ["aumenta"]


@pytest.mark.db
def test_alerta_inexistente(sesion_db):
    assert consultar_ficha(sesion_db, 9999) is None


# --- Criterio 2: cinco factores, en orden de peso, con su sentido -------------------------


@pytest.mark.db
def test_cinco_factores_ordenados_por_peso_con_su_sentido(sesion_db):
    factores = consultar_ficha(sesion_db, sembrar(sesion_db))["factores"]
    assert len(factores) == 5
    assert [f["orden"] for f in factores] == [1, 2, 3, 4, 5]
    pesos = [abs(f["contribucion"]) for f in factores]
    assert pesos == sorted(pesos, reverse=True)
    assert [f["sentido"] for f in factores] == SENTIDOS_ESPERADOS
    assert [f["texto_sentido"] for f in factores] == ["Aumenta el riesgo"] * 4 + ["Disminuye el riesgo"]


# --- Criterio 3: nombres y valores comprensibles ------------------------------------------


@pytest.mark.db
def test_valores_guardados_se_muestran_comprensibles(sesion_db):
    factores = consultar_ficha(sesion_db, sembrar(sesion_db))["factores"]
    assert [f["texto"] for f in factores] == TEXTOS_ESPERADOS


@pytest.mark.db
def test_valor_guardado_con_decimales(sesion_db):
    """«13.21» (valor sin formatear de FACTOR_EXPLICATIVO) → «13,2 (escala de 0 a 20)»."""
    factores = [*FACTORES[:3], ("nota_promedio_s2", "13.21", "-0.3123"), FACTORES[4]]
    textos = [
        f["texto"] for f in consultar_ficha(sesion_db, sembrar(sesion_db, factores=factores))["factores"]
    ]
    assert textos[3] == "Nota promedio en el 2.º semestre: 13,2 (escala de 0 a 20)"
    assert not any("." in t.split(":")[1] for t in textos)  # coma decimal, sin códigos


# --- Variables que no corresponden al momento: mensaje controlado -------------------------


@pytest.mark.db
@pytest.mark.parametrize(
    ("momento", "factores", "detalle"),
    [
        # variable excluida (aranceles al día) en lugar del 3.er factor
        (
            "cierre_2s",
            [*FACTORES[:2], ("aranceles_al_dia", "1", "0.7051"), *FACTORES[3:]],
            "aranceles_al_dia",
        ),
        # variable del 2.º semestre en un cálculo de cierre del 1.er semestre (información futura)
        ("cierre_1s", FACTORES, "materias_aprobadas_s2"),
        # faltan factores
        ("cierre_2s", FACTORES[:4], "4 factores"),
    ],
)
def test_factor_que_no_corresponde_no_se_muestra_y_queda_en_el_registro(
    sesion_db, caplog, momento, factores, detalle
):
    with caplog.at_level(logging.ERROR, logger="alerta_temprana.servicio.ficha"):
        ficha = consultar_ficha(sesion_db, sembrar(sesion_db, momento=momento, factores=factores))
    assert ficha["factores"] is None  # no se muestra ningún factor
    assert ficha["probabilidad"] == 0.9805 and ficha["nivel"] == "alto"  # el resto de la ficha sí
    assert any(detalle in r.getMessage() and "alerta" in r.getMessage() for r in caplog.records)


def test_ninguna_variable_excluida_tiene_nombre_para_la_ficha():
    from alerta_temprana.modelo.etiquetas import NOMBRES

    assert not set(V.VARIABLES_EXCLUIDAS) & set(NOMBRES)
    textos = " ".join(NOMBRES.values()).lower()
    assert "arancel" not in textos and "al día" not in textos and "deudor" not in textos


# --- API interna ----------------------------------------------------------------------------


@pytest.fixture
def cliente(sesion_db):
    app.dependency_overrides[obtener_sesion] = lambda: sesion_db
    yield TestClient(app)  # sin «with»: no corre el ciclo de vida sobre la base de desarrollo
    app.dependency_overrides.clear()


@pytest.mark.db
@pytest.mark.datos
def test_fichas_de_los_seis_casos_coinciden_con_las_del_anexo(sesion_db, archivos_de_carga, planificador):  # noqa: F811
    """Con las cargas de inscripción y de cierre del 1.er semestre, la vigente de cada caso
    del cuestionario es la de cierre_1s v1.0: la ficha muestra la probabilidad, el nivel y
    los 5 factores (texto y sentido) de reportes/cuestionario/casos.csv. Los casos sin
    alerta (nivel bajo en las dos cargas) se comparan con la misma traducción de factores."""
    import pandas as pd

    from alerta_temprana.config import RAIZ, obtener_configuracion
    from alerta_temprana.datos.seudonimizacion import codigo_estudiante, legajo_sintetico
    from alerta_temprana.servicio import carga as servicio_carga
    from alerta_temprana.servicio.ficha import factores_comprensibles
    from alerta_temprana.servicio.modelos import registrar_modelos

    registrar_modelos(sesion_db, RAIZ / "modelos")
    for momento in (V.Momento.INSCRIPCION, V.Momento.CIERRE_1S):
        resultado = servicio_carga.registrar_carga(
            sesion_db, archivos_de_carga[momento].read_bytes(), momento, "sistemas01"
        )
        estado = planificador.esperar(resultado.id_carga, tiempo=300)
        assert estado.estado == "completado", estado.mensaje

    casos = pd.read_csv(RAIZ / "reportes" / "cuestionario" / "casos.csv")
    clave = obtener_configuracion().seudonimo_clave
    con_alerta = 0
    for caso in casos.itertuples():
        codigo = codigo_estudiante(legajo_sintetico(caso.indice_original), clave)
        textos_anexo = [getattr(caso, f"factor_{i}") for i in range(1, 6)]
        sentidos_anexo = [
            "aumenta" if getattr(caso, f"contribucion_{i}") > 0 else "disminuye" for i in range(1, 6)
        ]
        id_alerta = sesion_db.scalar(select(Alerta.id_alerta).where(Alerta.codigo_estudiante == codigo))
        if id_alerta is not None:
            con_alerta += 1
            ficha = consultar_ficha(sesion_db, id_alerta)
            assert (ficha["momento"], ficha["version_modelo"]) == ("cierre_1s", "1.0")
            assert (ficha["probabilidad"], ficha["nivel"]) == (caso.probabilidad, caso.nivel), (
                f"caso {caso.caso}"
            )
            factores = ficha["factores"]
        else:
            assert caso.nivel == "bajo", f"caso {caso.caso}"
            prediccion = sesion_db.scalars(
                select(Prediccion).where(Prediccion.codigo_estudiante == codigo, Prediccion.vigente)
            ).one()
            guardados = list(
                sesion_db.scalars(
                    select(FactorExplicativo).where(
                        FactorExplicativo.id_prediccion == prediccion.id_prediccion
                    )
                )
            )
            factores = factores_comprensibles(sesion_db, codigo, V.Momento.CIERRE_1S, guardados)
        assert [f["texto"] for f in factores] == textos_anexo, f"caso {caso.caso}"
        assert [f["sentido"] for f in factores] == sentidos_anexo, f"caso {caso.caso}"
    assert con_alerta >= 4  # los dos casos de nivel alto y los dos de nivel medio tienen alerta


@pytest.mark.db
def test_api_ficha(cliente, sesion_db):
    id_alerta = sembrar(sesion_db)
    respuesta = cliente.get(f"/api/alertas/{id_alerta}")
    assert respuesta.status_code == 200
    ficha = respuesta.json()
    assert (ficha["probabilidad"], ficha["nivel"]) == (0.9805, "alto")
    assert [f["texto"] for f in ficha["factores"]] == TEXTOS_ESPERADOS
    assert cliente.get("/api/alertas/9999").status_code == 404


@pytest.mark.db
def test_api_ficha_con_explicacion_no_valida_responde_sin_factores(cliente, sesion_db):
    factores = [*FACTORES[:4], ("deudor", "0", "-0.2701")]
    respuesta = cliente.get(f"/api/alertas/{sembrar(sesion_db, factores=factores)}")
    assert respuesta.status_code == 200
    assert respuesta.json()["factores"] is None
    assert "deudor" not in respuesta.text


# --- Pantalla (tarea 6.3) -------------------------------------------------------------------


def _ficha(**cambios) -> dict:
    """Ficha como la devuelve consultar_ficha (la de EST-932B2E48 en la base de la Demo)."""
    factores = [
        {
            "orden": i,
            "variable": variable,
            "texto": texto,
            "contribucion": float(contribucion),
            "sentido": sentido,
            "texto_sentido": "Aumenta el riesgo" if sentido == "aumenta" else "Disminuye el riesgo",
        }
        for i, ((variable, _, contribucion), texto, sentido) in enumerate(
            zip(FACTORES, TEXTOS_ESPERADOS, SENTIDOS_ESPERADOS, strict=True), start=1
        )
    ]
    base = {
        "id_alerta": 294,
        "codigo_estudiante": CODIGO,
        "carrera": "Educación Básica",
        "turno": "diurno",
        "probabilidad": 0.9805,
        "nivel": "alto",
        "fecha_calculo": FECHA_CALCULO,
        "version_modelo": "1.0",
        "momento": "cierre_2s",
        "vigente": True,
        "factores": factores,
        "estado": "pendiente",
        "fecha_creacion": FECHA_ALERTA,
        "cambios_estado": [],  # HU-007
    }
    return base | cambios


def _contenido(**cambios) -> list:
    from alerta_temprana.ui import ficha

    return ficha.contenido(_ficha(**cambios))


def _todos(raiz) -> list:
    from tests.test_hu005 import _componentes

    return list(_componentes(raiz))


def _con_clase(raiz, clase: str) -> list:
    return [c for c in _todos(raiz) if clase in (getattr(c, "className", None) or "").split()]


def test_pantalla_muestra_probabilidad_nivel_y_fecha_del_calculo():
    from tests.test_hu005 import _por_id, _texto

    componentes = _por_id(_contenido())
    assert _texto(componentes["ficha-probabilidad"]).endswith("0,98")
    nivel = _con_clase(componentes["ficha-nivel"], "nivel-alto")
    assert nivel and nivel[0].children == "Alto"  # etiqueta con color y texto
    calculo = _texto(componentes["ficha-calculo"])
    assert "08/11/2026 23:57" in calculo and "modelo v1.0 (Cierre del 2.º semestre)" in calculo
    assert "Educación Básica · Diurno" in _texto(componentes["ficha-carrera"])


def test_pantalla_lista_los_cinco_factores_con_su_sentido_y_barra_proporcional():
    from tests.test_hu005 import _por_id, _texto

    seccion = _por_id(_contenido())["ficha-factores"]
    assert "Factores que más pesan en esta estimación" in _texto(seccion)
    filas = _con_clase(seccion, "factor")
    esperados = [
        f"{texto} {'Aumenta el riesgo' if sentido == 'aumenta' else 'Disminuye el riesgo'}"
        for texto, sentido in zip(TEXTOS_ESPERADOS, SENTIDOS_ESPERADOS, strict=True)
    ]
    assert [_texto(f) for f in filas] == esperados
    barras = _con_clase(seccion, "factor-barra")
    assert [b.style["width"] for b in barras] == ["100%", "69%", "48%", "26%", "18%"]
    sentidos = _con_clase(seccion, "factor-sentido")
    assert [s.style["color"] for s in sentidos] == ["#B91C1C"] * 4 + ["#1D4ED8"]  # rojo y azul


def test_pantalla_muestra_el_aviso_completo_debajo_de_los_factores():
    from alerta_temprana.modelo.etiquetas import AVISO_FICHA
    from tests.test_hu005 import _por_id, _texto

    assert AVISO_FICHA == (
        "La alerta es una estimación para apoyar la decisión y no reemplaza el criterio del tutor. "
        "Los factores muestran cuánto pesa cada variable en la estimación, no las causas del abandono."
    )
    seccion = _por_id(_contenido())["ficha-factores"]
    assert seccion.children[-1].id == "aviso-ficha"  # al final de la sección de factores
    assert _texto(seccion.children[-1]) == AVISO_FICHA


def test_pantalla_sin_terminos_prohibidos_ni_variables_excluidas():
    from tests.test_hu005 import _texto, html_div

    texto = _texto(html_div(_contenido())).lower()
    prohibidos = (
        "influy",
        "factores que explican",
        "el porqué",
        "arancel",
        "al día",
        "deudor",
        "riesgo crítico",
    )
    for prohibido in prohibidos:
        assert prohibido not in texto
    # «causas» solo dentro del aviso, que dice que los factores NO son causas
    assert texto.count("causas") == 1 and "no las causas del abandono" in texto


def test_pantalla_sin_explicacion_muestra_el_mensaje_controlado():
    from alerta_temprana.modelo.etiquetas import AVISO_FICHA
    from tests.test_hu005 import _por_id, _texto, html_div

    contenido = _contenido(factores=None)
    mensaje = _por_id(contenido)["ficha-sin-explicacion"]
    assert _texto(mensaje) == "No se puede mostrar la explicación de esta alerta."
    texto = _texto(html_div(contenido))
    assert "Aumenta el riesgo" not in texto and "Disminuye el riesgo" not in texto
    assert AVISO_FICHA in texto and "0,98" in texto  # el aviso y las tarjetas siguen


def test_pantalla_tiene_enlace_al_listado_y_seguimiento():
    from tests.test_hu005 import _por_id, _texto

    componentes = _por_id(_contenido())
    assert componentes["volver-listado"].href == "/listado"
    seguimiento = _texto(componentes["ficha-seguimiento"])
    assert "Alerta creada el 08/11/2026" in seguimiento
    assert componentes["ficha-estado"].value == "pendiente"  # desplegable desde HU-007


def test_carrera_nocturna_no_repite_el_turno():
    from alerta_temprana.ui.ficha import texto_carrera_turno

    assert texto_carrera_turno("Gestión (nocturno)", "nocturno") == "Gestión (nocturno)"
    assert texto_carrera_turno("Enfermería", "nocturno") == "Enfermería · Nocturno"


def test_pantalla_alerta_inexistente_o_base_caida(monkeypatch):
    from sqlalchemy.exc import OperationalError

    from alerta_temprana.ui import ficha
    from tests.test_hu005 import _texto, html_div

    monkeypatch.setattr(ficha, "_leer_ficha", lambda _id: None)
    titulo, contenido = ficha.pantalla(9999)
    assert titulo == "Ficha del estudiante" and ficha.SIN_ALERTA in _texto(html_div(contenido))

    def caida(_id):
        raise OperationalError("SELECT", {}, Exception("sin conexión"))

    monkeypatch.setattr(ficha, "_leer_ficha", caida)
    _, contenido = ficha.pantalla(1)
    assert ficha.SIN_BASE in _texto(html_div(contenido))


def test_el_listado_tiene_ver_ficha_en_cada_fila():
    from alerta_temprana.ui import listado
    from tests.test_hu005 import _alerta

    fila = listado.filas_tabla([_alerta(id_alerta=294)])[0]
    enlaces = [c for c in _todos(fila) if type(c).__name__ == "Link"]
    assert [(e.children, e.href) for e in enlaces] == [("Ver ficha", "/ficha/294")]


# --- Navegación (decisión del 09/11): la ficha es pantalla de Coordinación y Tutor/a ---------


@pytest.fixture
def ficha_sin_base(monkeypatch):
    from alerta_temprana.ui import ficha

    monkeypatch.setattr(ficha, "_leer_ficha", lambda id_alerta: _ficha(id_alerta=id_alerta))


@pytest.mark.parametrize(
    ("usuario", "ruta", "esperada"),
    [
        ("coordinacion01", "/ficha/294", "/ficha/294"),
        ("tutor01", "/ficha/294", "/ficha/294"),
        ("sistemas01", "/ficha/294", "/"),
        ("secretaria01", "/ficha/294", "/metricas"),
        ("coordinacion01", "/ficha/abc", "/listado"),
        ("coordinacion01", "/ficha/", "/listado"),
    ],
)
def test_ruta_para_la_ficha(usuario, ruta, esperada):
    from alerta_temprana.ui.diseno import ruta_para

    assert ruta_para(usuario, ruta) == esperada


def test_abrir_la_ficha_desde_el_listado(ficha_sin_base):
    from dash import no_update

    from tests.test_hu005 import _enlaces, _navegar, _por_id

    ruta, titulo, contenido, menu = _navegar("/ficha/294", "coordinacion01", "url.pathname")
    assert ruta is no_update  # la dirección ya es la de la ficha
    assert titulo == "Ficha del estudiante EST-932B2E48"
    assert "ficha-factores" in _por_id(contenido)
    assert _enlaces(menu) == ["/listado"]
    assert menu[0].children.style["fontWeight"] == 600  # resalta «Listado de alertas»


def test_de_coordinacion_a_tutor_la_ficha_no_cambia(ficha_sin_base):
    from dash import no_update

    from tests.test_hu005 import _navegar

    ruta, titulo, contenido, _ = _navegar("/ficha/294", "tutor01", "usuario-prueba.value")
    assert ruta is no_update and titulo is no_update and contenido is no_update


@pytest.mark.parametrize(
    ("usuario", "ruta_esperada", "titulo_esperado", "id_esperado"),
    [
        ("sistemas01", "/", "Carga de datos", "formulario-carga"),
        ("secretaria01", "/metricas", "Panel de métricas", None),
    ],
)
def test_con_la_ficha_abierta_otro_rol_pasa_a_su_pantalla_inicial(
    usuario, ruta_esperada, titulo_esperado, id_esperado
):
    from tests.test_hu005 import _enlaces, _navegar, _por_id

    ruta, titulo, contenido, menu = _navegar("/ficha/294", usuario, "usuario-prueba.value")
    assert (ruta, titulo) == (ruta_esperada, titulo_esperado)
    ids = _por_id(contenido)
    assert "ficha-factores" not in ids
    if id_esperado:
        assert id_esperado in ids
    assert _enlaces(menu) == [ruta_esperada]
