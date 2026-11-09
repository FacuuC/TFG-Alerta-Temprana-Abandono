"""HU-005: listado de alertas tempranas (tareas 5.1 y 5.2).

Las pruebas con base siembran alertas sintéticas directamente (estudiante, predicción
vigente y alerta), sin modelos ni dataset, para elegir nivel, probabilidad, carrera,
turno y estado de cada una.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from alerta_temprana.app import app
from alerta_temprana.db.sesion import obtener_sesion
from alerta_temprana.db.tablas import Alerta, Carga, Estudiante, Modelo, Prediccion, Usuario
from alerta_temprana.servicio.alertas import (
    COLUMNAS_LISTADO,
    FiltrosAlertas,
    consultar_alertas,
    resumir_alertas,
)

FECHA = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)
CODIGO = re.compile(r"^EST-[0-9A-F]{8}$")
IDENTIFICATORIAS = ("legajo", "documento", "apellido_nombre", "nombre")

# (código, carrera, turno_diurno, nivel, probabilidad, estado), insertadas desordenadas
ALERTAS = [
    ("EST-0000000A", 9500, True, "medio", "0.6100", "pendiente"),
    ("EST-0000000B", 9119, False, "bajo", "0.3200", "contactado"),
    ("EST-0000000C", 9500, True, "alto", "0.9100", "pendiente"),
    ("EST-0000000D", 9147, True, "alto", "0.9700", "en_acompanamiento"),
    ("EST-0000000E", 9119, True, "bajo", "0.4400", "pendiente"),
    ("EST-0000000F", 9991, False, "medio", "0.8100", "contactado"),
    ("EST-0000001A", 9500, False, "alto", "0.9400", "pendiente"),
]
ORDEN_ESPERADO = [
    "EST-0000000D",  # alto 0,97
    "EST-0000001A",  # alto 0,94
    "EST-0000000C",  # alto 0,91
    "EST-0000000F",  # medio 0,81
    "EST-0000000A",  # medio 0,61
    "EST-0000000E",  # bajo 0,44
    "EST-0000000B",  # bajo 0,32
]


def _estudiante(codigo: str, id_carga: int, carrera: int, diurno: bool) -> Estudiante:
    return Estudiante(
        codigo_estudiante=codigo,
        id_carga=id_carga,
        estado_civil=1,
        nacionalidad=1,
        desplazado=False,
        genero=False,
        edad_ingreso=19,
        internacional=False,
        nivel_educ_madre=1,
        nivel_educ_padre=1,
        ocupacion_madre=1,
        ocupacion_padre=1,
        becario=False,
        tasa_desempleo=Decimal("10.8"),
        tasa_inflacion=Decimal("1.4"),
        variacion_pib=Decimal("1.74"),
        modalidad_ingreso=1,
        carrera=carrera,
        turno_diurno=diurno,
        titulo_previo=1,
        nota_titulo_previo=Decimal("130.0"),
    )


def sembrar(sesion, alertas=ALERTAS) -> None:
    usuario = sesion.scalar(select(Usuario).where(Usuario.nombre_usuario == "sistemas01"))
    carga = Carga(
        id_usuario=usuario.id_usuario,
        fecha=FECHA,
        momento="cierre_1s",
        registros_validos=len(alertas),
        registros_rechazados=0,
    )
    modelo = Modelo(
        version="1.0",
        momento="cierre_1s",
        fecha=FECHA,
        umbral_alto=Decimal("0.8936"),
        umbral_medio=Decimal("0.5301"),
        habilitado=True,
    )
    sesion.add_all([carga, modelo])
    sesion.flush()
    for codigo, carrera, diurno, nivel, probabilidad, estado in alertas:
        sesion.add(_estudiante(codigo, carga.id_carga, carrera, diurno))
        sesion.flush()
        prediccion = Prediccion(
            codigo_estudiante=codigo,
            id_modelo=modelo.id_modelo,
            id_carga=carga.id_carga,
            fecha=FECHA,
            probabilidad=Decimal(probabilidad),
            nivel=nivel,
            vigente=True,
        )
        sesion.add(prediccion)
        sesion.flush()
        sesion.add(
            Alerta(
                codigo_estudiante=codigo,
                id_prediccion=prediccion.id_prediccion,
                estado=estado,
                fecha_creacion=FECHA,
            )
        )
    sesion.commit()


def _codigos(alertas: list[dict]) -> list[str]:
    return [a["codigo_estudiante"] for a in alertas]


# --- Criterio 1: orden y listado sin filtro por defecto ---------------------------------


@pytest.mark.db
def test_orden_por_nivel_y_probabilidad(sesion_db):
    sembrar(sesion_db)
    assert _codigos(consultar_alertas(sesion_db)) == ORDEN_ESPERADO


@pytest.mark.db
def test_alerta_de_nivel_bajo_aparece_por_defecto(sesion_db):
    """Observación 7 del tutor (07/11): sin filtro, incluidas las que bajaron a nivel bajo."""
    sembrar(sesion_db)
    alertas = consultar_alertas(sesion_db, FiltrosAlertas())
    assert len(alertas) == len(ALERTAS)
    assert {"EST-0000000B", "EST-0000000E"} <= set(_codigos(alertas))
    assert [a["nivel"] for a in alertas][-2:] == ["bajo", "bajo"]


# --- Criterio 2: columnas sin datos identificatorios ------------------------------------


@pytest.mark.db
def test_filas_tienen_solo_las_columnas_del_listado(sesion_db):
    sembrar(sesion_db)
    alertas = consultar_alertas(sesion_db)
    for alerta in alertas:
        assert tuple(alerta) == COLUMNAS_LISTADO
        assert CODIGO.match(alerta["codigo_estudiante"])
        assert not any(c in alerta for c in IDENTIFICATORIAS)
    primera = alertas[0]
    assert primera["carrera"] == "Gestión"  # nombre legible, no el código 9147
    assert primera["turno"] == "diurno"
    assert primera["probabilidad"] == pytest.approx(0.97)
    assert primera["estado"] == "en_acompanamiento"


# --- Criterio 3: filtros -----------------------------------------------------------------


@pytest.mark.db
@pytest.mark.parametrize(
    ("filtros", "esperados"),
    [
        (FiltrosAlertas(carreras=[9500]), ["EST-0000001A", "EST-0000000C", "EST-0000000A"]),
        (FiltrosAlertas(carreras=[9119, 9991]), ["EST-0000000F", "EST-0000000E", "EST-0000000B"]),
        (FiltrosAlertas(turno="nocturno"), ["EST-0000001A", "EST-0000000F", "EST-0000000B"]),
        (
            FiltrosAlertas(turno="diurno"),
            ["EST-0000000D", "EST-0000000C", "EST-0000000A", "EST-0000000E"],
        ),
        (FiltrosAlertas(niveles=["bajo"]), ["EST-0000000E", "EST-0000000B"]),
        (
            FiltrosAlertas(niveles=["alto", "medio"]),
            ["EST-0000000D", "EST-0000001A", "EST-0000000C", "EST-0000000F", "EST-0000000A"],
        ),
        (FiltrosAlertas(estados=["contactado"]), ["EST-0000000F", "EST-0000000B"]),
        (FiltrosAlertas(estados=["en_acompanamiento"]), ["EST-0000000D"]),
    ],
)
def test_cada_filtro_solo(sesion_db, filtros, esperados):
    sembrar(sesion_db)
    assert _codigos(consultar_alertas(sesion_db, filtros)) == esperados


@pytest.mark.db
def test_filtros_combinados(sesion_db):
    sembrar(sesion_db)
    filtros = FiltrosAlertas(carreras=[9500], turno="diurno", niveles=["alto", "medio"], estados=["pendiente"])
    assert _codigos(consultar_alertas(sesion_db, filtros)) == ["EST-0000000C", "EST-0000000A"]
    sin_resultados = FiltrosAlertas(carreras=[9147], niveles=["bajo"])
    assert consultar_alertas(sesion_db, sin_resultados) == []


@pytest.mark.parametrize(
    "argumentos",
    [{"niveles": ["critico"]}, {"estados": ["matriculado"]}, {"turno": "mañana"}, {"carreras": [1]}],
)
def test_filtro_invalido(argumentos):
    with pytest.raises(ValueError, match="no válido"):
        FiltrosAlertas(**argumentos)


# --- Contadores sobre el mismo conjunto que el listado -----------------------------------


def test_resumir_alertas():
    alertas = [
        {"nivel": "alto", "estado": "pendiente"},
        {"nivel": "alto", "estado": "contactado"},
        {"nivel": "medio", "estado": "pendiente"},
        {"nivel": "bajo", "estado": "pendiente"},
    ]
    assert resumir_alertas(alertas) == {"alto": 2, "medio": 1, "pendientes": 3, "total": 4}
    assert resumir_alertas([]) == {"alto": 0, "medio": 0, "pendientes": 0, "total": 0}


@pytest.mark.db
def test_resumen_respeta_el_filtro(sesion_db):
    sembrar(sesion_db)
    assert resumir_alertas(consultar_alertas(sesion_db)) == {"alto": 3, "medio": 2, "pendientes": 4, "total": 7}
    solo_bajo = resumir_alertas(consultar_alertas(sesion_db, FiltrosAlertas(niveles=["bajo"])))
    assert solo_bajo == {"alto": 0, "medio": 0, "pendientes": 1, "total": 2}
    contactadas = resumir_alertas(consultar_alertas(sesion_db, FiltrosAlertas(estados=["contactado"])))
    assert contactadas == {"alto": 0, "medio": 1, "pendientes": 0, "total": 2}


# --- API interna (decisión P4) ------------------------------------------------------------


@pytest.fixture
def cliente(sesion_db):
    app.dependency_overrides[obtener_sesion] = lambda: sesion_db
    yield TestClient(app)  # sin «with»: no corre el ciclo de vida sobre la base de desarrollo
    app.dependency_overrides.clear()


@pytest.mark.db
def test_api_alertas_con_filtros(cliente, sesion_db):
    sembrar(sesion_db)
    todas = cliente.get("/api/alertas").json()
    assert _codigos(todas["alertas"]) == ORDEN_ESPERADO
    assert todas["resumen"]["total"] == 7
    filtradas = cliente.get(
        "/api/alertas", params={"carrera": [9500, 9119], "nivel": ["alto", "bajo"], "estado": "pendiente"}
    ).json()
    assert _codigos(filtradas["alertas"]) == ["EST-0000001A", "EST-0000000C", "EST-0000000E"]
    assert filtradas["resumen"] == {"alto": 2, "medio": 0, "pendientes": 3, "total": 3}


@pytest.mark.parametrize("params", [{"nivel": "critico"}, {"turno": "mañana"}, {"estado": "matriculado"}])
def test_api_filtro_invalido_responde_422(params):
    assert TestClient(app).get("/api/alertas", params=params).status_code == 422


# --- Pantalla (tarea 5.2) -----------------------------------------------------------------


def _componentes(raiz):
    """Recorre un árbol de componentes de Dash."""
    yield raiz
    hijos = getattr(raiz, "children", None)
    if hijos is None or isinstance(hijos, str | int | float):
        return
    for hijo in hijos if isinstance(hijos, list | tuple) else [hijos]:
        if hasattr(hijo, "to_plotly_json"):
            yield from _componentes(hijo)


def _por_id(contenido: list) -> dict:
    return {c.id: c for raiz in contenido for c in _componentes(raiz) if getattr(c, "id", None)}


def _texto(componente) -> str:
    partes = []
    for c in _componentes(componente):
        hijos = getattr(c, "children", None)
        if isinstance(hijos, str | int | float):
            partes.append(str(hijos))
    return " ".join(partes)


def _alerta(**cambios) -> dict:
    base = {
        "id_alerta": 1,
        "codigo_estudiante": "EST-7F3A21C4",
        "carrera": "Enfermería",
        "turno": "diurno",
        "nivel": "alto",
        "probabilidad": 0.9134,
        "estado": "pendiente",
    }
    return base | cambios


def test_listado_abre_sin_filtros():
    from alerta_temprana.ui import listado

    componentes = _por_id(listado.contenido())
    for id_filtro in listado.FILTROS:
        assert componentes[id_filtro].value is None
    assert listado.armar_filtros(None, None, None, None) == FiltrosAlertas()


def test_nivel_se_muestra_con_color_y_texto():
    from alerta_temprana.ui.diseno import etiqueta_nivel

    fondos = set()
    for nivel, texto in {"alto": "Alto", "medio": "Medio", "bajo": "Bajo"}.items():
        etiqueta = etiqueta_nivel(nivel)
        assert etiqueta.children == texto
        fondos.add(etiqueta.style["background"])
    assert len(fondos) == 3


def test_probabilidad_con_coma_decimal_y_textos_de_la_fila():
    from alerta_temprana.ui import listado

    fila = listado.filas_tabla([_alerta(estado="en_acompanamiento", turno="nocturno")])[0]
    texto = _texto(fila)
    assert "0,91" in texto and "0.91" not in texto
    for esperado in ("EST-7F3A21C4", "Enfermería", "Nocturno", "Alto", "En acompañamiento"):
        assert esperado in texto


def test_tabla_no_muestra_datos_identificatorios():
    from alerta_temprana.ui import listado

    assert list(listado.COLUMNAS_TABLA) == ["codigo_estudiante", "carrera", "turno", "nivel", "probabilidad", "estado"]
    assert set(listado.COLUMNAS_TABLA) <= set(COLUMNAS_LISTADO)
    encabezados = " ".join(listado.COLUMNAS_TABLA.values()).lower()
    assert not any(c in encabezados for c in ("legajo", "documento", "nombre"))


def test_tabla_con_desplazamiento_y_encabezado_fijo():
    from alerta_temprana.ui import listado

    componentes = _por_id(listado.contenido())
    contenedor = componentes["contenedor-tabla-alertas"]
    assert contenedor.style["overflowY"] == "auto" and contenedor.style["maxHeight"]
    encabezados = [c for c in _componentes(contenedor) if type(c).__name__ == "Th"]
    assert len(encabezados) == len(listado.COLUMNAS_TABLA)
    assert all(th.style["position"] == "sticky" and th.style["top"] == 0 for th in encabezados)


def test_tarjetas_y_mensajes_sin_alertas():
    from alerta_temprana.ui import listado

    texto = _texto(html_div(listado.tarjetas({"alto": 137, "medio": 131, "pendientes": 1200, "total": 529})))
    assert "Nivel alto" in texto and "137" in texto
    assert "Nivel medio" in texto and "131" in texto
    assert "Pendientes de contacto" in texto and "1.200" in texto
    assert listado.texto_cantidad(529) == "529 alertas" and listado.texto_cantidad(1) == "1 alerta"
    assert listado.SIN_ALERTAS in _texto(listado.filas_tabla([])[0])
    assert listado.SIN_COINCIDENCIAS in _texto(listado.filas_tabla([], con_filtros=True)[0])


def html_div(hijos):
    from dash import html

    return html.Div(hijos)


def _enlaces(menu: list) -> list[str]:
    return [c.href for c in _componentes(html_div(menu)) if hasattr(c, "href")]


def test_ruta_listado_y_menu_por_usuario():
    from alerta_temprana.ui.diseno import opciones_menu
    from alerta_temprana.ui.panel import pantalla_para

    titulo, contenido = pantalla_para("/listado")
    assert titulo == "Listado de alertas tempranas"
    assert "tabla-alertas" in _por_id(contenido)
    assert pantalla_para("/")[0] == "Carga de datos"

    assert _enlaces(opciones_menu("sistemas01")) == ["/"]
    assert _enlaces(opciones_menu("coordinacion01")) == ["/listado"]
    assert _enlaces(opciones_menu("tutor01")) == ["/listado"]
    assert _enlaces(opciones_menu("secretaria01")) == ["/metricas"]


def test_pantalla_de_secretaria_solo_tiene_el_aviso():
    from alerta_temprana.ui.diseno import AVISO_SIN_PANTALLAS
    from alerta_temprana.ui.panel import pantalla_para

    titulo, contenido = pantalla_para("/metricas")
    assert titulo == "Panel de métricas"
    assert "HU-008" in AVISO_SIN_PANTALLAS
    assert AVISO_SIN_PANTALLAS in _texto(html_div(contenido))
    ids = _por_id(contenido)
    assert "tabla-alertas" not in ids and "formulario-carga" not in ids


# --- Regla de navegación (decisión del 09/11): siempre una pantalla del menú ------------


@pytest.mark.parametrize(
    ("usuario", "ruta", "esperada"),
    [
        ("sistemas01", "/listado", "/"),  # Coordinación → Área de Sistemas, o escrita a mano
        ("secretaria01", "/listado", "/metricas"),  # Coordinación → Secretaría Académica
        ("tutor01", "/listado", "/listado"),  # Coordinación → Tutor/a: no cambia
        ("coordinacion01", "/", "/listado"),
        ("tutor01", "/metricas", "/listado"),
        ("secretaria01", "/", "/metricas"),
        ("sistemas01", "/", "/"),
        ("coordinacion01", "/otra", "/listado"),  # dirección inexistente
        ("coordinacion01", None, "/listado"),
        ("desconocido", "/listado", "/"),  # usuario desconocido: el de por defecto
    ],
)
def test_ruta_para(usuario, ruta, esperada):
    from alerta_temprana.ui.diseno import ruta_para

    assert ruta_para(usuario, ruta) == esperada


def _navegar(ruta: str | None, usuario: str, disparador: str):
    """Corre el callback `navegar` como lo haría Dash, con el disparador indicado."""
    from contextvars import copy_context

    from dash._callback_context import context_value
    from dash._utils import AttributeDict

    from alerta_temprana.ui.panel import navegar

    def correr():
        context_value.set(AttributeDict(triggered_inputs=[{"prop_id": disparador, "value": None}]))
        return navegar(ruta, usuario)

    return copy_context().run(correr)


@pytest.mark.parametrize(
    ("usuario", "ruta_esperada", "titulo"),
    [
        ("sistemas01", "/", "Carga de datos"),  # Coordinación → Área de Sistemas
        ("secretaria01", "/metricas", "Panel de métricas"),  # Coordinación → Secretaría
    ],
)
def test_cambiar_de_usuario_pasa_a_la_pantalla_inicial_del_rol(usuario, ruta_esperada, titulo):
    ruta, titulo_pagina, contenido, menu = _navegar("/listado", usuario, "usuario-prueba.value")
    assert ruta == ruta_esperada
    assert titulo_pagina == titulo
    assert "tabla-alertas" not in _por_id(contenido)
    assert _enlaces(menu) == [ruta_esperada]


def test_de_coordinacion_a_tutor_el_listado_no_cambia():
    from dash import no_update

    ruta, titulo, contenido, menu = _navegar("/listado", "tutor01", "usuario-prueba.value")
    assert ruta is no_update and titulo is no_update and contenido is no_update  # conserva los filtros
    assert _enlaces(menu) == ["/listado"]


def test_area_de_sistemas_con_listado_escrito_a_mano_pasa_a_la_carga():
    ruta, titulo, contenido, menu = _navegar("/listado", "sistemas01", "url.pathname")
    assert ruta == "/"
    assert titulo == "Carga de datos"
    ids = _por_id(contenido)
    assert "formulario-carga" in ids and "tabla-alertas" not in ids
    assert _enlaces(menu) == ["/"]


def test_al_abrir_una_pantalla_del_menu_se_muestra_sin_cambiar_la_direccion():
    from dash import no_update

    ruta, titulo, contenido, _ = _navegar("/listado", "coordinacion01", "url.pathname")
    assert ruta is no_update
    assert titulo == "Listado de alertas tempranas" and "tabla-alertas" in _por_id(contenido)


def test_la_barra_superior_tiene_el_selector_de_usuario_de_prueba():
    from alerta_temprana.ui.diseno import barra_superior

    componentes = _por_id([barra_superior("Listado de alertas tempranas")])
    selector = componentes["usuario-prueba"]
    assert {o["value"] for o in selector.options} == {"sistemas01", "coordinacion01", "tutor01", "secretaria01"}
    assert "ultima-actualizacion" in componentes
