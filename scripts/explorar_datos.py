"""Análisis exploratorio de los datos (tarea 2.1; CRISP-DM, fase 2).

Uso:  python scripts/explorar_datos.py

Escribe reportes/informe_exploratorio.md y las figuras de reportes/figuras/.

- Todo lo que relaciona una variable con el abandono usa SOLO el conjunto de
  entrenamiento de la partición guardada (data/procesados/particion.csv).
- Los controles de calidad que no miran la situación final (faltantes, rangos) usan el
  archivo completo sin la variable objetivo.
- El conjunto de prueba no se usa: ni sus etiquetas ni sus estadísticas.
"""

from __future__ import annotations

import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from alerta_temprana import formato as F  # noqa: E402
from alerta_temprana.config import RAIZ  # noqa: E402
from alerta_temprana.datos import exploracion as X  # noqa: E402
from alerta_temprana.datos import variables as V  # noqa: E402
from alerta_temprana.modelo import preparacion as P  # noqa: E402
from alerta_temprana.modelo.etiquetas import NOMBRES, texto_valor  # noqa: E402

RUTA_DATOS = RAIZ / "data" / "raw" / "data.csv"
RUTA_PARTICION = RAIZ / "data" / "procesados" / "particion.csv"
REPORTES = RAIZ / "reportes"
FIGURAS = REPORTES / "figuras"
MINIMO_CASOS = 10

# Paleta de referencia (validada: azul y naranja pasan los controles de visión de colores)
AZUL, NARANJA = "#2a78d6", "#eb6834"
GRIS_TEXTO, GRIS_SECUNDARIO, GRILLA, FONDO = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
DIVERGENTE = LinearSegmentedColormap.from_list("divergente", ["#2a78d6", "#f0efec", "#e34948"])

ETIQUETA_SITUACION = {"abandono": "Abandono", "cursando": "Sigue cursando", "graduado": "Graduado"}


def _estilo() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": FONDO,
            "axes.facecolor": FONDO,
            "axes.edgecolor": GRILLA,
            "axes.labelcolor": GRIS_SECUNDARIO,
            "axes.titlecolor": GRIS_TEXTO,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": GRILLA,
            "grid.linewidth": 0.8,
            "xtick.color": GRIS_SECUNDARIO,
            "ytick.color": GRIS_SECUNDARIO,
            "font.size": 10,
            "legend.frameon": False,
        }
    )


_FMT_PCT = FuncFormatter(lambda v, _: F.porcentaje(v, 0))
_FMT_DEC = FuncFormatter(lambda v, _: F.decimal(v, 2).rstrip("0").rstrip(","))


def figura_situacion_final(dist: pd.DataFrame, ruta) -> None:
    fig, ax = plt.subplots(figsize=(7, 2.6))
    orden = ["graduado", "cursando", "abandono"]
    colores = [AZUL, AZUL, NARANJA]
    ax.barh([ETIQUETA_SITUACION[s] for s in orden], dist.loc[orden, "casos"], color=colores, height=0.55)
    for i, s in enumerate(orden):
        ax.text(
            dist.loc[s, "casos"] + 15,
            i,
            f"{F.entero(dist.loc[s, 'casos'])} ({F.porcentaje(dist.loc[s, 'proporcion'])})",
            va="center",
            color=GRIS_TEXTO,
        )
    ax.set_xlim(0, dist["casos"].max() * 1.3)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Estudiantes (entrenamiento)")
    ax.set_title("Situación final en entrenamiento", loc="left", pad=28)
    ax.legend(
        handles=[plt.Rectangle((0, 0), 1, 1, color=NARANJA), plt.Rectangle((0, 0), 1, 1, color=AZUL)],
        labels=["Abandono (1)", "No abandono (0)"],
        loc="lower right",
        bbox_to_anchor=(1, 1.02),
        ncol=2,
    )
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def figura_abandono_por_aprobadas(tabla: pd.DataFrame, ruta) -> None:
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.bar([str(i) for i in tabla.index], tabla["tasa"], color=AZUL, width=0.6)
    ax.yaxis.set_major_formatter(_FMT_PCT)
    ax.set_ylim(0, 1)
    ax.grid(axis="x", visible=False)
    ax.set_xlabel("Materias aprobadas en el 1.er semestre")
    ax.set_ylabel("Abandono observado")
    ax.set_title("Abandono observado por materias aprobadas (entrenamiento)", loc="left")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def figura_correlaciones(matriz: pd.DataFrame, ruta) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 7.5))
    imagen = ax.imshow(matriz.to_numpy(), cmap=DIVERGENTE, vmin=-1, vmax=1)
    ax.set_xticks(range(len(matriz)), matriz.columns, rotation=90)
    ax.set_yticks(range(len(matriz)), matriz.index)
    ax.grid(visible=False)
    barra = fig.colorbar(imagen, ax=ax, shrink=0.75, ticks=[-1, -0.5, 0, 0.5, 1])
    barra.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: F.decimal(v, 1)))
    barra.set_label("Correlación de Spearman")
    ax.set_title("Correlaciones de Spearman (entrenamiento)", loc="left")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def figura_edad_y_nota(ent: pd.DataFrame, ruta) -> None:
    fig, ejes = plt.subplots(1, 2, figsize=(9, 3.2))
    paneles = [
        ("edad_ingreso", "Edad al ingresar", np.arange(16.5, 61.5, 2)),
        ("nota_promedio_s1", "Nota promedio del 1.er semestre (0 a 20)", np.arange(0, 20.5, 1)),
    ]
    for ax, (variable, titulo, bordes) in zip(ejes, paneles, strict=True):
        for valor, color, etiqueta in ((0, AZUL, "No abandono"), (1, NARANJA, "Abandono")):
            datos = ent.loc[ent[P.OBJETIVO_BINARIO] == valor, variable].clip(upper=bordes[-1] - 0.01)
            ax.hist(datos, bins=bordes, density=True, histtype="step", linewidth=2, color=color, label=etiqueta)
        ax.set_title(titulo, loc="left", fontsize=11)
        ax.set_ylabel("Densidad")
        ax.yaxis.set_major_formatter(_FMT_DEC)
        ax.grid(axis="x", visible=False)
    ejes[0].legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def _tabla(encabezado: list[str], filas: list[list[str]]) -> list[str]:
    lineas = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    lineas += ["| " + " | ".join(f) + " |" for f in filas]
    return lineas


def main() -> int:
    _estilo()
    df = P.cargar_dataset(RUTA_DATOS)
    conjunto = P.cargar_particion(RUTA_PARTICION)
    ent = X.datos_para_explorar(df, conjunto)
    completo_sin_objetivo = X.sin_objetivo(df)
    FIGURAS.mkdir(parents=True, exist_ok=True)

    todas = V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_2S]
    tipos = P.columnas_del_momento(V.Momento.CIERRE_2S)
    numericas, categoricas, binarias = tipos["numericas"], tipos["categoricas"], tipos["binarias"]
    hoy = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))

    calidad = X.controles_calidad(completo_sin_objetivo, todas)
    dist_ent = X.distribucion_situacion_final(ent)
    peso = X.peso_clase_positiva(ent)
    resumen_num = X.resumen_numericas(ent, numericas)
    resumen_cat = X.resumen_categoricas(ent, categoricas, MINIMO_CASOS)
    raras = X.categorias_poco_frecuentes(ent, categoricas, MINIMO_CASOS)
    matriz = X.correlaciones(ent, numericas)
    con_abandono = matriz[X.OBJETIVO_BINARIO].drop(X.OBJETIVO_BINARIO)
    pares = X.pares_muy_correlacionados(matriz, 0.8)

    aprobadas = ent["materias_aprobadas_s1"].clip(upper=10).astype(int)
    tabla_aprobadas = X.tasa_abandono_por(ent, aprobadas.rename("aprobadas"))
    tabla_aprobadas.index = [("10 o más" if i == 10 else str(i)) for i in tabla_aprobadas.index]
    sin_inscriptas = ent[ent["materias_inscriptas_s1"] == 0]
    sin_inscriptas_situacion = sin_inscriptas[V.OBJETIVO].value_counts()
    sin_inscriptas_df = completo_sin_objetivo[completo_sin_objetivo["materias_inscriptas_s1"] == 0]
    sin_inscriptas_completo = len(sin_inscriptas_df)
    columnas_semestre = list(V.VARIABLES_SEMESTRE_1) + list(V.VARIABLES_SEMESTRE_2)
    todo_cero = int((sin_inscriptas_df[columnas_semestre] == 0).all(axis=1).sum())
    carreras_sin = sin_inscriptas_df["carrera"].value_counts()
    carrera_principal = int(carreras_sin.index[0])
    total_carrera = int((completo_sin_objetivo["carrera"] == carrera_principal).sum())

    figura_situacion_final(dist_ent, FIGURAS / "situacion_final.png")
    figura_abandono_por_aprobadas(tabla_aprobadas, FIGURAS / "abandono_por_aprobadas_s1.png")
    figura_correlaciones(matriz, FIGURAS / "correlaciones.png")
    figura_edad_y_nota(ent, FIGURAS / "edad_y_nota_s1.png")

    L: list[str] = [
        "# Informe exploratorio de los datos",
        "",
        f"Generado por `scripts/explorar_datos.py` el {F.fecha_hora(hoy)} (tarea 2.1; CRISP-DM, fase 2).",
        "",
        "**Qué datos se miran.** Todo lo que relaciona una variable con el abandono se calcula solo con",
        f"el conjunto de **entrenamiento** ({F.entero(len(ent))} estudiantes de la partición fija 60/20/20).",
        "Los controles de calidad que no usan la situación final (faltantes, rangos) se hacen sobre el",
        f"archivo completo ({F.entero(len(df))} registros) sin la variable objetivo. El conjunto de prueba",
        "no se usa en este informe.",
        "",
        "## 1. Archivo y controles de calidad",
        "",
        f"- Fuente: Realinho et al. (2021), UCI, archivo `data/raw/data.csv`: {F.entero(len(df))} registros",
        f"  y {V.COLUMNAS_ORIGINALES_ESPERADAS} columnas (36 predictoras y la situación final).",
        f"- Valores faltantes en las {len(todas)} variables del modelo: "
        f"**{int(calidad['faltantes'].sum())}**.",
        "- Los códigos de las variables categóricas son los **originales de UCI** (carrera de 33 a 9991,",
        "  ocupaciones de 0 a 195), no los correlativos del anexo del artículo (decisión P10). La",
        "  correspondencia está en `docs/datos/anexo-codigos-realinho-2022.md`.",
        "",
        "Rango de las variables numéricas (archivo completo):",
        "",
    ]
    L += _tabla(
        ["Variable", "Mínimo", "Máximo", "Valores distintos"],
        [
            [f"`{v}`", F.decimal(calidad.loc[v, "minimo"], 2), F.decimal(calidad.loc[v, "maximo"], 2),
             F.entero(calidad.loc[v, "distintos"])]
            for v in numericas
        ],
    )
    L += [
        "",
        "## 2. Variable objetivo y desbalance de clases",
        "",
        "Archivo completo (distribución publicada, Realinho et al., 2022, p. 7): graduado 2.209 (49,9 %),",
        "abandono 1.421 (32,1 %) y sigue cursando 794 (17,9 %).",
        "",
        "En entrenamiento:",
        "",
    ]
    L += _tabla(
        ["Situación final", "Valor binario", "Casos", "Proporción"],
        [
            [ETIQUETA_SITUACION[s], "1" if s == "abandono" else "0", F.entero(dist_ent.loc[s, "casos"]),
             F.porcentaje(dist_ent.loc[s, "proporcion"])]
            for s in dist_ent.index
        ],
    )
    L += [
        "",
        "![Situación final en entrenamiento](figuras/situacion_final.png)",
        "",
        f"La clase positiva (abandono) es el {F.porcentaje(ent[P.OBJETIVO_BINARIO].mean())} de entrenamiento:",
        f"hay {F.decimal(peso, 3)} no abandonos por cada abandono. Ese cociente es el `scale_pos_weight` de",
        "XGBoost; la regresión logística usa `class_weight=\"balanced\"`. No se generan casos sintéticos.",
        "«Sigue cursando» se agrupa con «graduado» como no abandono; por eso la evaluación final informa",
        "también el AUC-ROC sin quienes siguen cursando.",
        "",
        "## 3. Variables por momento de predicción y exclusiones",
        "",
    ]
    L += _tabla(
        ["Momento", "Variables", "Agrega"],
        [
            [V.ETIQUETA_MOMENTO[V.Momento.INSCRIPCION], "19", "demográficas, socioeconómicas, macroeconómicas y académicas de la inscripción"],
            [V.ETIQUETA_MOMENTO[V.Momento.CIERRE_1S], "25", "las seis de rendimiento del 1.er semestre (`_s1`)"],
            [V.ETIQUETA_MOMENTO[V.Momento.CIERRE_2S], "31", "las seis de rendimiento del 2.º semestre (`_s2`)"],
        ],
    )
    L += ["", "Variables excluidas (se descartan en la carga y no entran a ningún modelo):", ""]
    L += _tabla(["Variable", "Motivo"], [[f"`{v}`", motivo] for v, (_, motivo) in V.VARIABLES_EXCLUIDAS.items()])
    L += [
        "",
        "## 4. Variables numéricas (entrenamiento)",
        "",
    ]
    L += _tabla(
        ["Variable", "Media", "Desvío", "Mediana", "Media en abandono", "Media en no abandono"],
        [
            [f"`{v}`", F.decimal(r.media, 2), F.decimal(r.desvio, 2), F.decimal(r.mediana, 2),
             F.decimal(r.media_abandono, 2), F.decimal(r.media_no_abandono, 2)]
            for v, r in resumen_num.iterrows()
        ],
    )
    L += [
        "",
        "![Edad y nota del 1.er semestre según el abandono](figuras/edad_y_nota_s1.png)",
        "",
        "## 5. Variables categóricas (entrenamiento)",
        "",
        f"Se codifican con one-hot ajustado solo con entrenamiento. Categorías con menos de {MINIMO_CASOS}",
        "casos:",
        "",
    ]
    L += _tabla(
        ["Variable", "Categorías", f"Con < {MINIMO_CASOS} casos", "Estudiantes en ellas", "Más frecuente"],
        [
            [f"`{v}`", str(int(r.categorias)), str(int(r.poco_frecuentes)), str(int(r.casos_en_poco_frecuentes)),
             f"{texto_valor(v, {v: int(r.mas_frecuente)})} ({F.porcentaje(r.proporcion_mas_frecuente)})"]
            for v, r in resumen_cat.iterrows()
        ],
    )
    L += [
        "",
        f"En total hay {len(raras)} categorías con menos de {MINIMO_CASOS} casos, que reúnen a "
        f"{F.entero(raras['casos'].sum())} estudiantes ({F.porcentaje(raras['casos'].sum() / len(ent))} de",
        "entrenamiento). **Decisión:** no se agrupan ni se descartan. Cada una genera una columna one-hot",
        "con pocos casos, que la regresión logística regulariza y que XGBoost casi no usa para dividir;",
        "una categoría que no aparece en entrenamiento queda en cero (`handle_unknown=\"ignore\"`), así que",
        "no rompe la predicción de estudiantes nuevos. Agrupar requeriría criterios por variable que el",
        "documento no fija.",
        "",
        "## 6. Variables binarias y edad de ingreso (entrenamiento)",
        "",
    ]
    filas_bin = []
    for v in binarias:
        tabla = X.tasa_abandono_por(ent, v)
        for valor, r in tabla.iterrows():
            filas_bin.append([NOMBRES[v], texto_valor(v, {v: valor}), F.entero(r.casos), F.porcentaje(r.tasa)])
    tabla_edad = X.tasa_abandono_por(ent, X.tramos_de_edad(ent)).reindex([c[0] for c in V.CORTES_EDAD])
    for tramo, r in tabla_edad.iterrows():
        filas_bin.append(["Edad al ingresar", tramo, F.entero(r.casos), F.porcentaje(r.tasa)])
    L += _tabla(["Variable", "Valor", "Casos", "Abandono observado"], filas_bin)
    L += [
        "",
        "Género, edad y condición de becario son además los subgrupos de la evaluación de sesgos",
        "(evaluación final, solo con el modelo del cierre del 1.er semestre).",
        "",
        "## 7. Rendimiento del 1.er semestre (entrenamiento)",
        "",
        "![Abandono según materias aprobadas en el 1.er semestre](figuras/abandono_por_aprobadas_s1.png)",
        "",
    ]
    L += _tabla(
        ["Materias aprobadas (1.er semestre)", "Casos", "Abandonos", "Abandono observado"],
        [[str(i), F.entero(r.casos), F.entero(r.abandonos), F.porcentaje(r.tasa)] for i, r in tabla_aprobadas.iterrows()],
    )
    L += [
        "",
        f"**Estudiantes con 0 materias inscriptas en el 1.er semestre:** {sin_inscriptas_completo} en el archivo",
        f"completo y {len(sin_inscriptas)} en entrenamiento ("
        + ", ".join(
            f"{ETIQUETA_SITUACION[s].lower()} {int(sin_inscriptas_situacion.get(s, 0))}"
            for s in ("abandono", "cursando", "graduado")
        )
        + ").",
        f"En el archivo completo, {todo_cero} de los {sin_inscriptas_completo} tienen en cero **las doce** variables",
        f"de rendimiento (1.er y 2.º semestre) y {int(carreras_sin.iloc[0])} pertenecen a una sola carrera, "
        f"{texto_valor('carrera', {'carrera': carrera_principal})}",
        f"(código {carrera_principal}), que tiene {total_carrera} estudiantes en total "
        f"({F.porcentaje(int(carreras_sin.iloc[0]) / total_carrera)} de ellos sin datos de rendimiento),",
        f"repartidos en {sin_inscriptas_df['tasa_desempleo'].nunique()} de los "
        f"{completo_sin_objetivo['tasa_desempleo'].nunique()} años de ingreso. Con graduados entre ellos, no es un abandono",
        "temprano: lo más probable es que **falte el registro de rendimiento de esa carrera** en la",
        "fuente, y que el cero signifique «sin dato» y no «no aprobó nada».",
        "",
        "**Decisión:** se mantienen sin cambios. Las listas de variables y el modelo de `cierre_1s` (v1.0,",
        "congelado para el cuestionario) ya se construyeron así, y el preprocesamiento no inventa valores.",
        "El modelo puede aprender la combinación «esa carrera con todo en cero», por lo que sus",
        "estimaciones para esa carrera en los cierres de semestre son menos confiables. Queda como",
        "limitación para el documento. En la ficha se muestran como «sin materias inscriptas» (tarea 6.2).",
        "",
        "## 8. Correlaciones (entrenamiento)",
        "",
        "Correlación de Spearman (no supone relación lineal y tolera valores extremos).",
        "",
        "![Correlaciones](figuras/correlaciones.png)",
        "",
        "Variables numéricas con mayor correlación con el abandono (en valor absoluto):",
        "",
    ]
    top = con_abandono.reindex(con_abandono.abs().sort_values(ascending=False).index).head(10)
    L += _tabla(["Variable", "Correlación con el abandono"], [[f"`{v}`", F.decimal(r, 3)] for v, r in top.items()])
    L += ["", f"Pares de variables con |correlación| ≥ 0,8 ({len(pares)}):", ""]
    if len(pares):
        L += _tabla(
            ["Variable", "Variable", "Correlación"],
            [[f"`{r.variable_a}`", f"`{r.variable_b}`", F.decimal(r.rho, 3)] for r in pares.itertuples()],
        )
    else:
        L += ["Ninguno."]
    L += [
        "",
        "Los pares muy correlacionados son la misma variable de rendimiento en el 1.er y en el 2.º",
        "semestre. Solo conviven en el modelo del cierre del 2.º semestre. **Decisión:** se mantienen",
        "todas, porque las listas de cada momento las fija",
        "el documento y el objetivo es estimar el riesgo, no interpretar coeficientes. La correlación sí",
        "importa al leer las explicaciones: dos variables muy correlacionadas se reparten el peso en SHAP.",
        "",
        "## 9. Variables macroeconómicas",
        "",
    ]
    macro = ["tasa_desempleo", "tasa_inflacion", "variacion_pib"]
    combinaciones = ent[macro].drop_duplicates().sort_values("tasa_desempleo")
    tabla_macro = X.tasa_abandono_por(ent, macro)
    L += [
        f"Toman {len(combinaciones)} combinaciones distintas, una por año de ingreso. En entrenamiento:",
        "",
    ]
    L += _tabla(
        ["Desempleo", "Inflación", "Variación del PIB", "Casos", "Abandono observado"],
        [
            [F.decimal(d, 1), F.decimal(i, 1), F.decimal(g, 2), F.entero(r.casos), F.porcentaje(r.tasa)]
            for (d, i, g), r in tabla_macro.iterrows()
        ],
    )
    L += [
        "",
        "Funcionan como un indicador del año de ingreso. **Decisión (P9, confirmada el 03/11):** se",
        "mantienen, porque el documento las incluye en la lista de 19 variables de inscripción y la",
        "plataforma las puede completar con los indicadores del año. Limitación: con solo diez años, el",
        "modelo puede asociar un año puntual con más abandono sin que el indicador económico sea la razón.",
        "",
        "## 10. Conclusiones para la preparación",
        "",
        "- Variable objetivo binaria: abandono = 1; graduado o sigue cursando = 0.",
        f"- Desbalance moderado ({F.porcentaje(ent[P.OBJETIVO_BINARIO].mean())} de abandono): pesos de clase,",
        "  sin casos sintéticos.",
        "- Sin valores faltantes: no hace falta imputar.",
        "- Categóricas con one-hot (`handle_unknown=\"ignore\"`), numéricas estandarizadas y binarias sin",
        "  cambios, todo ajustado solo con entrenamiento dentro del `Pipeline`.",
        "- Se mantienen las 31 variables del documento (19, 25 y 31 por momento) y las cinco exclusiones.",
        "- Las variables de rendimiento del semestre son las que más se relacionan con el abandono, lo que",
        "  anticipa que el modelo de inscripción va a rendir bastante menos que los de cierre de semestre.",
    ]
    (REPORTES / "informe_exploratorio.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Informe en reportes/informe_exploratorio.md; figuras en {FIGURAS.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
