# Avance del Sprint 1

Registro para la línea real del burndown (sección Sprint Backlog del documento). Al
terminar cada historia, sumar una fila. Puntos totales: 45.

| Fecha | Historia o tarea | Estado | Puntos terminados | Puntos restantes | Notas |
|---|---|---|---|---|---|
| 02/11 | Tarea 1.1: entorno, repositorio y contenedores | En progreso | 0 | 45 | Estructura y especificaciones listas; falta instalar, descargar datos y primer commit |
| 03/11 | Tarea 1.1: dependencias | En progreso | 0 | 45 | Versiones fijadas y probadas con Python 3.13 (15 pruebas en verde; app y base conectadas). Falta: dataset, Docker y primer commit en Windows |
| 03/11 | HU-002 camino rápido + 4.1, 6.1, 6.2 | En progreso | 0 | 45 | Partición, modelo de cierre_1s congelado (XGBoost, AUC validación 0,8878), umbrales, SHAP, etiquetas y 6 fichas del cuestionario. 33 pruebas en verde |
| 03/11 | Tarea 1.1: dataset | En progreso | 0 | 45 | `data/raw/data.csv` verificado (4.424 × 37, distribución correcta, códigos originales de UCI). Falta: `.venv`, `.env`, Docker y primer commit en Windows |
| 04/11 | HU-002: tareas 2.1, 2.3, 2.4 y 2.5 | En progreso | 0 | 45 | Informe exploratorio, modelos de inscripción y cierre_2s, umbrales exactos, carga portable y `evaluar_final.py` ensayado con validación. 80 pruebas en verde (4 esperan la evaluación final). Falta: ejecución única sobre prueba (Facundo) |
| 04/11 | HU-002 | Terminada | 13 | 32 | Evaluación final única sobre prueba: AUC-ROC 0,7861 / 0,8928 / 0,9177; meta de cierre_1s alcanzada; tres modelos habilitados. Umbrales en prueba: detección 74,6–79,2 % (< 80 %), se informa (ver HU-004, criterio 5). 85 pruebas en verde |

| 04/11 | HU-001: tareas 1.2, 1.3 y 1.4 | En progreso | 13 | 32 | Tablas del DER, validación, seudonimización, servicio, API, pantalla de carga y 3 archivos simulados (885 válidos, 0 rechazados cada uno). P2 y P5 confirmadas. 144 pruebas en verde y 1 `xfail` (códigos de las fichas, ver pendientes). Falta: verificación manual de la pantalla, `/revisar-hu` y commit |
| 05/11 | HU-001: verificación manual | En progreso | 13 | 32 | Las 5 pruebas manuales de la pantalla pasaron (Facundo). Se mantiene la `SEUDONIMO_CLAVE` actual: se quitó la prueba de los códigos de las fichas. 144 pruebas en verde. Falta: `/revisar-hu` y commit |
| 05/11 | Decisión del tutor: el cuestionario no se aplica | — | 13 | 32 | El instrumento (formulario y 6 fichas) va al Anexo; el objetivo 4 se informa con lo que se entrega (ver `08-decisiones.md`, 05/11). La tarea 6.4 queda sin aplicación ni análisis |
| 05/11 | HU-001 | Terminada | 21 | 24 | Criterios 1 a 5 cumplidos (revisión con evidencia); verificación manual de la pantalla en verde; 144 pruebas en verde. La base de desarrollo no se vacía ahora: es el primer paso de la verificación de HU-003 (`README.md`, «Datos para la Demo») |
| 05/11 | HU-003 (3.1 a 3.3) + HU-004 (4.2) | En progreso | 21 | 24 | P3 y P4 confirmadas. MODELO se llena desde `modelos/`, servicio de predicción, planificador en segundo plano, alertas (P3), estado del recálculo en la carga y última actualización en la barra superior. De punta a punta con `data/cargas/`: 117 / 134 / 137 en nivel alto (como el informe) y las 6 fichas coinciden. 196 pruebas en verde. Falta: verificación manual, `/revisar-hu` y commit |
| 09/11 | HU-003 | Terminada | 26 | 19 | Criterios 1 a 5 cumplidos (revisión con evidencia); verificación manual del recálculo en verde (Facundo); el criterio 5 se verifica con pruebas automáticas. 198 pruebas en verde |
| 09/11 | HU-004 | Terminada | 29 | 16 | Criterios 1 a 4 cumplidos (1 en HU-002; 2 a 4 en el servicio de predicción, con alertas según P3); criterio 5 informado como no alcanzado en prueba, sin reajustar (decisión del 04/11). Se sumaron las pruebas de la tarea 3.3 de carga rechazada y de conservación del estado de seguimiento entre cargas. 198 pruebas en verde |
| 09/11 | HU-005 (5.1 y 5.2) | En progreso | 29 | 16 | Servicio de consulta con orden y filtros en SQL, `GET /api/alertas`, navegación según el usuario de prueba (decisión del 09/11) y listado sin filtro por defecto (modificación de P3 del 07/11, observación 7 del tutor). Con las tres cargas de la Demo: 529 alertas (alto 137, medio 131, bajo 261). 244 pruebas en verde. Falta: verificación manual, `/revisar-hu` y commit |
| 09/11 | HU-005 | Terminada | 34 | 11 | Criterios 1 a 4 cumplidos (revisión con evidencia); verificación manual del listado y de la navegación en verde (Facundo). Sin filtro por defecto (modificación de P3, observación 7 del tutor); 529 alertas con las tres cargas (alto 137, medio 131, bajo 261). 244 pruebas en verde |
| 09/11 | HU-006 (6.3) | En progreso | 34 | 11 | Ficha en `/ficha/<id_alerta>` desde «Ver ficha» del listado: probabilidad, nivel, carrera y turno, cálculo (fecha y hora · modelo), los 5 factores con texto comprensible, barra y sentido, el aviso del criterio 4 y el seguimiento como texto. `GET /api/alertas/{id}`. Un factor que no corresponde al momento no se muestra: mensaje controlado y detalle en el registro. Cuenta como pantalla de Coordinación y Tutor/a (navegación del 09/11). Con inscripción y cierre_1s, las fichas de los 6 casos coinciden con el Anexo. Criterio 5 no verificado (cuestionario no aplicado). 277 pruebas en verde. Falta: verificación manual, `/revisar-hu` y commit |
| 09/11 | HU-006 | Terminada | 42 | 3 | Criterios 1 a 4 cumplidos (revisión con evidencia); verificación manual de la ficha, la navegación y la API en verde, con la captura de la Figura 7 (Facundo). Criterio 5 no verificado: el cuestionario no se aplica (decisión del 05/11), se informa como no evaluado, igual que HU-004, criterio 5. Las fichas de los 6 casos del Anexo coinciden con la pantalla (con inscripción y cierre_1s). 277 pruebas en verde |

### Verificación manual de la pantalla de carga (HU-001)

Con la base levantada (`docker compose -f compose.yaml -f compose.dev.yaml up -d db`),
`python scripts/generar_cargas.py` y `uvicorn alerta_temprana.app:app --reload`, en
http://127.0.0.1:8000:

1. Con «Área de Sistemas (sistemas01)» en la barra superior, elegir «Inscripción», arrastrar
   `data/cargas/exportacion_inscripcion.csv` y «Validar y cargar» → 885 válidos, 0
   rechazados, 885 nuevos; leyenda de seudonimización; columnas descartadas (identificatorias
   y excluidas); la carga aparece en «Cargas anteriores» con fecha dd/mm/aaaa y `sistemas01`.
2. «Cierre del 1.er semestre» con `exportacion_cierre_1s.csv` → 0 nuevos, 885 ya
   existentes, 885 rendimientos agregados. Repetir con «Cierre del 2.º semestre».
3. «Cierre del 1.er semestre» con `exportacion_inscripcion.csv` → carga rechazada, lista de
   columnas `_s1` y la sugerencia de revisar el momento.
4. «Inscripción» con `tests/fixtures/registros_con_errores.csv` → 7 válidos, 3 rechazados;
   «Descargar informe de errores» baja un CSV con 3 filas (fila, código, columna, motivo) y
   sin legajos. Con `tests/fixtures/coma_decimal.csv` → rechazo con el mensaje de la coma
   decimal.
5. Elegir «Tutor/a (tutor01)» → el formulario se oculta y aparece el aviso de que la carga
   es del Área de Sistemas.

Resultado (05/11, Facundo): **las 5 pruebas pasaron.** Los tres archivos simulados quedaron
cargados en la base de desarrollo con la `SEUDONIMO_CLAVE` actual.

### Verificación manual del recálculo (HU-003 y HU-004)

Primer paso de «Datos para la Demo» (`README.md`): **vaciar la base** (borra las cargas de
la verificación de HU-001 y los 7 estudiantes sintéticos) y levantarla de nuevo; generar
los archivos y arrancar la app. Al iniciar, la app crea las tablas con las restricciones
nuevas y registra los tres modelos en MODELO.

1. Antes de cargar, con cualquier usuario: la barra superior dice «Todavía no se calculó el
   riesgo.».
2. Con «Área de Sistemas (sistemas01)», cargar `exportacion_inscripcion.csv` como
   «Inscripción» → la tarjeta «Cálculo del riesgo» dice «en curso…» y en unos segundos
   «Completado: modelo v1.0 (Inscripción) · 885 estudiantes», con nivel alto 117, medio
   359, bajo 409, 476 alertas nuevas y 0 actualizadas. La barra superior pasa a «Última
   actualización: dd/mm/aaaa hh:mm · modelo v1.0 (Inscripción)».
3. `exportacion_cierre_1s.csv` como «Cierre del 1.er semestre» → «Completado: modelo v1.0
   (Cierre del 1.er semestre)»: alto 134, medio 162, bajo 589; 47 alertas nuevas y 476
   actualizadas. La barra superior cambia al modelo de cierre_1s.
4. `exportacion_cierre_2s.csv` como «Cierre del 2.º semestre» → alto 137, medio 131, bajo
   617; 6 alertas nuevas y 523 actualizadas (529 alertas en total).
5. Elegir «Tutor/a (tutor01)» → la barra superior sigue mostrando la última actualización.
6. Por la API: `curl.exe http://127.0.0.1:8000/api/predicciones/ultima-actualizacion` →
   versión `1.0`, momento `cierre_2s`; `curl.exe http://127.0.0.1:8000/api/cargas/3/recalculo`
   → `completado`.

El criterio 5 (sin modelo habilitado) se verifica solo con las pruebas automáticas
(decisión de Facundo, 05/11).

Resultado (09/11, Facundo): **los 6 pasos pasaron.** La base de desarrollo queda con las
tres cargas simuladas, en orden, y sin los estudiantes sintéticos.

### Verificación manual del listado (HU-005)

Con la base de desarrollo con las tres cargas (resultado de la verificación de HU-003) y
`uvicorn alerta_temprana.app:app --reload`, en http://127.0.0.1:8000:

1. Elegir «Coordinación (coordinacion01)» en la barra superior → pasa solo, sin recargar,
   al «Listado de alertas tempranas»; el menú lateral muestra «Listado de alertas». Los
   cuatro filtros están vacíos («Todas» / «Todos»).
2. Tarjetas: nivel alto 137, nivel medio 131, pendientes de contacto 529; «529 alertas».
   La tabla empieza por nivel alto con la probabilidad más alta y termina en nivel bajo;
   el nivel se ve como etiqueta con color y texto; probabilidad con coma (0,99).
3. Desplazar la tabla: el encabezado queda fijo. Esta vista, sin filtros, es la captura de
   la Figura 6.
4. Filtrar Nivel = Bajo → 261 alertas, tarjetas alto 0 y medio 0. Sumar Turno = Nocturno,
   una carrera y un estado → tabla y tarjetas cambian juntas; con una combinación sin
   resultados, «Ninguna alerta cumple los filtros.».
5. Navegación según el usuario (decisión del 09/11), empezando cada caso en el listado con
   «Coordinación» y un filtro aplicado (por ejemplo, Nivel = Alto):
   - a. «Tutor/a (tutor01)» → sigue el listado, **con el mismo filtro** y las mismas
     alertas (el tutor ve todas: ver `pendientes-documento.md`).
   - b. «Área de Sistemas (sistemas01)» → pasa sin recargar a «Carga de datos»; la
     dirección queda en `/`, el menú muestra «Carga de datos» y la carga funciona como antes.
   - c. Volver a «Coordinación» (pasa al listado) y elegir «Secretaría Académica
     (secretaria01)» → «Panel de métricas» con el aviso de que el panel de métricas
     (HU-008) no forma parte de este prototipo; sin filtros, tarjetas, tabla ni formulario
     de carga; la dirección queda en `/metricas`.
   - d. Con «Área de Sistemas», escribir a mano `http://127.0.0.1:8000/listado` → se
     muestra «Carga de datos» y la dirección pasa a `/`. Con «Secretaría Académica»,
     escribir `/listado` o `/` → pasa a `/metricas`. Con «Coordinación», escribir `/otra`
     → pasa a `/listado`.
   - e. En ningún caso aparecen errores en la consola del navegador (F12 → Consola).
6. `curl.exe "http://127.0.0.1:8000/api/alertas?nivel=bajo"` con cualquier usuario elegido
   → 261 alertas, resumen con alto y medio en 0 (la API no cambia con la navegación).

Resultado (09/11, Facundo): **los 6 pasos pasaron**, incluidas la navegación al cambiar de
usuario y al escribir direcciones a mano, y la consola del navegador sin errores.

### Verificación manual de la ficha (HU-006)

Con la base de desarrollo con las tres cargas (la misma de HU-005) y
`uvicorn alerta_temprana.app:app --reload`, en http://127.0.0.1:8000. Los números de alerta
(294 y 58) son los de esa base; si se vuelve a armar, se buscan por el código.

1. Elegir «Coordinación (coordinacion01)» → listado con la columna «Ficha» y «Ver ficha» en
   cada fila. Filtrar Carrera = Educación Básica y Nivel = Alto y hacer clic en «Ver ficha» de
   **EST-932B2E48** → se abre sin recargar la página, la dirección pasa a `/ficha/294`, el
   título es «Ficha del estudiante EST-932B2E48» y el menú resalta «Listado de alertas».
2. Tarjetas: probabilidad **0,98**; nivel **Alto** (etiqueta roja con texto); «Educación
   Básica · Diurno»; cálculo «08/11/2026 23:57 · modelo v1.0 (Cierre del 2.º semestre)».
3. «Factores que más pesan en esta estimación», en este orden (barra relativa al mayor):

   | # | Factor | Sentido | Barra |
   |---|---|---|---|
   | 1 | Materias aprobadas en el 2.º semestre: 1 de 6 | Aumenta el riesgo (rojo) | 100 % |
   | 2 | Carrera: Educación Básica | Aumenta el riesgo (rojo) | 69 % |
   | 3 | Nivel educativo de la madre: sin dato | Aumenta el riesgo (rojo) | 48 % |
   | 4 | Materias aprobadas en el 1.er semestre: 3 de 6 | Aumenta el riesgo (rojo) | 26 % |
   | 5 | Edad al ingresar: 20 años | Disminuye el riesgo (azul) | 18 % |

   Debajo, el aviso completo: «La alerta es una estimación para apoyar la decisión y no
   reemplaza el criterio del tutor. Los factores muestran cuánto pesa cada variable en la
   estimación, no las causas del abandono.». En ninguna parte dice «más influyen», «Aranceles
   al día» ni «Matrícula al día». Seguimiento: «Estado: Pendiente» y «Alerta creada el
   08/11/2026».
4. «← Volver al listado» → listado sin filtros (529 alertas).
5. Filtrar Carrera = Higiene Oral y Nivel = Bajo y abrir **EST-4CC9FA68** (`/ficha/58`):
   probabilidad **0,19**; nivel **Bajo**; «Higiene Oral · Diurno»; el mismo cálculo; factores:

   | # | Factor | Sentido | Barra |
   |---|---|---|---|
   | 1 | Materias aprobadas en el 2.º semestre: 8 de 8 | Disminuye el riesgo (azul) | 100 % |
   | 2 | Edad al ingresar: 27 años | Aumenta el riesgo (rojo) | 35 % |
   | 3 | Materias aprobadas en el 1.er semestre: 7 de 7 | Disminuye el riesgo (azul) | 31 % |
   | 4 | Nota promedio en el 2.º semestre: 13,2 (escala de 0 a 20) | Disminuye el riesgo (azul) | 22 % |
   | 5 | Materias inscriptas en el 2.º semestre: 8 | Aumenta el riesgo (rojo) | 14 % |

   Seguimiento: «Estado: Pendiente» y «Alerta creada el 08/11/2026».
6. Navegación con la ficha abierta (decisión del 09/11):
   - a. «Tutor/a (tutor01)» → la misma ficha, sin cambios.
   - b. «Área de Sistemas (sistemas01)» → «Carga de datos», dirección `/`.
   - c. Volver a «Coordinación», abrir una ficha y elegir «Secretaría Académica
     (secretaria01)» → «Panel de métricas», dirección `/metricas`.
   - d. Con «Coordinación», escribir a mano `/ficha/99999` → «No se encontró la alerta.» con
     el enlace para volver; `/ficha/abc` → pasa a `/listado`. Con «Área de Sistemas»,
     escribir `/ficha/294` → «Carga de datos» en `/`.
   - e. Sin errores en la consola del navegador (F12 → Consola).
7. API: `curl.exe http://127.0.0.1:8000/api/alertas/294` → probabilidad 0.9805, nivel
   `alto`, momento `cierre_2s` y los 5 factores con el texto del paso 3;
   `curl.exe http://127.0.0.1:8000/api/alertas/99999` → 404.
8. Captura de la **Figura 7**: la ficha de EST-932B2E48 con «Tutor/a (tutor01)» en la barra
   superior, con las tarjetas, los cinco factores y el aviso visibles. Si HU-007 se termina,
   conviene repetirla después, con el desplegable del estado.

El criterio 5 (valoración del cuestionario) no se verifica: el cuestionario no se aplica
(decisión del 05/11; `pendientes-documento.md`).

Resultado (09/11, Facundo): **los 8 pasos pasaron**, incluidas la navegación con la ficha
abierta, las direcciones escritas a mano, la API y la captura de la Figura 7 (ficha de
EST-932B2E48 con «Tutor/a» en la barra superior y el aviso visible).

## Estado de las historias

| ID | Puntos | Estado | Commit |
|---|---|---|---|
| HU-001 | 8 | Terminada | «HU-001: carga, validación y seudonimización…» (05/11) |
| HU-002 | 13 | Terminada | «HU-002: evaluación final sobre prueba…» (04/11) |
| HU-003 | 5 | Terminada | «HU-003 y HU-004: recálculo automático del riesgo…» (09/11) |
| HU-004 | 3 | Terminada | «HU-003 y HU-004: recálculo automático del riesgo…» (09/11) |
| HU-005 | 5 | Terminada | «HU-005: listado de alertas con orden, filtros y navegación por usuario…» (09/11) |
| HU-006 | 8 | Terminada | «HU-006: ficha del estudiante con los factores que más pesan…» (09/11) |
| HU-007 | 3 | Por hacer | |
