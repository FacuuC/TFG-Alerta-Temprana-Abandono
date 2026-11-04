"""Informe de evaluación final en Markdown (reportes/informe_evaluacion.md).

Recibe un ResultadoEvaluacion ya calculado y solo arma el texto, así se puede probar
con resultados simulados. En modo ensayo (validación en lugar de prueba) el título lo
dice en forma explícita.
"""

from __future__ import annotations

import json

from alerta_temprana import formato as F
from alerta_temprana.datos import variables as V
from alerta_temprana.modelo.etiquetas import NOMBRES
from alerta_temprana.modelo.evaluacion import AUC_MINIMO_CIERRE_1S, PUESTOS_PESO_ALTO, ResultadoEvaluacion

TITULO = "Informe de evaluación final"
TITULO_ENSAYO = "ENSAYO (validación) — no son resultados de prueba"
FRASE_ELECCION = (
    "La elección del modelo de cada momento se hizo con el conjunto de validación, antes de ver la "
    "prueba. La comparación en prueba con la alternativa no elegida es solo informativa: aunque la "
    "alternativa salga mejor, el modelo habilitado no cambia."
)
NOMBRE_ALGORITMO = {"xgboost": "XGBoost", "regresion_logistica": "Regresión logística"}


def _si_no(valor: bool) -> str:
    return "sí" if valor else "no"


def _tabla(encabezado: list[str], filas: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(encabezado) + " |",
        "|" + "---|" * len(encabezado),
        *("| " + " | ".join(f) + " |" for f in filas),
    ]


def armar_informe(r: ResultadoEvaluacion) -> str:
    conj = r.conjunto
    L: list[str] = []
    if r.ensayo:
        L += [
            f"# {TITULO_ENSAYO}",
            "",
            "> Ensayo de `scripts/evaluar_final.py` con el conjunto de **validación** en lugar de prueba,",
            "> para verificar el script de punta a punta. **No son resultados de prueba** y no se usan en",
            "> el documento. No se registró ningún uso de la prueba ni se modificó ningún modelo.",
            "",
        ]
    else:
        L += [f"# {TITULO}", ""]
    L += [
        f"Generado por `scripts/evaluar_final.py` el **{F.fecha_hora(r.fecha)}** "
        f"(tareas 2.4 y 2.5; CRISP-DM, fase 5, etapa B). Conjunto evaluado: **{conj}** "
        f"({F.entero(r.momentos[0].metricas['n'])} estudiantes, {F.entero(r.momentos[0].metricas['abandonos'])} abandonos).",
        "",
    ]
    if not r.ensayo:
        L += [
            "El conjunto de prueba se usa **una sola vez**, en esta ejecución, que autorizó una persona",
            "desde una terminal interactiva (`reportes/uso_conjunto_prueba.json`). Si un resultado no",
            "alcanza el objetivo, se informa como tal: la prueba no se usa para reajustar nada.",
            "",
        ]
    if r.motivo_repeticion:
        L += [f"**Ejecución repetida.** Motivo: {r.motivo_repeticion}", ""]
    L += [f"**{FRASE_ELECCION}**", ""]

    # 1. Modelos
    L += ["## 1. Modelos evaluados", ""]
    L += _tabla(
        ["Momento", "Versión", "Algoritmo", "Hiperparámetros", "Entrenado", "SHA-256 de `pipeline.joblib`"],
        [
            [V.ETIQUETA_MOMENTO[m.momento], m.version, NOMBRE_ALGORITMO[m.algoritmo],
             f"`{json.dumps(m.hiperparametros)}`", m.fecha_entrenamiento[:10], f"`{m.sha256[:16]}…`"]
            for m in r.momentos
        ],
    )

    # 2. Desempeño
    L += [
        "",
        f"## 2. Desempeño por momento ({conj})",
        "",
        "Alerta = nivel alto o medio (probabilidad ≥ umbral medio). Precisión: de los estudiantes con",
        "alerta, qué proporción abandonó. Sensibilidad: de los que abandonaron, qué proporción tuvo alerta.",
        "",
    ]
    L += _tabla(
        ["Momento", f"AUC-ROC ({conj})", "Precisión", "Sensibilidad", "AUC-ROC en validación (al elegir el modelo)"],
        [
            [V.ETIQUETA_MOMENTO[m.momento], F.decimal(m.metricas["auc_roc"]),
             F.decimal(m.metricas["precision_alerta"], 3), F.decimal(m.metricas["sensibilidad_alerta"], 3),
             F.decimal(m.auc_validacion)]
            for m in r.momentos
        ],
    )
    c1s = next(m for m in r.momentos if m.momento is V.Momento.CIERRE_1S)
    alcanzada = c1s.metricas["auc_roc"] > AUC_MINIMO_CIERRE_1S
    L += [
        "",
        f"**Meta del objetivo 1** (AUC-ROC > {F.decimal(AUC_MINIMO_CIERRE_1S, 2)} en el cierre del 1.er semestre): "
        f"{'**alcanzada**' if alcanzada else '**no alcanzada**'} ({F.decimal(c1s.metricas['auc_roc'])}).",
        "",
        "Matriz de confusión de la alerta:",
        "",
    ]
    L += _tabla(
        ["Momento", "Abandonos con alerta", "Abandonos sin alerta", "No abandonos con alerta", "No abandonos sin alerta"],
        [
            [V.ETIQUETA_MOMENTO[m.momento], F.entero(m.metricas["verdaderos_positivos"]),
             F.entero(m.metricas["falsos_negativos"]), F.entero(m.metricas["falsos_positivos"]),
             F.entero(m.metricas["verdaderos_negativos"])]
            for m in r.momentos
        ],
    )

    # 3. Umbrales
    L += [
        "",
        f"## 3. Umbrales (fijados en validación) y su comprobación en {conj}",
        "",
    ]
    L += _tabla(
        ["Momento", "Umbral alto", "Umbral medio", f"En nivel alto (≤ {F.porcentaje(r.capacidad, 0)})",
         f"Abandonos detectados (≥ {F.porcentaje(r.deteccion, 0)})", "Abandono por nivel (alto / medio / bajo)",
         "Decreciente"],
        [
            [V.ETIQUETA_MOMENTO[m.momento], F.decimal(m.umbral_alto), F.decimal(m.umbral_medio),
             f"{F.porcentaje(m.comprobacion['proporcion_alto'])} ({_si_no(m.comprobacion['proporcion_alto'] <= r.capacidad)})",
             f"{F.porcentaje(m.comprobacion['deteccion_alto_medio'])} ({_si_no(m.comprobacion['deteccion_alto_medio'] >= r.deteccion)})",
             " / ".join(F.porcentaje(m.comprobacion[f"tasa_abandono_{n}"]) for n in ("alto", "medio", "bajo")),
             _si_no(m.comprobacion["decreciente"])]
            for m in r.momentos
        ],
    )
    L += [
        "",
        "Entre paréntesis, si se cumple la regla. Los umbrales no se modifican con estos resultados.",
    ]

    # 4. Alternativa
    L += [
        "",
        f"## 4. Comparación con la alternativa no elegida ({conj}, solo informativa)",
        "",
        FRASE_ELECCION,
        "",
        "La alternativa es la regresión logística de referencia cuando el elegido es XGBoost, y el mejor",
        "XGBoost de la grilla cuando el elegido es la regresión logística. Se volvió a ajustar con",
        "entrenamiento y, antes de leer la prueba, se comprobó que reproduce su AUC-ROC de validación",
        "registrado (tolerancia ±0,0005).",
        "",
    ]
    L += _tabla(
        ["Momento", "Elegido", f"AUC-ROC elegido ({conj})", "Alternativa", f"AUC-ROC alternativa ({conj})",
         "Precisión / sensibilidad alternativa", "AUC-ROC validación alternativa: registrado / recalculado"],
        [
            [V.ETIQUETA_MOMENTO[m.momento], NOMBRE_ALGORITMO[m.algoritmo], F.decimal(m.metricas["auc_roc"]),
             NOMBRE_ALGORITMO[m.alternativa["algoritmo"]], F.decimal(m.alternativa["metricas"]["auc_roc"]),
             f"{F.decimal(m.alternativa['metricas']['precision_alerta'], 3)} / "
             f"{F.decimal(m.alternativa['metricas']['sensibilidad_alerta'], 3)}",
             f"{F.decimal(m.alternativa['auc_validacion_registrado'])} / {F.decimal(m.alternativa['auc_validacion_recalculado'])}"]
            for m in r.momentos
        ],
    )
    L += ["", "La alternativa usa los umbrales del modelo elegido para la alerta (alto + medio)."]

    # 5. Subgrupos
    L += [
        "",
        f"## 5. Desempeño por subgrupos (cierre del 1.er semestre, {conj})",
        "",
        "AUC-ROC no definido («—») si el grupo tiene una sola clase.",
        "",
    ]
    L += _tabla(
        ["Subgrupo", "Grupo", "Estudiantes", "Abandonos", "AUC-ROC", "Sensibilidad", "Precisión"],
        [
            [f.subgrupo, f.grupo, F.entero(f.n), F.entero(f.abandonos), F.decimal(f.auc_roc),
             F.decimal(f.sensibilidad_alerta, 3), F.decimal(f.precision_alerta, 3)]
            for f in r.subgrupos.itertuples()
        ],
    )

    # 6. Sin cursando
    L += [
        "",
        f"## 6. AUC-ROC con y sin «sigue cursando» (cierre del 1.er semestre, {conj})",
        "",
    ]
    L += _tabla(
        ["Cálculo", "Estudiantes", "AUC-ROC"],
        [
            ["Con todos (graduado y sigue cursando = no abandono)", F.entero(r.cursando["n_con_cursando"]),
             F.decimal(r.cursando["auc_roc_con_cursando"])],
            ["Sin quienes siguen cursando", F.entero(r.cursando["n_sin_cursando"]),
             F.decimal(r.cursando["auc_roc_sin_cursando"])],
        ],
    )
    L += [
        "",
        "Quienes siguen cursando todavía pueden abandonar más adelante. Si el AUC-ROC sube al sacarlos,",
        "parte de los «errores» del modelo está en ese grupo de situación incierta.",
    ]

    # 7. SHAP
    L += [
        "",
        f"## 7. Variables que más pesan en las estimaciones (SHAP, cierre del 1.er semestre, {conj})",
        "",
        "Media del valor absoluto de SHAP por variable. Muestra cuánto pesa cada variable en las",
        "estimaciones del modelo, **no las causas** del abandono.",
        "",
    ]
    L += _tabla(
        ["Puesto", "Variable", "Peso medio"],
        [[str(i + 1), NOMBRES[v], F.decimal(p, 3)] for i, (v, p) in enumerate(r.importancia.head(10).items())],
    )
    altas = r.demograficas[r.demograficas["peso_alto"]]
    L += [
        "",
        f"**Revisión de variables demográficas.** Se considera «peso alto» estar entre las {PUESTOS_PESO_ALTO}",
        "variables de mayor peso medio.",
        "",
    ]
    L += _tabla(
        ["Variable demográfica", "Puesto", "Peso medio", "Peso alto"],
        [[NOMBRES[f.variable], str(f.puesto), F.decimal(f.peso_medio, 3), _si_no(f.peso_alto)]
         for f in r.demograficas.itertuples()],
    )
    if len(altas):
        L += [
            "",
            "Tienen peso alto: " + ", ".join(NOMBRES[v] for v in altas["variable"]) + ". Conviene leerlo junto",
            "con las diferencias entre subgrupos de la sección 5: el peso indica que el modelo usa la",
            "variable para estimar, no que esa característica cause el abandono.",
        ]
    else:
        L += ["", "Ninguna variable demográfica está entre las de mayor peso."]

    # 8. Habilitación
    L += ["", "## 8. Habilitación", ""]
    if r.ensayo:
        L += ["En el ensayo no se habilita ni se registra nada. Así quedaría con estos números:", ""]
    L += _tabla(
        ["Momento", "Habilitado", "Motivo"],
        [[V.ETIQUETA_MOMENTO[m.momento], _si_no(m.habilitado), m.motivo_habilitacion] for m in r.momentos],
    )
    if not r.ensayo:
        L += [
            "",
            "Cada modelo queda registrado en `modelos/<momento>/v<versión>/metadatos.json` con su versión, la",
            "fecha de entrenamiento, la fecha de esta evaluación, sus métricas y sus umbrales.",
        ]
    return "\n".join(L) + "\n"
