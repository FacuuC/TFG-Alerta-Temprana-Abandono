# Datos

| Carpeta | Contenido | ¿Se versiona? | Cómo se genera |
|---|---|---|---|
| `raw/` | `data.csv` (UCI), `uci_metadata.json`, `fuente.json` (huella y verificación) | No | `python scripts/descargar_datos.py` |
| `procesados/` | `particion.csv`: partición 60/20/20 estratificada con semilla 42, la misma para los tres momentos. Solo tiene `indice_original` y `conjunto`, **sin la variable objetivo** | Sí (`particion.csv`) | `python scripts/preparar_particion.py` (no modifica una partición que ya existe) |
| `cargas/` | `exportacion_inscripcion.csv`, `exportacion_cierre_1s.csv`, `exportacion_cierre_2s.csv`: los archivos de carga simulados, uno por momento de predicción | Sí | `python scripts/generar_cargas.py` (decisión P2) |

**Fuente y cambios (CC BY 4.0).** El dataset es de Realinho, V., Vieira Martins, M.,
Machado, J. y Baptista, L. (2021). *Predict students' dropout and academic success*
[Conjunto de datos]. UCI Machine Learning Repository. https://doi.org/10.24432/C5MC89.
Licencia CC BY 4.0. Es público y está anonimizado.

Los archivos de `cargas/` son **derivados del conjunto de prueba de Realinho et al. (2021),
con licencia CC BY 4.0. Se agregaron identificadores sintéticos y se quitó la situación
final.** En detalle:

- solo los 885 estudiantes del conjunto de prueba de la partición;
- columnas con los nombres de la plataforma, separadas por «;», UTF-8 y con punto decimal;
- identificadores **sintéticos** agregados (`legajo`, `documento` y `apellido_nombre`),
  constantes entre los tres archivos, que la plataforma descarta al cargar;
- sin la situación final (`Target`), porque el dataset se lee sin esa columna;
- cada archivo trae todo lo disponible hasta su momento (el de inscripción, sin datos de
  los semestres);
- se mantienen las cinco variables excluidas, para mostrar que la carga las descarta.

Los dos archivos que se versionan (la partición y las cargas) están en el repositorio para
que un clon nuevo pueda instalar y usar la demo solo con Docker, sin Python ni el dataset.
