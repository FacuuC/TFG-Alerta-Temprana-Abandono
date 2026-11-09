"""Panel de Dash: pantallas de carga (HU-001) y listado de alertas (HU-005).

El layout común tiene el menú lateral (según el usuario de prueba), la barra superior
con el selector y la última actualización, y el estado del último recálculo. El contenido
cambia con la dirección: `/` es la carga, `/listado` el listado y `/metricas` el aviso de
la Secretaría Académica. La ficha se suma en HU-006.

Regla de navegación (decisión del 09/11): lo que se muestra siempre es una pantalla del
menú del usuario elegido. Al cambiar de usuario o al entrar a una dirección escrita a
mano que no está en su menú, se pasa a la pantalla inicial de su rol, sin recargar la
página. Si la pantalla actual está en el menú del nuevo usuario, no cambia (ni se vuelve
a armar, así se conservan los filtros del listado). Es navegación, no control de acceso
(decisión P5): la API no cambia.
"""

from __future__ import annotations

from dataclasses import dataclass

import dash
from dash import Input, Output, callback, ctx, dcc, html, no_update

from alerta_temprana.ui import (
    actualizacion,  # noqa: F401  (última actualización en la barra superior)
    carga,  # registra los callbacks de la pantalla de carga
    listado,  # registra los callbacks del listado
)
from alerta_temprana.ui.diseno import (
    AVISO_SIN_PANTALLAS,
    ESTILO_TARJETA,
    RUTA_CARGA,
    RUTA_LISTADO,
    RUTA_METRICAS,
    TITULOS,
    opciones_menu,
    pagina,
    ruta_para,
)


def contenido_metricas() -> list:
    """Pantalla de la Secretaría Académica: solo el aviso, sin listado ni formulario de carga."""
    return [html.Div(html.P(AVISO_SIN_PANTALLAS, style={"margin": 0}), style=ESTILO_TARJETA)]


_CONTENIDO = {RUTA_CARGA: carga.contenido, RUTA_LISTADO: listado.contenido, RUTA_METRICAS: contenido_metricas}


def pantalla_para(ruta: str) -> tuple[str, list]:
    """(título, contenido) de una pantalla del menú."""
    return TITULOS[ruta], _CONTENIDO[ruta]()


@dataclass
class Navegacion:
    """Resultado de aplicar la regla. `None` en ruta, título o contenido = no cambia."""

    ruta: str | None  # nueva dirección, solo si hay que cambiarla
    titulo: str | None
    contenido: list | None
    menu: list


def navegacion(usuario: str | None, ruta: str | None, cambio_de_usuario: bool) -> Navegacion:
    """Aplica la regla de navegación (función pura)."""
    destino = ruta_para(usuario, ruta)
    menu = opciones_menu(usuario, destino)
    if cambio_de_usuario and destino == ruta:
        return Navegacion(None, None, None, menu)  # la pantalla está en su menú: no cambia
    titulo, contenido = pantalla_para(destino)
    return Navegacion(destino if destino != ruta else None, titulo, contenido, menu)


def _o_sin_cambio(valor):
    return no_update if valor is None else valor


@callback(
    Output("url", "pathname"),
    Output("titulo-pagina", "children"),
    Output("contenido-pagina", "children"),
    Output("menu-opciones", "children"),
    Input("url", "pathname"),
    Input("usuario-prueba", "value"),
)
def navegar(ruta: str | None, usuario: str):
    resultado = navegacion(usuario, ruta, cambio_de_usuario=ctx.triggered_id == "usuario-prueba")
    return (
        _o_sin_cambio(resultado.ruta),
        _o_sin_cambio(resultado.titulo),
        _o_sin_cambio(resultado.contenido),
        resultado.menu,
    )


def crear_panel() -> dash.Dash:
    # suppress_callback_exceptions: cada pantalla aparece según la dirección
    panel = dash.Dash(
        __name__, requests_pathname_prefix="/", title="Alerta temprana", suppress_callback_exceptions=True
    )
    panel.layout = html.Div(
        [
            # callback-nav: cambiar la dirección desde un callback no recarga la página
            dcc.Location(id="url", refresh="callback-nav"),
            dcc.Store(id="estado-recalculo"),  # lo escribe la carga; lo leen la barra y el listado
            pagina("", [html.Div(id="contenido-pagina")]),
        ]
    )
    return panel
