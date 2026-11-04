# Datos (no se versionan)

| Carpeta | Contenido | Cómo se genera |
|---|---|---|
| `raw/` | `data.csv` (UCI), `uci_metadata.json`, `fuente.json` (huella y verificación) | `python scripts/descargar_datos.py` |
| `procesados/` | `particion.csv` (60/20/20, semilla fija) y otros intermedios | Scripts de HU-002 |
| `cargas/` | Archivos de exportación simulados, uno por momento (estudiantes de prueba) | Script de HU-001 |

El dataset es público (CC BY 4.0) y está anonimizado. Los identificadores de los archivos
de carga (legajo, documento, nombre) son sintéticos.
