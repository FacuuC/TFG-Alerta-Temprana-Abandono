# CLAUDE.md: prototipo del TFG «Alerta temprana del riesgo de abandono»

Prototipo (Sprint 1) de una plataforma web que estima el riesgo de abandono de
estudiantes de primer año, lo explica con SHAP, clasifica a los estudiantes en tres
niveles de urgencia y permite registrar el seguimiento de cada alerta. Es el núcleo
de un Trabajo Final de Grado (Licenciatura en IA y Robótica). **El código tiene
que coincidir con lo que dice el documento del TFG**: el profesor lo revisa para
verificar esa coherencia.

Todo en español: código del dominio, interfaz, mensajes, commits y documentación.

## Antes de trabajar en una historia, leé

1. `docs/sprint-1/README.md`: orden de trabajo, definición de terminado y flujo.
2. `docs/sprint-1/HU-00X.md`: la historia, con criterios de aceptación y tareas.
3. Los documentos de `docs/proyecto/` que la historia indique.
4. `docs/proyecto/08-decisiones.md`: decisiones tomadas y **pendientes**. Si la
   historia depende de una decisión pendiente, preguntá antes de implementar.

## Stack (fijado por el documento; no cambiarlo)

- Python 3.13, pandas, scikit-learn (preparación, regresión logística de referencia y
  métricas), XGBoost (modelo principal), SHAP (explicaciones).
- FastAPI (API interna) y Dash (panel) **en un único servicio**: `src/alerta_temprana/app.py`
  monta Dash dentro de FastAPI con a2wsgi.
- PostgreSQL 17 con SQLAlchemy 2 y psycopg 3.
- Docker Compose con dos contenedores: `app` y `db`. La base no publica puertos.

## Estructura

```
src/alerta_temprana/
  config.py          configuración desde .env (parámetros metodológicos incluidos)
  datos/variables.py FUENTE ÚNICA de variables, momentos, exclusiones y subgrupos
  datos/             carga, validación y seudonimización (HU-001)
  modelo/            preparación, entrenamiento, evaluación, umbrales, SHAP (HU-002, 4.1, 6.1, 6.2)
  servicio/          predicción y recálculo en cada carga (HU-003, 4.2)
  db/                tablas del DER y sesión
  api/               rutas internas de FastAPI
  ui/                pantallas de Dash
scripts/             tareas de línea de comandos (descargar datos, entrenar, generar cargas, respaldo)
tests/               pytest: al menos una prueba por criterio de aceptación automatizable
data/raw/            dataset de UCI (no se versiona)
modelos/             modelos versionados con sus metadatos (sí se versionan)
reportes/            informe exploratorio e informe de evaluación (sí se versionan)
docs/                especificación del proyecto y del sprint
```

## Comandos (Windows, PowerShell, con el entorno virtual activado)

```powershell
.\.venv\Scripts\Activate.ps1
pytest                                                    # todas las pruebas
pytest -m "not db"                                        # sin base de datos
docker compose -f compose.yaml -f compose.dev.yaml up -d db   # base para desarrollo
uvicorn alerta_temprana.app:app --reload                  # app local en http://127.0.0.1:8000
docker compose up -d --build                              # todo en Docker
python scripts/verificar_entorno.py                       # control del entorno
python scripts/preparar_particion.py                      # partición fija (ya generada)
python scripts/entrenar.py --momento inscripcion          # elige modelo y umbrales con validación
python scripts/generar_fichas_cuestionario.py             # fichas del cuestionario (ya generadas)
```

## Reglas que no se negocian

Vienen de las correcciones del tutor. Romper una invalida resultados del documento.

1. **Conjunto de prueba sagrado.** Partición estratificada 60/20/20 con semilla fija,
   la misma para los tres momentos, guardada en disco. Variables, hiperparámetros,
   elección entre modelos y umbrales se deciden **solo con validación**. La prueba se
   usa **una sola vez**, en el script de evaluación final. Si no se alcanza la meta,
   se informa así; no se reajusta.
2. **Sin información futura.** Cada modelo usa solo las variables de su momento
   (`VARIABLES_POR_MOMENTO`: 19, 25 y 31). Nada de `_s2` en `cierre_1s`.
3. **Transformaciones ajustadas solo con entrenamiento** (one-hot, estandarización);
   después se aplican a validación y prueba. Usá `Pipeline` de scikit-learn.
4. **Variable objetivo binaria:** abandono = 1; graduado o «sigue cursando» = 0.
5. **Desbalance con pesos de clase** (`scale_pos_weight`, `class_weight`). Nunca SMOTE
   ni casos sintéticos.
6. **Variables excluidas** (necesidades especiales, deudor, aranceles al día, orden de
   postulación, nota de admisión): se descartan en la carga y no entran a ningún modelo.
7. **Seudonimización:** la plataforma nunca guarda ni muestra nombre, documento ni
   legajo. Solo el código seudonimizado.
8. **Explicaciones:** SHAP muestra cuánto pesa cada variable en la estimación, **no la
   causa** del abandono. Nunca escribir «factores que explican» o «el porqué».
9. **Alcance del Sprint 1:** HU-001 a HU-007. No implementar inicio de sesión (HU-009),
   panel de métricas (HU-008), API externa (HU-010), asignación a tutores (HU-011),
   intervenciones (HU-012), ajuste de umbrales (HU-013) ni reentrenamiento (HU-014).
   Se usa un usuario de prueba por rol, precargado, elegido en la barra superior.
10. **Secretos** solo en `.env` (nunca en el código ni en el repositorio).
11. **Modelo congelado:** `modelos/cierre_1s/v1.0/` generó las fichas del cuestionario.
    No reentrenarlo ni sobrescribirlo; cualquier cambio de modelo es una versión nueva y
    hay que avisar, porque las fichas evaluadas dejarían de coincidir.

## Términos fijos (código, interfaz y textos)

| Usar | No usar |
|---|---|
| carga (de datos) | ingesta |
| momento de predicción: inscripción, cierre del 1.er semestre, cierre del 2.º semestre | período, ingreso |
| seudonimizado (datos de la plataforma) | anonimizado (solo el dataset de Realinho lo es) |
| factores que más pesan en la estimación | factores que explican, causas |
| sigue cursando (`cursando`) | enrolled, matriculado |
| nivel de urgencia: alto, medio, bajo | riesgo crítico, severidad |
| estado de seguimiento: pendiente, contactado, en acompañamiento | — |
| organización de referencia | universidad X, institución real |

## Convenciones

- Nombres del dominio en español y `snake_case`, como en la Tabla 32 del documento
  (`codigo_estudiante`, `materias_aprobadas_s1`). Tipado en funciones públicas.
- Interfaz en español rioplatense neutro, con formato argentino: coma decimal (0,91),
  fechas dd/mm/aaaa. El nivel se muestra con color **y** texto.
- Una función hace una cosa; lógica de negocio fuera de los callbacks de Dash y de las
  rutas de FastAPI (en `datos/`, `modelo/`, `servicio/`), para poder probarla.
- Pruebas con pytest. Marcá con `@pytest.mark.db` las que necesitan PostgreSQL y con
  `@pytest.mark.datos` las que necesitan el dataset.
- Commits: `HU-00X: descripción breve (tarea X.Y)` y las líneas de atribución que
  correspondan. Una historia terminada = criterios cumplidos + pruebas en verde.

## Lo que no hay que hacer

- No modificar `docs/proyecto/` ni los criterios de aceptación sin que el usuario lo
  pida: son copia del documento entregado. Si algo del documento no se puede cumplir o
  es inconsistente, avisá y anotalo en `docs/pendientes-documento.md`.
- No agregar dependencias fuera del stack sin preguntar.
- No leer `.env`.
- No usar el conjunto de prueba en notebooks exploratorios ni en búsquedas de hiperparámetros.
