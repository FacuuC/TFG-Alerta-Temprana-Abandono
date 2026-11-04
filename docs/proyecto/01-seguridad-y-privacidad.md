# Seguridad y privacidad: qué implementa el prototipo

Fuente: secciones Propuesta (tratamiento de datos personales) y Seguridad del documento,
y «E4 - Seguridad - Definición de requerimientos» (24-26/10). El proyecto integral
describe muchos más controles (multifactor, HTTPS, respaldos en dos regiones, SLA);
**acá solo va lo que el prototipo tiene que cumplir al 09/11**, para que el código y la
sección Seguridad del documento digan lo mismo.

## Privacidad (Ley N.º 25.326)

- **Minimización:** al cargar un archivo se descartan las variables que el modelo no usa
  y las excluidas (necesidades educativas especiales, por ser dato sensible; deudor,
  aranceles al día, orden de postulación y nota de admisión, por no tener equivalente).
- **Seudonimización:** nombre, documento y legajo se reemplazan por un código
  (`codigo_estudiante`, VARCHAR(12)). La plataforma **no guarda la correspondencia**
  entre código y estudiante ni el archivo original de la exportación.
- **Sin datos identificatorios en pantalla:** el tutor identifica al estudiante a partir
  del código, en el sistema de gestión académica al que ya accede por su función.
- **Finalidad:** las alertas sirven solo para ofrecer acompañamiento; no se usan para
  sanciones ni becas. La ficha lo aclara.
- **Sesgos:** evaluación por subgrupos (género, edad de ingreso, becario) con AUC-ROC,
  sensibilidad y precisión. SHAP no prueba ausencia de sesgo.
- **El prototipo no trata datos identificables reales:** usa el conjunto público y
  anonimizado de Realinho et al. (2021). Los identificadores de los archivos de carga
  simulados (legajo, documento) son sintéticos.

## Controles del prototipo (antes del 09/11)

| Control | Dónde | Estado |
|---|---|---|
| Repositorio Git desde el primer commit; etiqueta `v0.1` en la versión entregada | Git | Primer commit: al crear el repositorio |
| Secretos en `.env`, fuera del repositorio; `.env.example` de muestra; `.gitignore` con secretos, datos y archivos generados | Raíz | Listo |
| Docker Compose: base sin puertos publicados, red interna (`internal: true`), reinicio automático y controles de salud | `compose.yaml` | Listo |
| Puerto de la aplicación solo en `127.0.0.1` | `compose.yaml` | Listo |
| Contenedor de la aplicación con usuario sin privilegios | `Dockerfile` | Listo |
| Scripts de respaldo y restauración de la base, una restauración de prueba documentada en el manual de instalación | `scripts/` | Cierre del sprint |
| Validación y seudonimización de la carga | HU-001 | Sprint 1 |
| Aviso de la ficha: no reemplaza el criterio del tutor; los factores no son causas | HU-006, criterio 4 | Sprint 1 |
| Registro de quién cambió cada estado de seguimiento y cuándo | HU-007 (tabla CAMBIO_ESTADO) | Sprint 1 |

El prototipo corre en local y sin HTTPS (se declara como limitación). El repositorio es
público y no contiene datos de estudiantes ni credenciales.

## Sprint 2 (después del 09/11, antes de la defensa): no implementar ahora

HU-009: usuario y contraseña con Argon2id o bcrypt, roles tutor y Área de Sistemas con
restricción de pantallas, bloqueo a los 5 intentos fallidos, cierre por inactividad y
registro de inicios de sesión. Las tablas USUARIO y ROL ya existen en el Sprint 1 (con un
usuario de prueba por rol), así que HU-009 no cambia el modelo de datos.
