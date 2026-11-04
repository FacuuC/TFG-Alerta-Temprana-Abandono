# Datos

## Conjunto de datos

- **Fuente:** Realinho, V., Vieira Martins, M., Machado, J. y Baptista, L. (2021).
  *Predict students' dropout and academic success* [Conjunto de datos]. UCI Machine
  Learning Repository. https://doi.org/10.24432/C5MC89. Licencia CC BY 4.0.
- **Artículo que lo describe:** Realinho et al. (2022), *Data*, 7(11), 146.
- **Origen:** estudiantes de grado del Instituto Politécnico de Portalegre (Portugal) que
  ingresaron entre 2008/2009 y 2018/2019. Anonimizado (RGPD).
- **Archivo:** `data/raw/data.csv` (separado por «;»), **4.424 registros, 36 predictoras +
  Target = 37 columnas**. Se descarga y verifica con `python scripts/descargar_datos.py`,
  que deja la huella SHA-256 y los valores de las variables codificadas en
  `data/raw/fuente.json`.
- **Situación final (Target):** graduado 2.209 (50 %), abandono 1.421 (32 %), sigue
  cursando 794 (18 %) (Realinho et al., 2022, p. 7). El abandono se define desde la
  institución e incluye los cambios de carrera o de institución (p. 1).
- El artículo informa 35 atributos (p. 2) porque su tabla 1 no incluye la nota del título
  previo ni la nota de admisión, que la versión de UCI agrega.

### Detalles del archivo que conviene saber

- El encabezado de «Daytime/evening attendance» termina en un **tabulador**.
- La nacionalidad se llama **«Nacionality»** (errata del original).
- Las mayúsculas pueden variar entre versiones («Marital status» / «Marital Status»).
- `variables.renombrar_columnas()` resuelve las tres cosas.
- **Códigos (verificado el 03/11):** el archivo usa los códigos originales (carrera 33,
  171, …, 9991), no los correlativos del anexo del artículo. La correspondencia con las
  etiquetas está en `../datos/anexo-codigos-realinho-2022.md`; para padres y madres,
  `data/raw/uci_metadata.json` trae la descripción oficial de UCI.
- **Datos observados (03/11):** sin valores faltantes en los controles; edad de 17 a 70;
  nota del título previo de 95 a 190; nota del semestre de 0 a 18,9; las macroeconómicas
  toman 10 valores distintos (uno por año de ingreso); 180 estudiantes tienen 0 materias
  inscriptas en el 1.er semestre (77 abandonan, 75 se gradúan, 28 siguen cursando),
  revisarlo en el análisis exploratorio.

## Variable objetivo

| Original | En la plataforma | Modelo |
|---|---|---|
| Dropout | `abandono` | 1 |
| Enrolled | `cursando` («sigue cursando») | 0 |
| Graduate | `graduado` | 0 |

Se informa además el AUC-ROC calculado **sin** quienes siguen cursando (control de la
etiqueta, observación 16). Limitaciones declaradas: abandonos posteriores al período
observado, falta del momento del abandono y abandono definido desde la institución.

## Variables excluidas (5)

| Variable original | Nombre | Motivo |
|---|---|---|
| Educational special needs | necesidades_especiales | Dato sensible: puede revelar información de salud (Ley 25.326, arts. 2 y 7) |
| Debtor | deudor | Sin equivalente: el grado es gratuito (Ley 24.521, art. 2 bis) |
| Tuition fees up to date | aranceles_al_dia | Sin equivalente: el grado es gratuito |
| Application order | orden_postulacion | Sin equivalente: el ingreso es libre e irrestricto (art. 7) |
| Admission grade | nota_admision | Sin equivalente: el ingreso es libre e irrestricto |

Se descartan **en la carga** (HU-001) y nunca llegan a un modelo.

## Variables por momento de predicción (31 en total)

El código está en `src/alerta_temprana/datos/variables.py`; esta tabla es la misma
información para leer.

**Inscripción (M0, 19 variables)**

| Grupo | Variables |
|---|---|
| Demográficas | estado_civil, nacionalidad, desplazado, genero, edad_ingreso, internacional |
| Socioeconómicas | nivel_educ_madre, nivel_educ_padre, ocupacion_madre, ocupacion_padre, becario |
| Macroeconómicas (valor por año de ingreso) | tasa_desempleo, tasa_inflacion, variacion_pib |
| Académicas de la inscripción | modalidad_ingreso, carrera, turno_diurno, titulo_previo, nota_titulo_previo |

**Cierre del 1.er semestre (M1, 25 variables):** las 19 anteriores más
`materias_acreditadas_s1`, `materias_inscriptas_s1`, `evaluaciones_s1`,
`materias_aprobadas_s1`, `nota_promedio_s1`, `materias_sin_evaluacion_s1`.

**Cierre del 2.º semestre (M2, 31 variables):** las 25 anteriores más las mismas seis con
sufijo `_s2`.

**Categóricas codificadas (van con one-hot):** estado_civil, nacionalidad,
nivel_educ_madre, nivel_educ_padre, ocupacion_madre, ocupacion_padre, modalidad_ingreso,
carrera, titulo_previo. **Binarias:** desplazado, genero, internacional, becario,
turno_diurno. El resto son numéricas.

A revisar en el análisis exploratorio (tarea 2.1): las macroeconómicas toman un valor por
año de ingreso; decidir si se mantienen y justificarlo en el informe.

## Partición (CRISP-DM, fase 3)

- Estratificada por la variable binaria, 60/20/20 (entrenamiento, validación, prueba),
  semilla fija (`SEMILLA=42`), **la misma para los tres momentos**.
- Los índices de cada conjunto se guardan en `data/procesados/particion.csv`
  (`indice_original`, `conjunto`), para que todos los scripts usen exactamente la misma.
- Prueba: alrededor de 885 estudiantes. Son los que se cargan en la plataforma.

## Archivos de carga simulados (exportación de SIU-Guaraní)

El conjunto es histórico, así que la actualización por períodos se **simula**: los
estudiantes del conjunto de prueba se cargan en tres archivos sucesivos, uno por momento,
y cada carga dispara el recálculo con el modelo correspondiente.

Propuesta de formato (**pendiente de confirmar**, ver `08-decisiones.md`):

- `data/cargas/exportacion_inscripcion.csv`, `exportacion_cierre_1s.csv`,
  `exportacion_cierre_2s.csv`, separados por «;», UTF-8.
- Columnas: identificadores sintéticos que la plataforma debe descartar (`legajo`,
  `documento`, `apellido_nombre`), las 19 variables de inscripción, las 5 excluidas
  (para demostrar el descarte) y, según el momento, las de `_s1` y `_s2`. Cada archivo es
  una foto completa hasta ese momento. Sin `situacion_final`.
- Los identificadores son ficticios (por ejemplo `apellido_nombre = "Estudiante 0001"`) y
  constantes entre los tres archivos, para que el mismo estudiante reciba el mismo código.
- Archivos de prueba con errores (columna faltante, valores fuera de rango, vacíos) en
  `tests/fixtures/` para los criterios 2 y 3 de HU-001.

## Etiquetas comprensibles (tarea 6.2)

La ficha muestra nombres y valores legibles, por ejemplo «Materias aprobadas en el 1.er
semestre: 2 de 6». Se necesita un diccionario `variable → etiqueta` y, para las
categóricas, `código → texto en español` (carrera, título previo, modalidad de ingreso,
etc.), armado a partir del anexo del artículo y verificado contra los códigos reales del
archivo.
