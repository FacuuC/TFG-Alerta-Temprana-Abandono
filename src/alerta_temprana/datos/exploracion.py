"""Análisis exploratorio (CRISP-DM, fase 2; tarea 2.1).

Todo lo que relaciona variables con el abandono se calcula SOLO con el conjunto de
entrenamiento (`datos_para_explorar`), para que ninguna decisión del modelo dependa de
validación ni de prueba. Los controles de calidad que no usan la variable objetivo
(faltantes, rangos, valores distintos) pueden hacerse sobre el archivo completo.
"""

from __future__ import annotations

import pandas as pd

from alerta_temprana.datos import variables as V

OBJETIVO_BINARIO = "abandono"  # igual a preparacion.OBJETIVO_BINARIO (sin importar el módulo del modelo)


def datos_para_explorar(df: pd.DataFrame, conjunto: pd.Series) -> pd.DataFrame:
    """Solo las filas de entrenamiento de la partición guardada."""
    return df.loc[conjunto[conjunto == "entrenamiento"].index]


def sin_objetivo(df: pd.DataFrame) -> pd.DataFrame:
    """El archivo sin la situación final ni la variable binaria (para controles de calidad)."""
    return df.drop(columns=[c for c in (V.OBJETIVO, OBJETIVO_BINARIO) if c in df.columns])


def controles_calidad(df: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Faltantes, mínimo, máximo y cantidad de valores distintos por variable."""
    filas = [
        {
            "variable": v,
            "faltantes": int(df[v].isna().sum()),
            "minimo": float(df[v].min()),
            "maximo": float(df[v].max()),
            "distintos": int(df[v].nunique()),
        }
        for v in variables
    ]
    return pd.DataFrame(filas).set_index("variable")


def distribucion_situacion_final(df: pd.DataFrame) -> pd.DataFrame:
    """Casos y proporción de cada situación final (abandono, cursando, graduado)."""
    casos = df[V.OBJETIVO].value_counts().reindex(["abandono", "cursando", "graduado"], fill_value=0)
    return pd.DataFrame({"casos": casos, "proporcion": casos / casos.sum()})


def peso_clase_positiva(df: pd.DataFrame) -> float:
    """Negativos / positivos: el `scale_pos_weight` de XGBoost."""
    y = df[OBJETIVO_BINARIO]
    return float((y == 0).sum() / (y == 1).sum())


def resumen_numericas(df: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Media, desvío, mínimo, mediana y máximo, más la media en abandono y en no abandono."""
    resumen = df[variables].agg(["mean", "std", "min", "median", "max"]).T
    resumen.columns = ["media", "desvio", "minimo", "mediana", "maximo"]
    medias = df.groupby(OBJETIVO_BINARIO)[variables].mean().T
    resumen["media_abandono"] = medias.get(1)
    resumen["media_no_abandono"] = medias.get(0)
    return resumen


def categorias_poco_frecuentes(df: pd.DataFrame, variables: list[str], minimo: int = 10) -> pd.DataFrame:
    """Categorías con menos de `minimo` casos (variable, código, casos)."""
    filas = []
    for v in variables:
        conteo = df[v].value_counts()
        for codigo, casos in conteo[conteo < minimo].sort_index().items():
            filas.append({"variable": v, "codigo": int(codigo), "casos": int(casos)})
    return pd.DataFrame(filas, columns=["variable", "codigo", "casos"])


def resumen_categoricas(df: pd.DataFrame, variables: list[str], minimo: int = 10) -> pd.DataFrame:
    """Por variable: categorías distintas, cuántas tienen menos de `minimo` casos y la más frecuente."""
    filas = []
    for v in variables:
        conteo = df[v].value_counts()
        filas.append(
            {
                "variable": v,
                "categorias": int(conteo.size),
                "poco_frecuentes": int((conteo < minimo).sum()),
                "casos_en_poco_frecuentes": int(conteo[conteo < minimo].sum()),
                "mas_frecuente": int(conteo.index[0]),
                "proporcion_mas_frecuente": float(conteo.iloc[0] / conteo.sum()),
            }
        )
    return pd.DataFrame(filas).set_index("variable")


def tasa_abandono_por(df: pd.DataFrame, agrupador: str | pd.Series) -> pd.DataFrame:
    """Casos, abandonos y tasa de abandono por valor de una variable (o de una serie agrupadora)."""
    grupos = df.groupby(agrupador)[OBJETIVO_BINARIO]
    return pd.DataFrame({"casos": grupos.size(), "abandonos": grupos.sum(), "tasa": grupos.mean()})


def tramos_de_edad(df: pd.DataFrame) -> pd.Series:
    return df["edad_ingreso"].map(V.tramo_edad).rename("tramo_edad")


def correlaciones(df: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Matriz de correlación de Spearman entre las variables y el abandono (al final)."""
    return df[variables + [OBJETIVO_BINARIO]].corr(method="spearman")


def pares_muy_correlacionados(matriz: pd.DataFrame, umbral: float = 0.8) -> pd.DataFrame:
    """Pares de variables distintas con |rho| >= umbral (sin contar el abandono)."""
    variables = [c for c in matriz.columns if c != OBJETIVO_BINARIO]
    filas = []
    for i, a in enumerate(variables):
        for b in variables[i + 1 :]:
            rho = float(matriz.loc[a, b])
            if abs(rho) >= umbral:
                filas.append({"variable_a": a, "variable_b": b, "rho": rho})
    resultado = pd.DataFrame(filas, columns=["variable_a", "variable_b", "rho"])
    return resultado.reindex(resultado["rho"].abs().sort_values(ascending=False).index)


def disponibilidad_por_momento() -> pd.DataFrame:
    """Para cada variable, en qué momentos de predicción está disponible."""
    todas = V.VARIABLES_POR_MOMENTO[V.Momento.CIERRE_2S]
    return pd.DataFrame(
        {m.value: [v in V.VARIABLES_POR_MOMENTO[m] for v in todas] for m in V.Momento}, index=todas
    )
