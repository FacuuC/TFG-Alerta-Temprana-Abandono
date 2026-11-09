"""Servicio de predicción: aplica el modelo habilitado del momento de cada
carga, guarda predicciones, factores y alertas, y conserva el historial
(HU-003, HU-004 tarea 4.2). Lo dispara el fin de una carga válida.

La lógica de negocio está acá y no en los callbacks de Dash ni en las rutas de FastAPI:
las pantallas y la API llaman a las mismas funciones (decisión P4), así se prueban sin
interfaz y respetan las mismas reglas.

- `carga`: registro de una carga (HU-001, criterios 1 a 5; P5: solo el Área de Sistemas).
- `modelos`: tabla MODELO y modelo habilitado con control de SHA-256 (HU-003; P6).
- `planificador`: recálculo en segundo plano al terminar cada carga (HU-003, criterios 1 y 5).
- `prediccion`: probabilidad, nivel y cinco factores SHAP con historial (HU-003 y HU-004).
- `alertas`: una alerta por estudiante y consulta del listado (HU-004 y HU-005; P3).
- `ficha`: ficha del estudiante con los factores que más pesan (HU-006, criterios 1 a 3).
- `seguimiento`: cambio de estado con registro en CAMBIO_ESTADO (HU-007; P3, P4 y P5).
- `usuarios`: control del usuario de prueba elegido (P5; no es control de acceso, HU-009).
"""
