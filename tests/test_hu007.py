"""HU-007: registro del estado de seguimiento (tareas 7.1 y 7.2; criterios 1 a 6).

- Tarea 7.1: `cambiar_estado` (servicio/seguimiento.py), la ruta de la API y la
  conservación del estado al recalcular. Los criterios 4 a 6 los cubre la regla P3 de
  servicio/alertas.py; acá se prueban con estados cambiados **con la función** (no con un
  UPDATE directo), empezando desde la inscripción y con las cargas siguientes, con los
  archivos de tests/fixtures/ y con los tres archivos de 885 estudiantes de data/cargas/.
- Tarea 7.2: control de estado en el listado y en la ficha.

Las pruebas con data/cargas/ solo cuentan niveles y estados: no leen etiquetas.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from alerta_temprana.app import app
from alerta_temprana.datos.variables import Momento as M
from alerta_temprana.db.sesion import obtener_sesion
from alerta_temprana.db.tablas import Alerta, CambioEstado, Prediccion, Rol, Usuario
from alerta_temprana.servicio import carga as servicio_carga
from alerta_temprana.servicio.alertas import FiltrosAlertas, consultar_alertas, resumir_alertas
from alerta_temprana.servicio.ficha import consultar_ficha
from alerta_temprana.servicio.modelos import registrar_modelos
from alerta_temprana.servicio.seguimiento import (
    AlertaInexistente,
    PermisoDenegado,
    cambiar_estado,
    historial_estados,
)
from tests.test_hu003 import (  # noqa: F401  (archivos_de_carga es una fixture)
    RAIZ_MODELOS,
    _cargar,
    archivos_de_carga,
)
from tests.test_hu005 import sembrar

NIVELES_CON_ALERTA = ("alto", "medio")


def _id_alerta(sesion, codigo: str) -> int:
    return sesion.scalar(select(Alerta.id_alerta).where(Alerta.codigo_estudiante == codigo))


def _contar(sesion, tabla, *condiciones) -> int:
    return sesion.scalar(select(func.count()).select_from(tabla).where(*condiciones))


def _cambios(sesion) -> list[tuple]:
    """Filas de CAMBIO_ESTADO, en orden, para comparar antes y después de un recálculo."""
    return sesion.execute(
        select(
            CambioEstado.id_cambio,
            CambioEstado.id_alerta,
            CambioEstado.id_usuario,
            CambioEstado.estado_anterior,
            CambioEstado.estado_nuevo,
            CambioEstado.fecha,
        ).order_by(CambioEstado.id_cambio)
    ).all()


# --- Criterio 2: cambio de estado con fecha y usuario ------------------------------------


@pytest.mark.db
def test_cambio_a_contactado_guarda_el_estado_con_fecha_y_usuario(sesion_db):
    sembrar(sesion_db)
    id_alerta = _id_alerta(sesion_db, "EST-0000000C")  # alto, pendiente
    antes = datetime.now(UTC)

    resultado = cambiar_estado(sesion_db, id_alerta, "contactado", "tutor01")

    assert resultado.registrado
    assert (resultado.estado_anterior, resultado.estado_nuevo) == ("pendiente", "contactado")
    assert resultado.usuario == "tutor01" and resultado.codigo_estudiante == "EST-0000000C"
    assert sesion_db.scalar(select(Alerta.estado).where(Alerta.id_alerta == id_alerta)) == "contactado"
    cambio, usuario = sesion_db.execute(
        select(CambioEstado, Usuario.nombre_usuario).join(Usuario, CambioEstado.id_usuario == Usuario.id_usuario)
    ).one()
    assert usuario == "tutor01"
    assert (cambio.id_alerta, cambio.estado_anterior, cambio.estado_nuevo) == (id_alerta, "pendiente", "contactado")
    assert cambio.fecha.tzinfo is not None  # TIMESTAMPTZ
    assert antes - timedelta(seconds=1) <= cambio.fecha <= datetime.now(UTC) + timedelta(seconds=1)
    assert cambio.id_cambio == resultado.id_cambio and cambio.fecha == resultado.fecha


@pytest.mark.db
def test_cambios_sucesivos_quedan_en_el_historial_y_se_puede_volver_a_pendiente(sesion_db):
    """Decisión del 09/11: volver a «pendiente» también queda registrado."""
    sembrar(sesion_db)
    id_alerta = _id_alerta(sesion_db, "EST-0000000C")
    cambiar_estado(sesion_db, id_alerta, "contactado", "tutor01")
    cambiar_estado(sesion_db, id_alerta, "en_acompanamiento", "coordinacion01")
    cambiar_estado(sesion_db, id_alerta, "pendiente", "tutor01")

    historial = historial_estados(sesion_db, id_alerta)
    assert [(c["estado_anterior"], c["estado_nuevo"], c["usuario"]) for c in historial] == [
        ("pendiente", "contactado", "tutor01"),
        ("contactado", "en_acompanamiento", "coordinacion01"),
        ("en_acompanamiento", "pendiente", "tutor01"),
    ]
    fechas = [c["fecha"] for c in historial]
    assert fechas == sorted(fechas)
    assert sesion_db.scalar(select(Alerta.estado).where(Alerta.id_alerta == id_alerta)) == "pendiente"
    # El historial es solo de esa alerta
    assert historial_estados(sesion_db, _id_alerta(sesion_db, "EST-0000000A")) == []


@pytest.mark.db
def test_mismo_estado_no_registra_nada(sesion_db):
    """Decisión del 09/11: si el estado nuevo es igual al actual, no se registra nada."""
    sembrar(sesion_db)
    id_alerta = _id_alerta(sesion_db, "EST-0000000D")  # en acompañamiento
    resultado = cambiar_estado(sesion_db, id_alerta, "en_acompanamiento", "tutor01")
    assert not resultado.registrado
    assert resultado.id_cambio is None and resultado.fecha is None
    assert resultado.estado_anterior == resultado.estado_nuevo == "en_acompanamiento"
    assert _contar(sesion_db, CambioEstado) == 0


@pytest.fixture
def usuario_inactivo(sesion_db):
    """Un tutor inactivo (rol y usuario no se vacían entre pruebas: se borra al terminar)."""
    id_rol = sesion_db.scalar(select(Rol.id_rol).where(Rol.nombre == "tutor"))
    usuario = Usuario(nombre_usuario="tutor_inactivo", id_rol=id_rol, activo=False)
    sesion_db.add(usuario)
    sesion_db.commit()
    yield usuario.nombre_usuario
    sesion_db.rollback()
    sesion_db.delete(usuario)
    sesion_db.commit()


@pytest.mark.db
@pytest.mark.parametrize(
    ("usuario", "motivo"),
    [
        ("sistemas01", "«area_sistemas»"),
        ("secretaria01", "«secretaria_academica»"),
        ("nadie99", "no existe o no está activo"),
    ],
)
def test_solo_coordinacion_y_tutor_pueden_cambiar_el_estado(sesion_db, usuario, motivo):
    sembrar(sesion_db)
    id_alerta = _id_alerta(sesion_db, "EST-0000000C")
    with pytest.raises(PermisoDenegado, match=motivo):
        cambiar_estado(sesion_db, id_alerta, "contactado", usuario)
    assert sesion_db.scalar(select(Alerta.estado).where(Alerta.id_alerta == id_alerta)) == "pendiente"
    assert _contar(sesion_db, CambioEstado) == 0


@pytest.mark.db
def test_usuario_inactivo_no_puede_cambiar_el_estado(sesion_db, usuario_inactivo):
    sembrar(sesion_db)
    with pytest.raises(PermisoDenegado, match="no existe o no está activo"):
        cambiar_estado(sesion_db, _id_alerta(sesion_db, "EST-0000000C"), "contactado", usuario_inactivo)
    assert _contar(sesion_db, CambioEstado) == 0


@pytest.mark.db
@pytest.mark.parametrize("estado", ["cerrado", "Contactado", "en acompañamiento", ""])
def test_estado_no_valido_no_guarda_nada(sesion_db, estado):
    sembrar(sesion_db)
    id_alerta = _id_alerta(sesion_db, "EST-0000000C")
    with pytest.raises(ValueError, match="Estado de seguimiento no válido"):
        cambiar_estado(sesion_db, id_alerta, estado, "tutor01")
    assert sesion_db.scalar(select(Alerta.estado).where(Alerta.id_alerta == id_alerta)) == "pendiente"
    assert _contar(sesion_db, CambioEstado) == 0


@pytest.mark.db
def test_alerta_inexistente(sesion_db):
    sembrar(sesion_db)
    with pytest.raises(AlertaInexistente):
        cambiar_estado(sesion_db, 99999, "contactado", "tutor01")
    assert _contar(sesion_db, CambioEstado) == 0


# --- Criterio 3: otro usuario ve el estado actualizado ------------------------------------


@pytest.mark.db
def test_otro_usuario_ve_el_estado_actualizado_en_el_listado_y_la_ficha(sesion_db, motor_pruebas):
    sembrar(sesion_db)
    id_alerta = _id_alerta(sesion_db, "EST-0000000C")
    pendientes_antes = resumir_alertas(consultar_alertas(sesion_db))["pendientes"]
    cambiar_estado(sesion_db, id_alerta, "contactado", "tutor01")

    # Otra sesión, como la de otro usuario que abre el listado
    from sqlalchemy.orm import Session

    with Session(motor_pruebas) as otra:
        alertas = consultar_alertas(otra)
        fila = next(a for a in alertas if a["id_alerta"] == id_alerta)
        assert fila["estado"] == "contactado"
        assert resumir_alertas(alertas)["pendientes"] == pendientes_antes - 1
        contactadas = consultar_alertas(otra, FiltrosAlertas(estados=["contactado"]))
        assert id_alerta in [a["id_alerta"] for a in contactadas]
        assert id_alerta not in [a["id_alerta"] for a in consultar_alertas(otra, FiltrosAlertas(estados=["pendiente"]))]
        ficha = consultar_ficha(otra, id_alerta)
        assert ficha["estado"] == "contactado"
        assert [(c["estado_nuevo"], c["usuario"]) for c in ficha["cambios_estado"]] == [("contactado", "tutor01")]


# --- API (decisión P4) ---------------------------------------------------------------------


@pytest.fixture
def cliente(sesion_db):
    app.dependency_overrides[obtener_sesion] = lambda: sesion_db
    yield TestClient(app)  # sin «with»: no corre el ciclo de vida sobre la base de desarrollo
    app.dependency_overrides.clear()


@pytest.mark.db
def test_api_cambia_el_estado_y_la_ficha_muestra_el_historial(cliente, sesion_db):
    sembrar(sesion_db)
    id_alerta = _id_alerta(sesion_db, "EST-0000000C")
    respuesta = cliente.post(f"/api/alertas/{id_alerta}/estado", json={"estado": "contactado", "usuario": "tutor01"})
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["registrado"] is True
    assert (datos["estado_anterior"], datos["estado_nuevo"], datos["usuario"]) == ("pendiente", "contactado", "tutor01")
    assert datetime.fromisoformat(datos["fecha"]).tzinfo is not None

    ficha = cliente.get(f"/api/alertas/{id_alerta}").json()
    assert ficha["estado"] == "contactado"
    assert [(c["estado_anterior"], c["estado_nuevo"], c["usuario"]) for c in ficha["cambios_estado"]] == [
        ("pendiente", "contactado", "tutor01")
    ]
    listado = cliente.get("/api/alertas", params={"estado": "contactado"}).json()
    assert id_alerta in [a["id_alerta"] for a in listado["alertas"]]

    otra_vez = cliente.post(f"/api/alertas/{id_alerta}/estado", json={"estado": "contactado", "usuario": "coordinacion01"})
    assert otra_vez.status_code == 200 and otra_vez.json()["registrado"] is False


@pytest.mark.db
@pytest.mark.parametrize(
    ("id_alerta", "cuerpo", "codigo"),
    [
        (None, {"estado": "contactado", "usuario": "sistemas01"}, 403),
        (None, {"estado": "contactado", "usuario": "secretaria01"}, 403),
        (99999, {"estado": "contactado", "usuario": "tutor01"}, 404),
        (None, {"estado": "cerrado", "usuario": "tutor01"}, 422),
        (None, {"usuario": "tutor01"}, 422),
    ],
)
def test_api_rechazos(cliente, sesion_db, id_alerta, cuerpo, codigo):
    sembrar(sesion_db)
    id_alerta = id_alerta or _id_alerta(sesion_db, "EST-0000000C")
    assert cliente.post(f"/api/alertas/{id_alerta}/estado", json=cuerpo).status_code == codigo
    assert _contar(sesion_db, CambioEstado) == 0


# --- Criterios 1, 4, 5 y 6 con recálculos ----------------------------------------------------
# Los estados se cambian con cambiar_estado, alternando estados y usuarios.


def _foto(sesion) -> dict[str, dict]:
    """Por estudiante con alerta: id, estado, predicción de la alerta y nivel de esa predicción."""
    filas = sesion.execute(
        select(Alerta.codigo_estudiante, Alerta.id_alerta, Alerta.estado, Alerta.id_prediccion, Prediccion.nivel).join(
            Prediccion, Alerta.id_prediccion == Prediccion.id_prediccion
        )
    ).all()
    return {
        f.codigo_estudiante: {"id_alerta": f.id_alerta, "estado": f.estado, "id_prediccion": f.id_prediccion, "nivel": f.nivel}
        for f in filas
    }


def _vigentes(sesion) -> dict[str, tuple[int, str]]:
    filas = sesion.execute(
        select(Prediccion.codigo_estudiante, Prediccion.id_prediccion, Prediccion.nivel).where(Prediccion.vigente)
    ).all()
    return {f.codigo_estudiante: (f.id_prediccion, f.nivel) for f in filas}


def _cambiar_todas(sesion, codigos) -> None:
    """Cambia el estado de esas alertas con cambiar_estado (contactado / en acompañamiento,
    tutor01 / coordinacion01)."""
    for i, codigo in enumerate(sorted(codigos)):
        estado = ("contactado", "en_acompanamiento")[i % 2]
        usuario = ("tutor01", "coordinacion01")[(i // 2) % 2]
        assert cambiar_estado(sesion, _id_alerta(sesion, codigo), estado, usuario).registrado


def _recalcular(sesion, plan, cargar, momento: M, tiempo: int):
    resultado = cargar(momento)
    estado = plan.esperar(resultado.id_carga, tiempo=tiempo)
    assert estado.estado == "completado", estado.mensaje
    return estado


def _comprobar_paso(sesion, antes: dict, cambios_antes: list) -> dict[str, list[str]]:
    """Controla los criterios 4 y 5 después de un recálculo y devuelve los caminos de cada
    estudiante: «sigue» (alto o medio → alto o medio), «baja» (→ bajo), «vuelve» (bajo con
    alerta → medio o alto), «nueva» (sin alerta → alerta) y «bajo_sin_alerta»."""
    despues, vigentes = _foto(sesion), _vigentes(sesion)
    caminos: dict[str, list[str]] = {"sigue": [], "baja": [], "vuelve": [], "nueva": [], "bajo_sin_alerta": []}
    for codigo, (id_prediccion, nivel) in vigentes.items():
        if codigo in antes:
            alerta, previa = despues[codigo], antes[codigo]
            # Misma alerta, mismo estado, apuntando a la predicción vigente (criterios 4 y 5)
            assert alerta["id_alerta"] == previa["id_alerta"], codigo
            assert alerta["estado"] == previa["estado"], codigo
            assert alerta["id_prediccion"] == id_prediccion and alerta["nivel"] == nivel, codigo
            if nivel == "bajo":
                caminos["baja"].append(codigo)
            elif previa["nivel"] == "bajo":
                caminos["vuelve"].append(codigo)
            else:
                caminos["sigue"].append(codigo)
        elif codigo in despues:
            # Sin alerta y sube a medio o alto: alerta nueva en «pendiente» (criterios 1 y 5)
            assert nivel in NIVELES_CON_ALERTA and despues[codigo]["estado"] == "pendiente", codigo
            caminos["nueva"].append(codigo)
        else:
            assert nivel == "bajo", codigo
            caminos["bajo_sin_alerta"].append(codigo)
    # Una alerta por estudiante; el recálculo no registra cambios de estado
    assert _contar(sesion, Alerta) == len(despues) == len(set(a["id_alerta"] for a in despues.values()))
    assert _cambios(sesion) == cambios_antes
    # Criterio 4: las que bajaron siguen en el listado, con nivel bajo y su estado
    listado = {a["codigo_estudiante"]: a for a in consultar_alertas(sesion)}
    for codigo in caminos["baja"]:
        assert listado[codigo]["nivel"] == "bajo" and listado[codigo]["estado"] == antes[codigo]["estado"]
    return caminos


def _comprobar_recarga(sesion, plan, cargar, momento: M, tiempo: int) -> None:
    """Criterio 6: recargar el archivo del mismo momento."""
    antes, cambios_antes = _foto(sesion), _cambios(sesion)
    predicciones_antes = sesion.execute(
        select(Prediccion.id_prediccion, Prediccion.codigo_estudiante, Prediccion.fecha)
    ).all()
    estado = _recalcular(sesion, plan, cargar, momento, tiempo)
    assert estado.resumen["alertas_creadas"] == 0
    despues, vigentes = _foto(sesion), _vigentes(sesion)
    assert {c: (a["id_alerta"], a["estado"]) for c, a in despues.items()} == {
        c: (a["id_alerta"], a["estado"]) for c, a in antes.items()
    }
    assert _cambios(sesion) == cambios_antes
    # La alerta usa solo la predicción más reciente; las anteriores quedan en el historial con su fecha
    historial = {
        p.id_prediccion: p
        for p in sesion.execute(
            select(Prediccion.id_prediccion, Prediccion.codigo_estudiante, Prediccion.fecha, Prediccion.vigente)
        )
    }
    for p in predicciones_antes:
        assert historial[p.id_prediccion].vigente is False
        assert historial[p.id_prediccion].fecha == p.fecha
    for codigo, alerta in despues.items():
        nueva = historial[alerta["id_prediccion"]]
        assert alerta["id_prediccion"] == vigentes[codigo][0] and nueva.vigente
        assert alerta["id_prediccion"] not in {p.id_prediccion for p in predicciones_antes}
        anteriores = [p.fecha for p in predicciones_antes if p.codigo_estudiante == codigo]
        assert anteriores and nueva.fecha > max(anteriores)


def _escenario(sesion, plan, cargar, tiempo: int) -> dict[str, set[str]]:
    """Inscripción → cambio de estado de todas las alertas → cierre_1s → cambio de estado de
    las nuevas → cierre_2s → recarga de cierre_2s. Devuelve los caminos que aparecieron."""
    registrar_modelos(sesion, RAIZ_MODELOS)
    _recalcular(sesion, plan, cargar, M.INSCRIPCION, tiempo)
    inicial = _foto(sesion)
    # Criterio 1: las alertas aparecen en «pendiente», sin cambios de estado registrados
    assert inicial and {a["estado"] for a in inicial.values()} == {"pendiente"}
    assert {a["nivel"] for a in inicial.values()} <= set(NIVELES_CON_ALERTA)
    assert _cambios(sesion) == []

    _cambiar_todas(sesion, inicial)
    assert _contar(sesion, CambioEstado) == len(inicial)
    caminos: dict[str, set[str]] = {}
    for momento in (M.CIERRE_1S, M.CIERRE_2S):
        antes = _foto(sesion)
        assert "pendiente" not in {a["estado"] for a in antes.values()}
        cambios_antes = _cambios(sesion)
        _recalcular(sesion, plan, cargar, momento, tiempo)
        paso = _comprobar_paso(sesion, antes, cambios_antes)
        for camino, codigos in paso.items():
            caminos.setdefault(camino, set()).update(codigos)
        _cambiar_todas(sesion, paso["nueva"])

    _comprobar_recarga(sesion, plan, cargar, M.CIERRE_2S, tiempo)
    return caminos


@pytest.mark.db
def test_estado_se_conserva_en_las_cargas_siguientes_con_las_fixtures(sesion_db, ruta_fixtures, planificador):
    """Criterios 1, 4, 5 y 6 con los 10 estudiantes de tests/fixtures/ (cubren los cuatro
    caminos entre inscripción, cierre_1s y cierre_2s)."""
    caminos = _escenario(sesion_db, planificador, lambda m: _cargar(sesion_db, ruta_fixtures, m), tiempo=60)
    tamanos = {k: len(v) for k, v in caminos.items()}
    for camino in ("sigue", "baja", "vuelve", "nueva"):
        assert caminos[camino], f"falta el camino «{camino}»: {tamanos}"


@pytest.mark.db
@pytest.mark.datos
def test_estado_se_conserva_en_las_cargas_siguientes_con_los_885_estudiantes(sesion_db, archivos_de_carga, planificador):  # noqa: F811
    """Criterios 1, 4, 5 y 6 con los tres archivos de data/cargas/ (clave actual), con todos
    los caminos: sigue en alto o medio, baja a bajo, vuelve a medio o alto con su alerta y
    alerta nueva en «pendiente»."""

    def cargar(momento):
        resultado = servicio_carga.registrar_carga(
            sesion_db, archivos_de_carga[momento].read_bytes(), momento, "sistemas01"
        )
        assert (resultado.registros_validos, resultado.registros_rechazados) == (885, 0)
        return resultado

    caminos = _escenario(sesion_db, planificador, cargar, tiempo=300)
    tamanos = {k: len(v) for k, v in caminos.items()}
    for camino in ("sigue", "baja", "vuelve", "nueva"):
        assert caminos[camino], f"falta el camino «{camino}»: {tamanos}"
    assert _contar(sesion_db, Alerta) == 529  # como en la verificación de HU-005


# --- Tarea 7.2: control de estado en el listado y en la ficha ---------------------------------

CAMBIO_UTC = datetime(2026, 11, 9, 17, 32, tzinfo=UTC)  # 14:32 en hora argentina
OPCIONES_ESPERADAS = [
    {"label": "Pendiente", "value": "pendiente"},
    {"label": "Contactado", "value": "contactado"},
    {"label": "En acompañamiento", "value": "en_acompanamiento"},
]


def _de_tipo(raiz, tipo: str) -> list:
    from tests.test_hu005 import _componentes

    return [c for c in _componentes(raiz) if type(c).__name__ == tipo]


def test_listado_tiene_desplegable_y_guardar_en_cada_fila():
    from alerta_temprana.ui import listado
    from tests.test_hu005 import _alerta

    filas = listado.filas_tabla([_alerta(id_alerta=7, estado="contactado"), _alerta(id_alerta=8)])
    for fila, (id_alerta, estado) in zip(filas, [(7, "contactado"), (8, "pendiente")], strict=True):
        (desplegable,) = _de_tipo(fila, "Dropdown")
        assert desplegable.id == {"type": listado.ID_ESTADO, "index": id_alerta}
        assert desplegable.value == estado
        assert desplegable.options == OPCIONES_ESPERADAS
        assert desplegable.clearable is False
        (boton,) = _de_tipo(fila, "Button")
        assert boton.id == {"type": listado.ID_GUARDAR, "index": id_alerta}
        assert boton.children == "Guardar"
    assert "mensaje-estado-listado" in str(listado.contenido())


def test_alerta_a_guardar_solo_con_un_clic_real():
    from alerta_temprana.ui.listado import ID_ESTADO, ID_GUARDAR, alerta_a_guardar

    ids = [{"type": ID_ESTADO, "index": 7}, {"type": ID_ESTADO, "index": 8}]
    valores = ["contactado", "en_acompanamiento"]
    assert alerta_a_guardar({"type": ID_GUARDAR, "index": 8}, 1, ids, valores) == (8, "en_acompanamiento")
    # Tabla vuelta a armar: botones nuevos con 0 clics
    assert alerta_a_guardar({"type": ID_GUARDAR, "index": 8}, 0, ids, valores) is None
    assert alerta_a_guardar(None, 1, ids, valores) is None
    assert alerta_a_guardar({"type": ID_GUARDAR, "index": 99}, 1, ids, valores) is None


def test_textos_de_confirmacion_en_hora_argentina():
    from alerta_temprana.servicio.seguimiento import CambioRegistrado
    from alerta_temprana.ui.seguimiento import texto_confirmacion, texto_ultimo_cambio

    registrado = CambioRegistrado(1, "EST-932B2E48", "pendiente", "contactado", "tutor01", True, 5, CAMBIO_UTC)
    assert texto_confirmacion(registrado) == "Estado de EST-932B2E48 guardado: Contactado (tutor01, 09/11/2026 14:32)."
    igual = CambioRegistrado(1, "EST-932B2E48", "contactado", "contactado", "tutor01", False)
    assert texto_confirmacion(igual) == "EST-932B2E48 ya estaba en «Contactado»; no se registró ningún cambio."
    assert (
        texto_ultimo_cambio("contactado", "en_acompanamiento", "coordinacion01", CAMBIO_UTC)
        == "Último cambio: Contactado → En acompañamiento, por coordinacion01, el 09/11/2026 14:32"
    )


def test_ficha_tiene_desplegable_guardar_estado_y_alerta_creada():
    from tests.test_hu005 import _por_id, _texto
    from tests.test_hu006 import _contenido

    componentes = _por_id(_contenido(estado="en_acompanamiento"))
    desplegable = componentes["ficha-estado"]
    assert desplegable.value == "en_acompanamiento" and desplegable.options == OPCIONES_ESPERADAS
    assert componentes["boton-guardar-estado"].children == "Guardar estado"
    assert componentes["ficha-id-alerta"].data == 294
    seguimiento = _texto(componentes["ficha-seguimiento"])
    assert "Seguimiento" in seguimiento and "Estado" in seguimiento
    assert "Alerta creada el 08/11/2026" in seguimiento
    assert "Último cambio" not in seguimiento  # todavía no hubo cambios


def test_ficha_muestra_el_ultimo_cambio_con_usuario_y_hora_argentina():
    from tests.test_hu005 import _por_id, _texto
    from tests.test_hu006 import _contenido

    cambios = [
        {
            "estado_anterior": "pendiente",
            "estado_nuevo": "contactado",
            "usuario": "tutor01",
            "fecha": CAMBIO_UTC - timedelta(days=1),
        },
        {
            "estado_anterior": "contactado",
            "estado_nuevo": "en_acompanamiento",
            "usuario": "coordinacion01",
            "fecha": CAMBIO_UTC,
        },
    ]
    componentes = _por_id(_contenido(estado="en_acompanamiento", cambios_estado=cambios))
    assert _texto(componentes["ficha-ultimo-cambio"]) == (
        "Último cambio: Contactado → En acompañamiento, por coordinacion01, el 09/11/2026 14:32"
    )


@pytest.fixture
def pantallas_sobre_pruebas(motor_pruebas, monkeypatch):
    """Las pantallas usan la base de pruebas en lugar de la de desarrollo."""
    from sqlalchemy.orm import sessionmaker

    fabrica = sessionmaker(bind=motor_pruebas, expire_on_commit=False)
    for modulo in ("seguimiento", "listado", "ficha"):
        monkeypatch.setattr(f"alerta_temprana.ui.{modulo}.obtener_fabrica_sesiones", lambda: fabrica)


@pytest.mark.db
def test_guardar_desde_la_pantalla_y_otro_usuario_ve_el_estado(sesion_db, pantallas_sobre_pruebas):
    """Criterios 2 y 3 desde las pantallas: tutor01 guarda; Coordinación abre el listado y la
    ficha y ve el estado nuevo con el último cambio."""
    from alerta_temprana.ui import ficha, listado
    from alerta_temprana.ui.seguimiento import guardar_estado
    from tests.test_hu005 import _por_id, _texto

    sembrar(sesion_db)
    id_alerta = _id_alerta(sesion_db, "EST-0000000C")
    guardado = guardar_estado(id_alerta, "contactado", "tutor01")
    assert guardado.resultado.registrado
    assert "mensaje-ok" in guardado.mensaje.className
    assert guardado.mensaje.children.startswith("Estado de EST-0000000C guardado: Contactado (tutor01, ")

    _tarjetas, _cantidad, filas = listado.actualizar_listado(None, None, None, None, "coordinacion01", None)
    estados = {d.id["index"]: d.value for fila in filas for d in _de_tipo(fila, "Dropdown")}
    assert estados[id_alerta] == "contactado"

    _titulo, contenido = ficha.pantalla(id_alerta)
    componentes = _por_id(contenido)
    assert componentes["ficha-estado"].value == "contactado"
    assert _texto(componentes["ficha-ultimo-cambio"]).startswith(
        "Último cambio: Pendiente → Contactado, por tutor01, el "
    )


def test_tarjetas_sobre_las_alertas_visibles_con_su_estado_actual():
    """Después de guardar, las tarjetas cuentan las alertas que muestra la tabla (decisión del
    07/11), aunque con un filtro de estado activo la fila guardada ya no lo cumpla."""
    from alerta_temprana.ui.listado import resumen_visible
    from tests.test_hu005 import _alerta

    alertas = [
        _alerta(id_alerta=1, nivel="alto", estado="contactado"),  # recién guardada
        _alerta(id_alerta=2, nivel="medio", estado="pendiente"),
        _alerta(id_alerta=3, nivel="alto", estado="pendiente"),  # no está en la tabla (filtro)
    ]
    assert resumen_visible(alertas, [1, 2]) == {"alto": 1, "medio": 1, "pendientes": 1, "total": 2}


@pytest.mark.db
def test_guardar_en_el_listado_actualiza_las_tarjetas_sin_armar_la_tabla(sesion_db, pantallas_sobre_pruebas):
    from dash import html

    from alerta_temprana.ui import listado
    from tests.test_hu005 import _texto

    sembrar(sesion_db)
    visibles = [a["id_alerta"] for a in consultar_alertas(sesion_db, FiltrosAlertas(estados=["pendiente"]))]
    antes = _texto(html.Div(listado.tarjetas_actualizadas(visibles)))
    cambiar_estado(sesion_db, _id_alerta(sesion_db, "EST-0000000C"), "contactado", "tutor01")
    despues = _texto(html.Div(listado.tarjetas_actualizadas(visibles)))
    assert "Pendientes de contacto 4" in antes and "Pendientes de contacto 3" in despues


@pytest.mark.db
def test_ficha_guardar_actualiza_el_mensaje_y_el_ultimo_cambio(sesion_db, pantallas_sobre_pruebas):
    from dash import no_update

    from alerta_temprana.ui.ficha import resultado_guardado
    from tests.test_hu005 import _texto

    sembrar(sesion_db)
    id_alerta = _id_alerta(sesion_db, "EST-0000000C")
    mensaje, ultimo = resultado_guardado(id_alerta, "en_acompanamiento", "coordinacion01")
    assert "guardado: En acompañamiento (coordinacion01, " in mensaje.children
    assert _texto(ultimo).startswith("Último cambio: Pendiente → En acompañamiento, por coordinacion01, el ")
    # Mismo estado: se avisa y el último cambio no se toca
    mensaje, ultimo = resultado_guardado(id_alerta, "en_acompanamiento", "tutor01")
    assert "no se registró ningún cambio" in mensaje.children and ultimo is no_update


@pytest.mark.db
@pytest.mark.parametrize("usuario", ["sistemas01", "secretaria01"])
def test_pantalla_rechaza_a_otros_roles_con_el_motivo(sesion_db, pantallas_sobre_pruebas, usuario):
    from alerta_temprana.ui.seguimiento import guardar_estado

    sembrar(sesion_db)
    guardado = guardar_estado(_id_alerta(sesion_db, "EST-0000000C"), "contactado", usuario)
    assert guardado.resultado is None and "mensaje-error" in guardado.mensaje.className
    assert "Coordinación del Programa de Tutorías y los tutores" in guardado.mensaje.children
    assert _contar(sesion_db, CambioEstado) == 0


def test_pantalla_sin_base_muestra_el_motivo(monkeypatch):
    from sqlalchemy.exc import OperationalError

    from alerta_temprana.ui import seguimiento

    def sin_base():
        raise OperationalError("SELECT 1", {}, Exception("sin conexión"))

    monkeypatch.setattr(seguimiento, "obtener_fabrica_sesiones", sin_base)
    guardado = seguimiento.guardar_estado(1, "contactado", "tutor01")
    assert guardado.resultado is None and guardado.mensaje.children == seguimiento.SIN_BASE


def test_cada_contenedor_de_primer_nivel_tiene_id_propio(monkeypatch):
    """Regresión del 09/11: sin id, Dash 3.4 reutilizaba en el navegador lo dibujado en la
    misma posición, y al guardar el estado en la ficha (abierta desde el listado) volvían a
    aparecer los filtros del listado en lugar de «Volver al listado». Cada contenedor de
    primer nivel de cada pantalla tiene que tener un id, distinto del de cualquier otra
    pantalla."""
    from alerta_temprana.ui import carga, ficha, listado, panel
    from tests.test_hu006 import _contenido

    monkeypatch.setattr(ficha, "_leer_ficha", lambda _id: None)
    pantallas = {
        "carga": carga.contenido(),
        "listado": listado.contenido(),
        "ficha": _contenido(),
        "ficha_inexistente": ficha.pantalla(1)[1],
        "metricas": panel.contenido_metricas(),
    }
    vistos: dict[str, str] = {}
    for nombre, hijos in pantallas.items():
        for hijo in hijos:
            id_ = getattr(hijo, "id", None)
            assert id_, f"{nombre}: {type(hijo).__name__} sin id"
            if id_ in vistos and vistos[id_] != nombre:
                assert id_ == "ficha-volver" and {nombre, vistos[id_]} <= {"ficha", "ficha_inexistente"}, id_
            vistos.setdefault(id_, nombre)


def test_textos_de_seguimiento_sin_terminos_prohibidos():
    from pathlib import Path

    import alerta_temprana.servicio.seguimiento as servicio
    import alerta_temprana.ui.seguimiento as ui

    for modulo in (servicio, ui):
        texto = Path(modulo.__file__).read_text(encoding="utf-8").lower()
        for prohibido in ("enrolled", "matriculado", "severidad", "riesgo crítico", "anonimizado", "ingesta"):
            assert prohibido not in texto, (modulo.__name__, prohibido)
