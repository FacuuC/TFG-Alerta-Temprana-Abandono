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
| 05/11 | HU-001 | Terminada | 21 | 24 | Criterios 1 a 5 cumplidos (revisión con evidencia); verificación manual de la pantalla en verde; 144 pruebas en verde. La base de desarrollo no se vacía ahora: es el primer paso de la verificación de HU-003 (`README.md`, «Datos para la Demo») |

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

## Estado de las historias

| ID | Puntos | Estado | Commit |
|---|---|---|---|
| HU-001 | 8 | Terminada | «HU-001: carga, validación y seudonimización…» (05/11) |
| HU-002 | 13 | Terminada | «HU-002: evaluación final sobre prueba…» (04/11) |
| HU-003 | 5 | Por hacer | |
| HU-004 | 3 | Por hacer | |
| HU-005 | 5 | Por hacer | |
| HU-006 | 8 | Por hacer | |
| HU-007 | 3 | Por hacer | |
