"""Panel de Dash. En HU-001 tiene la pantalla de carga; las demás se suman en HU-005 y HU-006."""

from __future__ import annotations

import dash

from alerta_temprana.ui import (
    actualizacion,  # noqa: F401  (última actualización en la barra superior)
    carga,  # registra los callbacks de la pantalla de carga
)
from alerta_temprana.ui.diseno import pagina


def crear_panel() -> dash.Dash:
    # suppress_callback_exceptions: el botón del informe de errores aparece con el resultado
    panel = dash.Dash(
        __name__, requests_pathname_prefix="/", title="Alerta temprana", suppress_callback_exceptions=True
    )
    panel.layout = pagina("Carga de datos", carga.contenido())
    return panel
