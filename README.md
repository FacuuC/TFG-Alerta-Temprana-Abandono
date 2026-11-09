# Alerta temprana del riesgo de abandono universitario

Prototipo de una plataforma web que estima el riesgo de abandono de los estudiantes de
primer año, muestra los factores que más pesan en cada estimación y clasifica a los
estudiantes en tres niveles de urgencia para el Programa de Tutorías.

Trabajo Final de Grado de Facundo Costamagna (Licenciatura en Inteligencia Artificial y
Robótica). El prototipo implementa el núcleo de la plataforma (Sprint 1, historias HU-001
a HU-007) sobre una **organización de referencia**: un caso modelado de universidad
nacional argentina, no una institución real.

Este README es el **manual de instalación** del prototipo: alcanza para instalarlo,
ejecutarlo, usarlo, respaldarlo y restaurarlo.

- [1. Qué es y qué no es](#1-qué-es-y-qué-no-es)
- [2. Requisitos](#2-requisitos)
- [3. Instalación paso a paso](#3-instalación-paso-a-paso)
- [4. Uso de la demo (manual de usuario breve)](#4-uso-de-la-demo-manual-de-usuario-breve)
- [5. Respaldo, restauración y vaciado de la base](#5-respaldo-restauración-y-vaciado-de-la-base)
- [6. Pruebas](#6-pruebas)
- [7. Correspondencia con el documento](#7-correspondencia-con-el-documento)
- [8. Fuente de los datos](#8-fuente-de-los-datos)
- [9. Problemas comunes](#9-problemas-comunes)
- [10. Instalación para desarrollo](#10-instalación-para-desarrollo)

## 1. Qué es y qué no es

Es una **copia de demostración local del Sprint 1**: dos contenedores Docker (aplicación y
base de datos) que corren en el equipo de quien la instala.

- **Sin inicio de sesión ni HTTPS.** En la barra superior se elige un usuario de prueba
  (uno por rol). **El selector de usuario no es un control de acceso:** cualquiera que
  abra la plataforma puede elegir cualquier usuario. El inicio de sesión por rol (HU-009)
  llega en un sprint posterior.
- **Solo en el equipo local.** La aplicación se publica únicamente en `127.0.0.1:8000`, así
  que no se puede abrir desde otras computadoras de la red, y la base de datos no publica
  ningún puerto: solo la alcanza la aplicación por la red interna de Docker. No cambies
  `"127.0.0.1:8000:8000"` por `"8000:8000"` ni publiques la plataforma en la red.
- **Solo con el conjunto de datos público** de Realinho et al. (2021) y los tres archivos
  de carga simulados que trae el repositorio. **Nunca con datos reales de estudiantes.**
- La plataforma nunca guarda ni muestra nombre, documento ni legajo: cada estudiante se
  identifica con un código seudonimizado (`EST-` y 8 caracteres).
- Los factores de la ficha muestran cuánto pesa cada variable en la estimación (SHAP), **no
  las causas** del abandono.

## 2. Requisitos

| Requisito | Detalle |
|---|---|
| Sistema | Windows 10/11, macOS o Linux |
| Docker | Docker Desktop, o Docker Engine con **Compose v2** (`docker compose version`) |
| Git | Para clonar el repositorio |
| Memoria | 4 GB libres para Docker (la aplicación usa unos 200 MB en reposo y más durante el cálculo del riesgo; la base, unos 50 MB) |
| Disco | Unos 3 GB: imagen de la aplicación ≈ 1,8 GB, imagen de PostgreSQL ≈ 0,4 GB, datos < 100 MB |
| Puertos | **8000** libre en `127.0.0.1` (la aplicación). El 5432 solo se usa en desarrollo (sección 10) |

No hace falta instalar Python para la instalación con Docker.

## 3. Instalación paso a paso

Los comandos van en PowerShell (Windows) o en una terminal bash (Linux, macOS o Git Bash),
desde la carpeta del repositorio.

**1. Clonar el repositorio**

```powershell
git clone <URL del repositorio> alerta-temprana
cd alerta-temprana
```

**2. Crear el archivo `.env`** a partir de `.env.example`. `.env` tiene los secretos y nunca
se sube al repositorio.

```powershell
Copy-Item .env.example .env        # PowerShell
cp .env.example .env               # bash
```

Abrilo con un editor y reemplazá los dos valores marcados con «cambiar». Para generar un
valor aleatorio:

```powershell
# PowerShell: 64 caracteres hexadecimales con un generador criptográfico
$b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); -join ($b | ForEach-Object { '{0:x2}' -f $_ })
```

```bash
openssl rand -hex 32               # bash
```

(Si tenés Python, `python scripts/crear_env.py` crea `.env` con valores aleatorios.)

| Variable | Para qué sirve | Valor |
|---|---|---|
| `ENTORNO` | Nombre del entorno | `desarrollo` (dejalo así) |
| `POSTGRES_USER` | Usuario de PostgreSQL | `alerta` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL. Se fija **la primera vez** que se crea la base | Un valor aleatorio (solo letras, dígitos, `-` y `_`) |
| `POSTGRES_DB` | Nombre de la base | `alerta_temprana` |
| `DB_HOST`, `DB_PORT` | Dónde buscan la base los procesos que corren **fuera** de Docker (pruebas, scripts y uvicorn de la sección 10). Dentro de Docker, `compose.yaml` usa `db:5432` y estos valores no se usan | `127.0.0.1` y `5432` (otro, por ejemplo `15432`, si el 5432 está ocupado) |
| `SEUDONIMO_CLAVE` | Clave secreta del HMAC que genera los códigos seudonimizados de los estudiantes (HU-001) | Un valor largo y aleatorio |
| `SEMILLA`, `CAPACIDAD_TUTORIAS`, `DETECCION_MINIMA`, `AUC_MINIMO_CIERRE_1S` | Parámetros metodológicos del documento: semilla 42, nivel alto ≤ 15 %, alto + medio ≥ 80 % de los abandonos, AUC-ROC > 0,80 | No los cambies |

**Sobre `SEUDONIMO_CLAVE`.** Alcanza con cualquier valor largo y aleatorio. Los códigos
`EST-…` que aparecen en el documento y en el video se generaron con la clave del autor: con
otra clave **cambian los códigos**, pero **no cambian las probabilidades, los niveles de
urgencia ni las cantidades**. Para ver exactamente el estado de la demo (los mismos códigos
y los mismos estados de seguimiento), restaurá el respaldo de la carpeta compartida
(sección 5). Después de restaurarlo **no vuelvas a cargar los archivos** con tu clave: los
mismos estudiantes entrarían con otros códigos y quedarían duplicados.

**3. Levantar la plataforma**

```powershell
docker compose up -d --build
```

La primera vez tarda unos minutos, porque construye la imagen. Al iniciar, la aplicación
crea las tablas, los cuatro roles, un usuario de prueba por rol y las filas de MODELO de
los tres modelos de `modelos/`. Para comprobar que los dos contenedores están en marcha:

```powershell
docker compose ps        # app y db en «healthy»; app en 127.0.0.1:8000->8000/tcp
```

**4. Abrir** http://127.0.0.1:8000. El estado está en http://127.0.0.1:8000/salud
(`{"estado":"ok","base_de_datos":"ok"}`).

Para detenerla: `docker compose stop` (los datos se conservan). Para volver a levantarla:
`docker compose up -d`.

## 4. Uso de la demo (manual de usuario breve)

Arriba a la derecha está el **selector de usuario de prueba**. El usuario elegido define el
menú y queda registrado en las cargas y en los cambios de estado.

| Usuario | Rol | Qué puede hacer |
|---|---|---|
| `sistemas01` (por defecto) | Área de Sistemas | Cargar los archivos (Carga de datos) |
| `coordinacion01` | Coordinación del Programa de Tutorías | Listado, ficha y cambio de estado |
| `tutor01` | Tutor/a | Listado, ficha y cambio de estado (en el Sprint 1 ve todas las alertas: la asignación a tutores es HU-011) |
| `secretaria01` | Secretaría Académica | Solo ve el aviso de que el panel de métricas (HU-008) no forma parte del prototipo |

**1. Cargar los tres archivos, en orden** (usuario `sistemas01`, pantalla «Carga de
datos»). En cada carga elegí el momento de predicción y arrastrá el archivo:

| Orden | Archivo | Momento de predicción | Resultado esperado |
|---|---|---|---|
| 1 | `data/cargas/exportacion_inscripcion.csv` | Inscripción | 885 válidos, 0 rechazados; 117 en nivel alto |
| 2 | `data/cargas/exportacion_cierre_1s.csv` | Cierre del 1.er semestre | 885 válidos; 134 en nivel alto |
| 3 | `data/cargas/exportacion_cierre_2s.csv` | Cierre del 2.º semestre | 885 válidos; 137 en nivel alto |

Después de cada carga, el riesgo se recalcula solo y en segundo plano. La tarjeta «Cálculo
del riesgo» pasa de «en curso» a «Completado: modelo v1.0 (…)» con los estudiantes por
nivel, y la barra superior muestra la «Última actualización». Las columnas identificatorias
y las variables excluidas de los archivos se descartan en la carga, y la pantalla las lista.
Con las tres cargas quedan **529 alertas: 137 en nivel alto, 131 en medio y 261 en bajo**.

Lo mismo se puede hacer por la API interna:

```powershell
curl.exe -F "archivo=@data/cargas/exportacion_inscripcion.csv" -F momento=inscripcion -F usuario=sistemas01 http://127.0.0.1:8000/api/cargas
curl.exe -F "archivo=@data/cargas/exportacion_cierre_1s.csv" -F momento=cierre_1s -F usuario=sistemas01 http://127.0.0.1:8000/api/cargas
curl.exe -F "archivo=@data/cargas/exportacion_cierre_2s.csv" -F momento=cierre_2s -F usuario=sistemas01 http://127.0.0.1:8000/api/cargas
```

(En bash, `curl` en lugar de `curl.exe`. Esperá a que termine cada cálculo antes de la carga
siguiente.)

**2. Listado de alertas** (usuario `coordinacion01` o `tutor01`). Muestra todas las alertas
ordenadas por nivel de urgencia (alto, medio y bajo) y, dentro de cada nivel, por
probabilidad de mayor a menor. Tiene filtros por carrera, turno, nivel y estado de
seguimiento, y tarjetas con los totales de nivel alto, nivel medio y pendientes de contacto.
El nivel se muestra con color y texto.

**3. Ficha del estudiante** («Ver ficha» en una fila): probabilidad de abandono, nivel de
urgencia, carrera y turno, fecha y modelo del cálculo, y los **cinco factores que más pesan
en la estimación**, con una barra proporcional y la indicación «Aumenta el riesgo» o
«Disminuye el riesgo». El aviso recuerda que los factores no son causas y que la ficha no
reemplaza el criterio del tutor.

**4. Cambiar el estado de seguimiento** (pendiente, contactado o en acompañamiento): en
el listado, con el desplegable de la fila y «Guardar»; en la ficha, con «Guardar estado».
Cada cambio queda registrado con el estado anterior, el nuevo, el usuario y la fecha y hora
(tabla CAMBIO_ESTADO), y se conserva aunque el riesgo se recalcule. Por la API:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/alertas/1/estado -ContentType 'application/json' -Body '{"estado": "contactado", "usuario": "tutor01"}'
```

```bash
curl -X POST -H "Content-Type: application/json" -d '{"estado": "contactado", "usuario": "tutor01"}' http://127.0.0.1:8000/api/alertas/1/estado
```

## 5. Respaldo, restauración y vaciado de la base

Los scripts están en `scripts/` y funcionan desde cualquier carpeta. Usan el usuario y la
base del contenedor `db`, así que no leen `.env`, y la base tiene que estar en marcha
(`docker compose up -d`). Los respaldos se guardan en `respaldos/`, que no se versiona.

Si PowerShell no deja ejecutar scripts («la ejecución de scripts está deshabilitada»),
anteponé `powershell -ExecutionPolicy Bypass -File`, como en los ejemplos.

| Acción | PowerShell | bash |
|---|---|---|
| Respaldo completo | `powershell -ExecutionPolicy Bypass -File scripts\respaldar.ps1 -Etiqueta demo` | `sh scripts/respaldar.sh demo` |
| Restauración | `powershell -ExecutionPolicy Bypass -File scripts\restaurar.ps1 respaldos\demo_20261109-2000.dump` | `sh scripts/restaurar.sh respaldos/demo_20261109-2000.dump` |
| Verificación | `powershell -ExecutionPolicy Bypass -File scripts\verificar.ps1` | `sh scripts/verificar.sh` |

- **Respaldo** (`respaldar`): `pg_dump` en formato custom (`-Fc`) hacia
  `respaldos/<etiqueta>_<AAAAMMDD-HHMM>.dump`. La etiqueta es opcional: por defecto es
  `respaldo`, admite letras sin acento, dígitos, `-` y `_`, y los espacios pasan a `-`. El
  archivo se genera dentro del contenedor y se copia con `docker compose cp`, porque la
  redirección `>` de PowerShell corrompe el binario. Al terminar se controla que
  `pg_restore` pueda leerlo.
- **Restauración** (`restaurar`): **reemplaza todo el contenido de la base** por el del
  respaldo. Pide escribir `SI` (con `-Si` o `--si` no pregunta). Detiene el contenedor de la
  aplicación, restaura con `pg_restore --clean --if-exists` en una sola transacción y vuelve
  a levantar la aplicación. Si la restauración falla, la base queda como estaba y la
  aplicación se vuelve a levantar igual. Al arrancar sobre una base restaurada, la
  aplicación no duplica nada: solo crea las tablas, los roles, los usuarios de prueba y las
  filas de MODELO que falten, y antes de usar cada modelo controla la huella SHA-256 de su
  archivo.
- **Verificación** (`verificar`, solo lee): estudiantes, cargas por momento, alertas por
  nivel y por estado de seguimiento, filas de CAMBIO_ESTADO, modelos (y cuáles están
  habilitados), roles y usuarios. Con las tres cargas da 885 estudiantes y 529 alertas (137
  en alto, 131 en medio y 261 en bajo).

**Vaciar la base** (borra cargas, estudiantes, predicciones, alertas y seguimiento):

```powershell
docker compose down -v      # borra los contenedores y el volumen datos_db
docker compose up -d        # al iniciar, la aplicación vuelve a crear todo
```

Al volver a levantarla, la aplicación recrea las tablas, los 4 roles, los 4 usuarios de
prueba y los 3 modelos habilitados en MODELO. `verificar` lo muestra: 0 estudiantes,
4 roles, 4 usuarios y 3 modelos habilitados.

**Restauración probada (09/11/2026)** sobre la base de la demo, con los scripts de
PowerShell y de bash: respaldo (229 KB, 11 tablas con datos) → `down -v` → `up -d`
(0 estudiantes, 4 roles, 4 usuarios, 3 modelos) → restauración → `verificar` igual que antes
del respaldo (885 estudiantes, 3 cargas, 529 alertas 137/131/261, 2 cambios de estado,
2.655 predicciones, 885 vigentes). Después se reinició la aplicación dos veces sin filas
duplicadas, con las secuencias al día y la SHA-256 de los tres modelos verificada. También
se probó una restauración fallida (un archivo que no es un respaldo): la base quedó intacta
y la aplicación se volvió a levantar.

## 6. Pruebas

Las pruebas necesitan Python 3.13 con el entorno virtual (sección 10) y la base publicada en
`127.0.0.1` con `compose.dev.yaml`. Usan una base aparte (`<POSTGRES_DB>_pruebas`), así
que no tocan los datos de la demo.

```powershell
docker compose -f compose.yaml -f compose.dev.yaml up -d
.\.venv\Scripts\Activate.ps1
pytest                     # 312 pruebas
pytest -m "not db"         # sin base de datos
```

Hay **312 pruebas**, y el resultado esperado es **312 passed, 0 skipped**. Si la base no
está publicada, las pruebas marcadas con `db` se saltean («PostgreSQL no disponible»), y
ese resultado no cuenta como verde. Las marcadas con `datos` necesitan el dataset
(`python scripts/descargar_datos.py`).

## 7. Correspondencia con el documento

Sprint 1: HU-001 a HU-007. Los módulos están en `src/alerta_temprana/`, los endpoints son
de la API interna y las pruebas, en `tests/`.

| Historia | Módulos | Pantalla | Endpoints | Pruebas |
|---|---|---|---|---|
| HU-001 Carga y validación de datos de estudiantes | `datos/carga.py`, `datos/validacion.py`, `datos/seudonimizacion.py`, `datos/variables.py`, `servicio/carga.py`, `db/tablas.py`, `ui/carga.py` | Carga de datos (Figura 5) | `POST /api/cargas`, `GET /api/cargas` | `test_hu001_*.py` (59) |
| HU-002 Entrenamiento y evaluación del modelo de riesgo | `modelo/` (preparación, entrenamiento, evaluación, umbrales, explicaciones, persistencia, `candado_prueba.py`); `scripts/entrenar.py`, `scripts/evaluar_final.py` | — (informes en `reportes/`) | — | `test_hu002.py`, `test_modelo.py`, `test_dataset.py`, `test_variables.py` (75) |
| HU-003 Estimación y actualización automática del riesgo | `servicio/planificador.py`, `servicio/prediccion.py`, `servicio/modelos.py`, `ui/actualizacion.py` | Tarjeta «Cálculo del riesgo» y «Última actualización» en la barra superior | `GET /api/cargas/{id_carga}/recalculo`, `GET /api/predicciones/ultima-actualizacion` | `test_hu003.py` (34) |
| HU-004 Clasificación por niveles de urgencia | `modelo/umbrales.py`, `servicio/prediccion.py`, `servicio/alertas.py` | Nivel con color y texto en el listado y la ficha | (en las respuestas de alertas) | `test_hu004.py` (20) |
| HU-005 Listado de alertas tempranas | `servicio/alertas.py`, `ui/listado.py` | Listado de alertas (Figura 6) | `GET /api/alertas` | `test_hu005.py` (46) |
| HU-006 Ficha del estudiante con la explicación del riesgo | `servicio/ficha.py`, `modelo/explicaciones.py`, `modelo/etiquetas.py`, `ui/ficha.py` | Ficha del estudiante (Figura 7) | `GET /api/alertas/{id_alerta}` | `test_hu006.py` (33) |
| HU-007 Registro del estado de seguimiento | `servicio/seguimiento.py`, `ui/seguimiento.py` | Listado y ficha (sección «Seguimiento») | `POST /api/alertas/{id_alerta}/estado` | `test_hu007.py` (35) |

Las 10 pruebas restantes (`test_entorno.py`) controlan que estén instaladas las bibliotecas
del stack y que la aplicación responda en `/salud`. Total: 312.

**Fuera del Sprint 1** (no implementado, product backlog del documento): HU-008 Panel de
métricas institucionales, HU-009 Acceso de usuarios según rol, HU-010 Consulta de
predicciones mediante API, HU-011 Asignación de alertas a tutores, HU-012 Registro de
intervenciones, HU-013 Ajuste de umbrales de urgencia, HU-014 Reentrenamiento periódico del
modelo y HU-015 Evaluación de resultados del acompañamiento.

La especificación completa está en [`docs/`](docs/) (empezá por
[`docs/sprint-1/README.md`](docs/sprint-1/README.md)). Las decisiones de implementación
(P1 a P11 y las posteriores) están en
[`docs/proyecto/08-decisiones.md`](docs/proyecto/08-decisiones.md).

## 8. Fuente de los datos

Realinho, V., Vieira Martins, M., Machado, J. y Baptista, L. (2021). *Predict students'
dropout and academic success* [Conjunto de datos]. UCI Machine Learning Repository.
https://doi.org/10.24432/C5MC89. Licencia **CC BY 4.0**. El conjunto es público y está
anonimizado (4.424 estudiantes, 37 columnas).

- **`data/raw/`** (no se versiona): el archivo original se descarga y se verifica con
  `python scripts/descargar_datos.py` (huella SHA-256 en `data/raw/fuente.json`).
- **`data/procesados/particion.csv`** (versionado): la partición estratificada 60/20/20
  con semilla 42, la misma para los tres momentos. Tiene solo el índice y el conjunto, sin
  la variable objetivo (`scripts/preparar_particion.py`).
- **`data/cargas/`** (versionado): los tres archivos de carga simulados, **derivados del
  conjunto de prueba de Realinho et al. (2021), con licencia CC BY 4.0. Se agregaron
  identificadores sintéticos y se quitó la situación final.** Cada archivo es una
  exportación simulada, una por momento de predicción, con todo lo disponible hasta ese
  momento. Los identificadores (`legajo`, `documento` y `apellido_nombre`) son sintéticos,
  constantes entre los tres archivos, y la plataforma los descarta al cargar. También
  incluyen las cinco variables excluidas, para mostrar que se descartan. Se generan con
  `python scripts/generar_cargas.py` a partir de `data/raw/data.csv` y de la partición
  (decisión P2).
- **Informe de evaluación:** [`reportes/informe_evaluacion.md`](reportes/informe_evaluacion.md)
  (AUC-ROC en prueba, umbrales, subgrupos y comparación con la regresión logística). El
  análisis exploratorio está en [`reportes/informe_exploratorio.md`](reportes/informe_exploratorio.md)
  y los modelos, con sus metadatos, en `modelos/<momento>/v1.0/`.

## 9. Problemas comunes

| Síntoma | Causa y solución |
|---|---|
| `Bind for 127.0.0.1:8000 failed: port is already allocated` | Otro programa usa el puerto 8000 (por ejemplo, otra copia de la plataforma o un `uvicorn`). Cerralo, o detené la otra copia con `docker compose stop` desde su carpeta. |
| `error during connect … dockerDesktopLinuxEngine` o `Cannot connect to the Docker daemon` | Docker no está iniciado. Abrí Docker Desktop (o `sudo systemctl start docker`), esperá a que diga «Engine running» y repetí el comando. |
| En la carga: «No se calcularon riesgos: no hay un modelo habilitado para el momento…» | MODELO no tiene un modelo habilitado para ese momento. Pasa si falta `modelos/<momento>/v1.0/` (clon incompleto) o si la base se creó cuando no estaba. Comprobá que existan los tres `metadatos.json` y `pipeline.joblib` y reiniciá la aplicación (`docker compose restart app`): al iniciar agrega los modelos que falten. `verificar` muestra los modelos habilitados. |
| «El archivo del modelo … no coincide con la huella SHA-256» | `pipeline.joblib` cambió o está dañado (por ejemplo, por una conversión de fin de línea). Volvé a obtenerlo del repositorio (`git checkout -- modelos/`). |
| `/salud` dice `"base_de_datos": "sin conexión"` | La aplicación arranca aunque la base no responda (su control de salud no depende de la base). Revisá `docker compose ps` y `docker compose logs db`. |
| `password authentication failed` después de cambiar `POSTGRES_PASSWORD` | La contraseña se fija la primera vez que se crea el volumen. Volvé a la anterior, o respaldá, vaciá con `docker compose down -v` y restaurá. |
| PowerShell: «la ejecución de scripts está deshabilitada» | Usá `powershell -ExecutionPolicy Bypass -File scripts\<script>.ps1`. |
| El listado tarda 2 a 3 segundos al cambiar un filtro | Es esperable con 529 alertas: cada fila tiene su desplegable de estado (limitación conocida del prototipo). |

## 10. Instalación para desarrollo

Para correr las pruebas, los scripts del modelo o la aplicación con recarga automática.
Requiere además **Python 3.13** (Windows, PowerShell):

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

# 5. Base de datos publicada solo en 127.0.0.1:DB_PORT (compose.dev.yaml)
docker compose -f compose.yaml -f compose.dev.yaml up -d db

# 6. Control del entorno y pruebas
python scripts/verificar_entorno.py
pytest
```

Si PowerShell no deja activar el entorno: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
Si el puerto 5432 está ocupado (por ejemplo, por un PostgreSQL instalado en el equipo),
cambiá `DB_PORT` en `.env` (por ejemplo, a 15432) y repetí el paso 5.

**Aplicación con recarga automática** (en lugar del contenedor `app`, que tiene que estar
detenido porque usa el mismo puerto 8000):

```powershell
docker compose -f compose.yaml -f compose.dev.yaml up -d db
uvicorn alerta_temprana.app:app --reload
```

`compose.dev.yaml` es solo para desarrollo: publica la base en `127.0.0.1:${DB_PORT}` para
que la alcancen pytest, los scripts y uvicorn (con `DB_HOST=127.0.0.1`). La versión que se
entrega (`docker compose up`, solo con `compose.yaml`) no publica la base.

**Regenerar los archivos de carga** (no hace falta: ya están versionados):
`python scripts/descargar_datos.py`, `python scripts/preparar_particion.py` (no modifica una
partición que ya existe) y `python scripts/generar_cargas.py`.

No cargues los archivos de `tests/fixtures/` en la base de la demo: son estudiantes
sintéticos de prueba y aparecerían en el listado.

### Estructura

```
src/alerta_temprana/   código de la aplicación (datos, modelo, servicio, db, api, ui)
scripts/               descarga de datos, entrenamiento, evaluación, respaldo y restauración
tests/                 pruebas (pytest)
data/                  partición y archivos de carga (versionados); dataset (se descarga)
modelos/               modelos entrenados con sus metadatos
reportes/              informe exploratorio, informe de evaluación y cuestionario
docs/                  especificación: contexto, datos, CRISP-DM, pantallas, historias
```

## Licencia y créditos

Código: uso académico. Datos: Realinho, V., Vieira Martins, M., Machado, J. y Baptista, L.
(2021). *Predict students' dropout and academic success* [Conjunto de datos]. UCI Machine
Learning Repository. https://doi.org/10.24432/C5MC89. Licencia CC BY 4.0. Los archivos de
`data/cargas/` derivan de ese conjunto: se agregaron identificadores sintéticos y se quitó
la situación final.
