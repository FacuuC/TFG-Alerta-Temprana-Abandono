# Alerta temprana del riesgo de abandono universitario

Prototipo de una plataforma web que estima el riesgo de abandono de los estudiantes de
primer año, muestra los factores que más pesan en cada estimación y clasifica a los
estudiantes en tres niveles de urgencia para el Programa de Tutorías.

Trabajo Final de Grado de Facundo Costamagna (Licenciatura en Inteligencia Artificial y
Robótica). El prototipo implementa el núcleo de la plataforma (Sprint 1, historias HU-001
a HU-007) sobre una **organización de referencia**: un caso modelado de universidad
nacional argentina, no una institución real.

- **Datos:** conjunto público y anonimizado de Realinho et al. (2021), UCI Machine Learning
  Repository, https://doi.org/10.24432/C5MC89 (CC BY 4.0). No se incluye en el
  repositorio: se descarga con un script.
- **Stack:** Python 3.13, scikit-learn, XGBoost, SHAP, FastAPI, Dash, PostgreSQL 17,
  Docker Compose.

## Requisitos

- Windows 10/11, macOS o Linux.
- Python 3.13 (3.12 también funciona).
- Docker Desktop (o Docker Engine con Compose v2).
- Git.

## Instalación para desarrollo (Windows, PowerShell)

Desde la carpeta del repositorio:

```powershell
# 0. Configuración de Claude Code y VS Code (solo la primera vez)
py -3.13 scripts/instalar_configuracion_editor.py

# 1. Entorno virtual
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

# 2. Dependencias (aplicación + pruebas + notebooks)
pip install -r requirements-dev.txt

# 3. Configuración con claves aleatorias (.env no se sube al repositorio)
python scripts/crear_env.py

# 4. Dataset (descarga desde UCI y verificación)
python scripts/descargar_datos.py

# 5. Base de datos para desarrollo (publicada solo en 127.0.0.1)
docker compose -f compose.yaml -f compose.dev.yaml up -d db

# 6. Control del entorno y pruebas
python scripts/verificar_entorno.py
pytest
```

Si PowerShell no deja activar el entorno («la ejecución de scripts está deshabilitada»):
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y volver a intentar.

Si el puerto 5432 está ocupado (por ejemplo, por un PostgreSQL instalado en Windows),
cambiá `DB_PORT` en `.env` (por ejemplo, a 5433) y repetí el paso 5.

## Ejecución

**Con Docker (como se entrega):**

```powershell
docker compose up -d --build
```

La aplicación queda en http://localhost:8000 (o http://127.0.0.1:8000) y su estado en
http://localhost:8000/salud. `docker compose ps` muestra el puerto como
`127.0.0.1:8000->8000/tcp`: se publica solo en la interfaz local del equipo, así que no se
puede abrir desde otras computadoras de la red. La base de datos no expone puertos fuera de
la red interna de Docker.

## Entorno de demostración

El prototipo es un entorno de demostración acotado:

- **Se ejecuta solo en el equipo local.** `compose.yaml` publica la aplicación únicamente
  en `127.0.0.1:8000` (dentro del contenedor escucha en `0.0.0.0`, pero el equipo anfitrión
  solo la expone en su interfaz local) y la base no publica puertos. `compose.dev.yaml`
  también publica la base solo en `127.0.0.1`. No cambies esas líneas por `"8000:8000"`
  ni publiques la plataforma en la red.
- **Se usa únicamente con los archivos del conjunto público del repositorio**: el dataset
  de Realinho et al. (2021) que descarga `scripts/descargar_datos.py` y los archivos
  simulados que genera `scripts/generar_cargas.py`. **Nunca con datos reales de
  estudiantes.**
- **El selector de usuario de prueba no es un control de acceso.** En el Sprint 1 no hay
  inicio de sesión: cualquiera que abra la plataforma puede elegir cualquier usuario de
  prueba. El inicio de sesión y el control por rol llegan con HU-009 (Sprint 2).

**En desarrollo (recarga automática):**

```powershell
docker compose -f compose.yaml -f compose.dev.yaml up -d db
uvicorn alerta_temprana.app:app --reload
```

## Datos para la Demo: base vacía y tres cargas en orden

Es el primer paso de cada verificación manual desde HU-003 y de la Demo: se parte de una
base vacía y se cargan los tres archivos simulados en orden, para que el riesgo se calcule
como en un año académico real. **Vaciar la base borra todo** (cargas, estudiantes,
predicciones, alertas y seguimiento).

```powershell
# 1. Vaciar la base (borra el volumen datos_db). En la versión con Docker completa:
#    docker compose down -v ; docker compose up -d --build
docker compose -f compose.yaml -f compose.dev.yaml down -v
docker compose -f compose.yaml -f compose.dev.yaml up -d db

# 2. Archivos simulados: estudiantes del conjunto de prueba, sin situación final
python scripts/generar_cargas.py

# 3. Aplicación (al iniciar crea las tablas y los usuarios de prueba)
uvicorn alerta_temprana.app:app --reload
```

4. En http://127.0.0.1:8000, con el usuario «Área de Sistemas (sistemas01)», en «Carga de
   datos», cargar **en este orden**, cada uno con su momento de predicción:
   1. `data/cargas/exportacion_inscripcion.csv` → «Inscripción»;
   2. `data/cargas/exportacion_cierre_1s.csv` → «Cierre del 1.er semestre»;
   3. `data/cargas/exportacion_cierre_2s.csv` → «Cierre del 2.º semestre».

   Cada carga da 885 registros válidos y 0 rechazados. Lo mismo por la API:

   ```powershell
   curl.exe -F "archivo=@data/cargas/exportacion_inscripcion.csv" -F momento=inscripcion -F usuario=sistemas01 http://127.0.0.1:8000/api/cargas
   curl.exe -F "archivo=@data/cargas/exportacion_cierre_1s.csv" -F momento=cierre_1s -F usuario=sistemas01 http://127.0.0.1:8000/api/cargas
   curl.exe -F "archivo=@data/cargas/exportacion_cierre_2s.csv" -F momento=cierre_2s -F usuario=sistemas01 http://127.0.0.1:8000/api/cargas
   ```

No cargues los archivos de `tests/fixtures/` en esta base: son estudiantes sintéticos de
prueba y aparecerían en el listado.

## Estructura

```
src/alerta_temprana/   código de la aplicación (datos, modelo, servicio, db, api, ui)
scripts/               descarga de datos, entrenamiento, evaluación, respaldo
tests/                 pruebas (pytest)
data/                  dataset y archivos de carga simulados (no se versionan)
modelos/               modelos entrenados con sus metadatos
reportes/              informe exploratorio, informe de evaluación y cuestionario
docs/                  especificación: contexto, datos, CRISP-DM, pantallas, historias
```

La especificación completa está en [`docs/`](docs/): empezá por
[`docs/sprint-1/README.md`](docs/sprint-1/README.md).

## Licencia y créditos

Código: uso académico. Datos: Realinho, V., Vieira Martins, M., Machado, J. y Baptista, L.
(2021). *Predict students' dropout and academic success* [Conjunto de datos]. UCI Machine
Learning Repository. https://doi.org/10.24432/C5MC89. Licencia CC BY 4.0.
