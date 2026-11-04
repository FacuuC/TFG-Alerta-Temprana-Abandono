"""Descarga y verifica el conjunto de datos de Realinho et al. (2021) desde UCI.

Uso:
    python scripts/descargar_datos.py            # descarga si falta y verifica
    python scripts/descargar_datos.py --forzar   # vuelve a descargar

Resultado en data/raw/:
    data.csv           archivo original de UCI (separado por «;»)
    uci_metadata.json  metadatos de UCI con la descripción y los códigos de cada variable
    fuente.json        URL, fecha, huella SHA-256, filas, columnas, distribución y
                       valores distintos de las variables codificadas

Solo usa la biblioteca estándar, así que funciona antes de instalar dependencias.
Fuente: Realinho, V., Vieira Martins, M., Machado, J. y Baptista, L. (2021).
Predict students' dropout and academic success [Conjunto de datos]. UCI Machine
Learning Repository. https://doi.org/10.24432/C5MC89 (licencia CC BY 4.0).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from alerta_temprana.datos import variables as V  # noqa: E402  (sin dependencias externas)

DESTINO = RAIZ / "data" / "raw"
URL_ZIP = "https://archive.ics.uci.edu/static/public/697/predict+students+dropout+and+academic+success.zip"
URL_METADATOS = "https://archive.ics.uci.edu/api/dataset?id=697"
DOI = "https://doi.org/10.24432/C5MC89"
CABECERAS = {"User-Agent": "tfg-alerta-temprana/0.1 (descarga del dataset para investigación)"}


def _bajar(url: str) -> bytes:
    pedido = urllib.request.Request(url, headers=CABECERAS)
    with urllib.request.urlopen(pedido, timeout=60) as respuesta:
        return respuesta.read()


def descargar_csv(destino: Path) -> None:
    print(f"Descargando {URL_ZIP} ...")
    contenido = _bajar(URL_ZIP)
    with zipfile.ZipFile(io.BytesIO(contenido)) as archivo_zip:
        csvs = [n for n in archivo_zip.namelist() if n.lower().endswith(".csv")]
        if len(csvs) != 1:
            raise SystemExit(f"Se esperaba un único CSV dentro del zip y se encontró: {csvs}")
        destino.write_bytes(archivo_zip.read(csvs[0]))
    print(f"Guardado en {destino.relative_to(RAIZ)}")


def descargar_metadatos(destino: Path) -> None:
    try:
        datos = json.loads(_bajar(URL_METADATOS))
        destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Metadatos guardados en {destino.relative_to(RAIZ)}")
    except Exception as error:  # los metadatos ayudan, pero no son imprescindibles
        print(f"AVISO: no se pudieron bajar los metadatos de UCI ({error}). Se puede seguir sin ellos.")


def verificar(ruta_csv: Path) -> dict:
    texto = ruta_csv.read_text(encoding="utf-8-sig")
    separador = ";" if texto.splitlines()[0].count(";") > texto.splitlines()[0].count(",") else ","
    filas = list(csv.reader(io.StringIO(texto), delimiter=separador))
    encabezado, registros = filas[0], [f for f in filas[1:] if f]

    problemas: list[str] = []
    if len(encabezado) != V.COLUMNAS_ORIGINALES_ESPERADAS:
        problemas.append(f"columnas: {len(encabezado)} (se esperaban {V.COLUMNAS_ORIGINALES_ESPERADAS})")
    if len(registros) != V.REGISTROS_ESPERADOS:
        problemas.append(f"registros: {len(registros)} (se esperaban {V.REGISTROS_ESPERADOS})")

    try:
        renombre = V.renombrar_columnas(encabezado)
    except ValueError as error:
        problemas.append(str(error))
        renombre = {}

    indice = {nombre: i for i, nombre in enumerate(encabezado)}
    columna_objetivo = next((c for c in encabezado if V.normalizar_nombre(c) == V.OBJETIVO_ORIGINAL), None)
    distribucion = Counter(r[indice[columna_objetivo]] for r in registros) if columna_objetivo else Counter()
    if dict(distribucion) != V.DISTRIBUCION_ESPERADA:
        problemas.append(
            f"distribución de Target: {dict(distribucion)} (se esperaba {V.DISTRIBUCION_ESPERADA})"
        )

    # Valores distintos de las variables codificadas: muestran si el archivo usa los
    # códigos del anexo del artículo (1 a 17 en carrera) o los códigos originales.
    valores_codificados = {}
    for original, nuevo in renombre.items():
        if nuevo in V.CATEGORICAS:
            valores = sorted({r[indice[original]] for r in registros}, key=lambda v: float(v))
            valores_codificados[nuevo] = valores

    return {
        "separador": separador,
        "columnas": len(encabezado),
        "registros": len(registros),
        "encabezado_original": encabezado,
        "distribucion_target": dict(distribucion),
        "valores_codificados": valores_codificados,
        "problemas": problemas,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--forzar", action="store_true", help="volver a descargar aunque el archivo exista")
    args = parser.parse_args()

    DESTINO.mkdir(parents=True, exist_ok=True)
    ruta_csv = DESTINO / "data.csv"
    if args.forzar or not ruta_csv.exists():
        descargar_csv(ruta_csv)
    else:
        print(
            f"{ruta_csv.relative_to(RAIZ)} ya existe; se verifica sin descargar (usá --forzar para bajarlo de nuevo)."
        )
    ruta_meta = DESTINO / "uci_metadata.json"
    if args.forzar or not ruta_meta.exists():
        descargar_metadatos(ruta_meta)

    resultado = verificar(ruta_csv)
    resultado.update(
        {
            "fuente": URL_ZIP,
            "doi": DOI,
            "licencia": "CC BY 4.0",
            "sha256": hashlib.sha256(ruta_csv.read_bytes()).hexdigest(),
            "verificado": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    )
    (DESTINO / "fuente.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        f"\nRegistros: {resultado['registros']}  Columnas: {resultado['columnas']}  Separador: «{resultado['separador']}»"
    )
    print(f"Distribución de Target: {resultado['distribucion_target']}")
    print(f"SHA-256: {resultado['sha256']}")
    print(f"Valores de carrera en el archivo: {resultado['valores_codificados'].get('carrera')}")
    if resultado["problemas"]:
        print("\nPROBLEMAS ENCONTRADOS:")
        for problema in resultado["problemas"]:
            print(f"  - {problema}")
        return 1
    print("\nOK: el archivo coincide con lo descripto en el documento (4.424 registros, 37 columnas).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
