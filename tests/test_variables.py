"""Las listas de variables coinciden con el documento (Recolección de Datos y Tabla 32)."""

import pytest

from alerta_temprana.datos import variables as V


def test_cantidad_de_variables_por_momento():
    assert len(V.VARIABLES_POR_MOMENTO[V.Momento.INSCRIPCION]) == 19
    assert len(V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_1S]) == 25
    assert len(V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_2S]) == 31


def test_ningun_momento_usa_variables_excluidas_ni_el_objetivo():
    for lista in V.VARIABLES_POR_MOMENTO.values():
        assert not set(lista) & set(V.VARIABLES_EXCLUIDAS)
        assert V.OBJETIVO not in lista


def test_inscripcion_no_usa_rendimiento_de_semestres():
    inscripcion = V.VARIABLES_POR_MOMENTO[V.Momento.INSCRIPCION]
    assert not [v for v in inscripcion if v.endswith(("_s1", "_s2"))]
    assert not [v for v in V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_1S] if v.endswith("_s2")]


def _encabezado_estilo_uci() -> list[str]:
    """Encabezado sintético con las rarezas del archivo de UCI (tabulador, mayúsculas, errata)."""
    columnas = [orig.title() for orig in V.MAPA_ORIGINAL_A_PLATAFORMA]
    return [c + "\t" if c.lower().startswith("daytime") else c for c in columnas]


def test_renombrar_tolera_tabuladores_y_mayusculas():
    renombre = V.renombrar_columnas(_encabezado_estilo_uci())
    assert len(renombre) == V.COLUMNAS_ORIGINALES_ESPERADAS
    assert "turno_diurno" in renombre.values()
    assert "nacionalidad" in renombre.values()


def test_renombrar_falla_si_falta_una_columna():
    encabezado = _encabezado_estilo_uci()[:-1]
    with pytest.raises(ValueError, match="faltantes"):
        V.renombrar_columnas(encabezado)
