"""Controles sobre el archivo descargado de UCI (se omiten si todavía no se descargó)."""

import pytest

from alerta_temprana.datos import variables as V

pytestmark = pytest.mark.datos


def test_dataset_tiene_la_forma_documentada(ruta_dataset):
    import pandas as pd

    df = pd.read_csv(ruta_dataset, sep=";")
    assert df.shape == (V.REGISTROS_ESPERADOS, V.COLUMNAS_ORIGINALES_ESPERADAS)
    df = df.rename(columns=V.renombrar_columnas(list(df.columns)))
    assert df[V.OBJETIVO].value_counts().to_dict() == V.DISTRIBUCION_ESPERADA
    assert not df.isna().any().any()
