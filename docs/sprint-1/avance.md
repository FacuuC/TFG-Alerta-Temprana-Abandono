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

## Estado de las historias

| ID | Puntos | Estado | Commit |
|---|---|---|---|
| HU-001 | 8 | Por hacer | |
| HU-002 | 13 | Terminada | «HU-002: evaluación final sobre prueba…» (04/11) |
| HU-003 | 5 | Por hacer | |
| HU-004 | 3 | Por hacer | |
| HU-005 | 5 | Por hacer | |
| HU-006 | 8 | Por hacer | |
| HU-007 | 3 | Por hacer | |
