# Pendientes para la versión final del documento

Inconsistencias entre el documento (entrega 3 + avance de la entrega 4, al 02/11) y lo que
se implementa. **No se editan ahora:** se aplican junto con las correcciones del tutor,
cuando lleguen. Al implementar, sumá acá cualquier diferencia nueva.

## Fechas del sprint

- [ ] Herramientas Metodológicas: «El Sprint 1, que finaliza el 2 de noviembre» → fechas
  reales del sprint.
- [ ] Planificación: hito «sistema funcional integrado (02/11)» y Gantt de la fase 3.
- [ ] Sprint backlog: columna «Estado» y burndown con el avance real (`sprint-1/avance.md`).

## Prototipos de pantalla (al final, reemplazar por capturas reales)

- [ ] Figura 7 (ficha): «Factores que más influyen» → «Factores que más pesan»
  (término fijo de la obs. 18). *Se resuelve con las capturas reales (bloque C).*
- [ ] Figura 7: aparece «Aranceles al día: no», una variable **excluida** del modelo. *Se resuelve con las capturas reales (bloque C).*
- [ ] Figura 7: el aviso no dice que los factores no son causas (HU-006, criterio 4). *Se resuelve con las capturas reales (bloque C).*
- [ ] Figura 7 (ficha real, HU-006, 09/11): la tarjeta «Cálculo» muestra fecha **y hora**
  («08/11/2026 23:57 · modelo v1.0 (Cierre del 2.º semestre)»), igual que la última
  actualización de la barra superior; arriba hay un enlace «← Volver al listado»; el título
  es «Ficha del estudiante EST-…». La sección «Seguimiento» (HU-007) tiene el desplegable,
  «Guardar estado» y «Alerta creada el…», como la figura, y además el mensaje de
  confirmación y la línea «Último cambio: Pendiente → Contactado, por tutor01, el
  dd/mm/aaaa hh:mm» (ver «Seguimiento», más abajo). *Se resuelve con las capturas reales (bloque C).*
- [ ] Figura 7 y Anexo: la ficha muestra la predicción **vigente** (con las tres cargas de
  la Demo, la de cierre del 2.º semestre), mientras que las seis fichas del Anexo son de
  cierre del 1.er semestre. Los PNG del Anexo no se reemplazan por capturas. Con solo las
  cargas de inscripción y de cierre del 1.er semestre, la pantalla muestra lo mismo que esas
  fichas (prueba de `tests/test_hu006.py`). *Se resuelve con las capturas reales (bloque C).*
- [ ] Ficha, explicación no válida: si un factor guardado no corresponde al momento del
  modelo (por ejemplo, una variable excluida) o no hay cinco, la ficha no muestra ningún
  factor y aparece «No se puede mostrar la explicación de esta alerta.»; el detalle queda en
  el registro de la aplicación. Con los modelos v1.0 no ocurre (es un control). Mencionarlo si
  se describe cómo se garantiza que no aparezcan variables excluidas.
- [ ] Figura 5 (carga): «Momento del período» → «Momento de predicción»; en «Cargas
  anteriores», «Ingreso» → «Inscripción».
- [ ] Figuras 6 y 7: códigos de 6 caracteres (`EST-7F3A21`); con la decisión P1 son de 8
  (`EST-7F3A21C4`). *Se resuelve con las capturas reales (bloque C).*
- [ ] Figuras 5 a 7: «Cerrar sesión» no existe en el Sprint 1 (selector de usuario de prueba). *Se resuelve con las capturas reales (bloque C).*
- [ ] Figura 6: «Última actualización · modelo» aparece en la barra superior (común a
  todas las pantallas), no a la derecha de los filtros. *Se resuelve con las capturas reales (bloque C).*
- [ ] Figura 6 (listado) y alcance del prototipo: en el prototipo, el usuario Tutor/a ve
  **todas** las alertas, no solo las de sus estudiantes, porque la asignación a tutores es
  HU-011 y la restricción por rol, HU-009 (las dos fuera del Sprint 1). Aclararlo en el
  texto de la Figura 6 o en las limitaciones del prototipo. *Se resuelve con las capturas reales (bloque C).*
- [ ] Tabla de roles y alcance del prototipo: en el prototipo, el usuario de prueba elegido
  define el menú y la pantalla que se muestra (Área de Sistemas → carga; Coordinación y
  Tutor/a → listado; Secretaría Académica → aviso de que el panel de métricas, HU-008, no
  forma parte del prototipo). Es **navegación, no control de acceso**: cualquiera puede
  elegir cualquier usuario y la API interna no restringe por rol. La restricción real
  llega con el inicio de sesión por rol (HU-009, Sprint 2). Aclararlo en las limitaciones.

## Texto

- [ ] Sprint backlog, tarea 1.1: «contenedores Docker de la API, la base de datos y el
  panel» → la Figura 9 muestra dos contenedores (aplicación y datos).
- [ ] Diagrama de Arquitectura (Figura 9): ubica los «modelos versionados (volumen de
  archivos)» en el contenedor de datos. En el prototipo, el contenedor `db` guarda solo la
  tabla MODELO (versión, momento, métricas, umbrales, habilitado). Los archivos de cada modelo
  (`modelos/<momento>/v<versión>/`: pipeline y `metadatos.json`) están en el repositorio del
  equipo anfitrión y se montan **de solo lectura** en el contenedor `app` (`/app/modelos`), que
  es el único que los lee. No están en la imagen (`.dockerignore`) ni en un volumen con nombre.
  Corregir el texto (o la figura) para que los modelos queden del lado de la aplicación.
- [ ] Alcance del prototipo, ítem 3: «en cada ingesta de datos» → «en cada carga de datos».
- [ ] Tabla 13 (Propuesta), fila «Registro del desempeño»: «La ingesta de datos» → «La
  carga de datos».
- [ ] Herramientas de Software, párrafo de Dash: «simplifica el despliegue del sistema
  SaaS» (bloque 3 del paquete de cambios de la E3, sin aplicar).
- [ ] Diagrama de Arquitectura, texto: «HTPPS» → «HTTPS».
- [ ] Tabla 32: las descripciones dicen «código de 1 a 17» (carrera), «1 a 18» (modalidad),
  «1 a 21» (nacionalidad), «1 a 17» (título previo), que son los códigos del anexo del
  artículo. **Confirmado el 03/11:** el archivo de UCI usa los códigos originales (carrera
  de 33 a 9991, nacionalidad de 1 a 109, modalidad de 1 a 57, título previo de 1 a 43,
  ocupaciones de 0 a 195). Cambiar a «código (ver anexo)» y la longitud de carrera a 4 y
  de nacionalidad, título previo, niveles educativos y ocupaciones a 3.

## Modelado (resultados del 03/11)

- [ ] CRISP-DM, fase de modelado: indicar la grilla usada (profundidad 2 a 5, tasa 0,03 a
  0,1, 100 a 400 árboles) y que se extendió porque la inicial dejaba el óptimo en el borde.
- [ ] CRISP-DM, fase de evaluación: en `cierre_1s`, XGBoost (0,8878) y la regresión
  logística (0,8871) quedaron prácticamente empatados en validación; se aplicó la regla
  («XGBoost solo si supera a la referencia»). Comentarlo en las Conclusiones junto con
  Bettahi et al. (2025, p. 18).
- [ ] Umbrales resultantes (alto 0,8936 y medio 0,5301): con la capacidad del 15 %, un
  estudiante con probabilidad 0,81 queda en nivel medio y uno con 0,45, en bajo. Vale
  explicarlo en el texto, porque las fichas del Anexo muestran casos así (caso 3: 0,81,
  nivel medio).

## Evaluación final (decisiones del 04/11)

- [ ] CRISP-DM, fase de evaluación: mencionar que la referencia (o la alternativa no elegida)
  **también se informa en prueba, solo como comparación**: la elección del modelo se hizo en
  validación antes de ver la prueba, y el modelo habilitado no cambia aunque la alternativa
  salga mejor.
- [ ] CRISP-DM, fase de evaluación: definir «peso alto» de una variable demográfica (estar
  entre las 5 de mayor media |SHAP|).

## Evaluación final (resultados del 04/11, `reportes/informe_evaluacion.md`)

- [ ] **Umbrales en prueba (HU-004, criterio 5): no alcanzado.** Se informa tal cual, sin
  reajustar (decisión del 04/11). La proporción de abandonos decrece de alto a bajo en los
  tres momentos, pero:

  | Momento | Nivel alto (≤ 15 %) | Detección alto + medio (≥ 80 %) |
  |---|---|---|
  | Inscripción | 13,2 % (sí) | 79,2 % (no) |
  | Cierre del 1.er semestre | 15,1 % (no) | 74,6 % (no) |
  | Cierre del 2.º semestre | 15,5 % (no) | 76,1 % (no) |

  Explicar en Conclusiones que los umbrales se fijan en validación (donde detectan el 80,0 %)
  y que en prueba la detección baja; en la plataforma conviene presentar la capacidad y la
  detección como metas aproximadas, no garantizadas.
- [ ] **Subgrupos (cierre_1s):** el AUC-ROC es parejo (0,84 a 0,93), pero la sensibilidad no:
  hasta 20 años 0,564 frente a más de 25 años 0,893; becarios 0,536 frente a no becarios
  0,770; femenino 0,683 frente a masculino 0,810. La edad de ingreso es la 2.ª variable de
  mayor peso SHAP (única demográfica con «peso alto»). Comentarlo como riesgo de sesgo: el
  modelo deja sin alerta a una parte mayor de los abandonos de jóvenes y becarios.
- [ ] **Comparación con la referencia en prueba (solo informativa):** XGBoost supera a la
  regresión logística en los tres momentos (inscripción 0,7861 frente a 0,7752; cierre_1s
  0,8928 frente a 0,8838; cierre_2s 0,9177 frente a 0,9159).
- [ ] **Anticipación frente a precisión:** AUC-ROC 0,7861 (inscripción), 0,8928 (cierre del
  1.er semestre, meta > 0,80 alcanzada) y 0,9177 (cierre del 2.º semestre); los tres
  habilitados. Sin «sigue cursando», el AUC-ROC de cierre_1s sube a 0,9255.
- [ ] **Fecha de entrenamiento del informe en UTC:** la columna «Entrenado» del informe
  muestra la fecha UTC de `metadatos.json` (cierre_1s: `2026-11-04T00:01:28+00:00`, que es
  el **03/11 a las 21:01, hora argentina**, coherente con el congelamiento del 03/11). Si se
  cita en el documento, aclararlo. El informe actual no se modifica (regenerarlo volvería a
  usar la prueba); `informe_evaluacion.py` ya muestra dd/mm/aaaa en hora argentina para
  futuras evaluaciones.

## Modelado de inscripción y cierre del 2.º semestre (04/11)

- [ ] Con la misma grilla, en `inscripcion` (AUC validación 0,7701 frente a 0,7673 de la
  regresión logística) y en `cierre_2s` (0,9147 frente a 0,9128) XGBoost supera a la
  referencia por muy poco, y el óptimo vuelve a quedar en el borde (profundidad 2, tasa 0,1),
  como en `cierre_1s`. No se extendió la grilla (misma para los tres momentos). Comentarlo
  junto con el empate de `cierre_1s`: con estos datos, modelos simples rinden casi igual.

## Análisis exploratorio (resultados del 04/11)

- [ ] Limitaciones de los datos: los 180 estudiantes con 0 materias inscriptas en el 1.er
  semestre son **todos** de Diseño de Animación y Multimedia (código 171; 180 de sus 215) y
  tienen en cero las doce variables de rendimiento, aunque hay graduados entre ellos. Lo más
  probable es que falte el registro de esa carrera en la fuente. Se mantienen sin cambios
  (`reportes/informe_exploratorio.md`, sección 7); mencionarlo en Datos y en Conclusiones,
  porque las estimaciones de cierre de semestre para esa carrera son menos confiables.
- [ ] CRISP-DM, comprensión de los datos: el análisis que relaciona variables con el abandono
  se hizo solo con entrenamiento (decisión del 04/11).

## Carga de datos (HU-001, 04/11)

- [x] **Seguridad: el selector de usuario no es un control de acceso.** En el Sprint 1 no
  hay inicio de sesión: cualquiera que abra la plataforma puede elegir otro usuario de
  prueba. El rol solo se controla para que la carga quede registrada a nombre del Área de
  Sistemas (decisión P5); el control de acceso real es HU-009 (Sprint 2). Declararlo en la
  sección Seguridad y en las limitaciones del prototipo.
  **Hecho el 07/11:** apartado «Entorno de demostración» en `proyecto/01-seguridad-y-privacidad.md`,
  `proyecto/02-arquitectura.md` y el `README.md` (solo en el equipo local, con el puerto
  publicado en `127.0.0.1:8000`; solo con el conjunto público; el selector no es un control
  de acceso, HU-009). Al pasarlo al documento, usar ese mismo texto en Seguridad y en las
  limitaciones del prototipo, y repetirlo en el manual de instalación.
- [ ] **Informe de errores sin guardar:** se descarga al terminar la carga y no se guarda en
  la base (CARGA no tiene un campo para él y así se respeta la minimización). Si se sale de
  la pantalla, no se puede volver a descargar. Declararlo como limitación.
- [ ] **Datos ya cargados no se actualizan:** si una exportación posterior trae datos de
  inscripción o de un semestre ya cargado con otros valores (una corrección), la corrección no
  entra (no hay edición de datos cargados, fuera de alcance). Declararlo como limitación.
- [ ] **Nota promedio redondeada (Tabla 32, NUMERIC(4,2)):** el archivo de UCI tiene notas
  del semestre con más decimales (1.790 del 1.er semestre); la base las guarda con 2. Medido
  el 04/11 con los modelos v1.0: la probabilidad cambia como máximo 0,09 en un estudiante de
  validación, **ningún nivel cambia** (0 de 885 en validación y en prueba, en los tres
  momentos) y las 6 fichas dan las mismas probabilidades con 4 decimales. Se mantiene el tipo
  del documento; mencionarlo si se describe el diccionario de datos.
- [ ] Figura 5: la pantalla real agrega «Estudiantes nuevos», «Ya existentes» y
  «Rendimientos semestrales agregados», y lista las columnas descartadas.

## Recálculo del riesgo y alertas (HU-003 y HU-004, 05/11)

- [ ] **Diccionario de datos / DER:** se agregaron dos restricciones, sin cambiar campos:
  una sola predicción vigente por estudiante (índice único parcial sobre PREDICCION) y una
  sola alerta por estudiante (decisión P3). Mencionarlas junto con «un solo modelo
  habilitado por momento».
- [ ] **FACTOR_EXPLICATIVO.valor** guarda el valor sin formatear («9500», «2», «13.9»): con
  VARCHAR(40) no entran algunos textos comprensibles (por ejemplo, «curso complementario de
  contabilidad y administración», 53 caracteres). La ficha lo muestra con su nombre y formato.
- [ ] **METRICA_SUBGRUPO queda vacía en el prototipo:** las métricas por subgrupo están en
  `reportes/informe_evaluacion.md` y solo las usaría el panel de métricas (HU-008, diseño
  integral). MODELO sí se llena desde los metadatos al iniciar la plataforma.
- [ ] **Figura 5 (carga):** el resultado agrega la tarjeta «Cálculo del riesgo» (en curso →
  «Completado: modelo v1.0 (Cierre del 1.er semestre) · 885 estudiantes», con los estudiantes
  por nivel y las alertas nuevas y actualizadas, o el motivo si no se calculó). La barra
  superior muestra «Última actualización: dd/mm/aaaa hh:mm · modelo vX (momento)» para todos
  los usuarios; la Figura 6 la muestra sin hora.
- [ ] **Limitación: estado del recálculo en memoria.** Si la aplicación se reinicia, el motivo
  de una carga sin modelo habilitado ya no se puede consultar (sí se mostró en la pantalla o
  en la respuesta de la API, y queda en el registro de la aplicación). Lo que se calculó se
  reconstruye desde la base.
- [ ] **Limitación: cargas fuera de orden.** La estimación vigente es la de la última carga
  (HU-003, criterio 3). Si se carga un archivo de cierre del 1.er semestre después de uno del
  2.º, la vigente pasa a ser la de cierre_1s, con menos información.
- [ ] **HU-003, criterio 5:** el motivo se informa al Área de Sistemas en el resultado de la
  carga (pantalla y API) y en el registro de la aplicación. No hay aviso por otro canal, como
  un correo; si el documento sugiere una notificación, aclararlo.
- [ ] **Comprobación de punta a punta (05/11):** con los tres archivos simulados cargados en
  orden, la plataforma deja 117, 134 y 137 estudiantes en nivel alto (13,2 / 15,1 / 15,5 % de
  885, como en el informe de evaluación) y las 6 fichas del Anexo coinciden con su predicción
  de cierre_1s (probabilidad, nivel y los 5 factores con sus contribuciones). Sirve para la
  sección Demo: la plataforma reproduce lo evaluado.

## Seguimiento de las alertas (HU-007, 09/11)

- [ ] **HU-007, criterios 4 a 6:** el Word ya tiene los seis criterios (correcciones del
  tutor); `sprint-1/HU-007.md` se actualizó con ese texto. El sprint backlog (tarea 7.1,
  «conservarlo al recalcular») sigue valiendo: lo cubre la regla P3 sin cambios.
- [ ] **Figura 6 (listado):** cada fila tiene el desplegable del estado y un botón
  «Guardar» (la figura muestra solo el desplegable), para que un clic sin querer no quede
  registrado como cambio. Al guardar aparece un mensaje de confirmación arriba de la tabla
  y se actualizan las tarjetas. *Se resuelve con las capturas reales (bloque C).*
- [ ] **Sección Seguridad («registra quién y cuándo cambió cada estado»):** queda en la
  tabla **CAMBIO_ESTADO** del DER (estado anterior, estado nuevo, usuario y fecha y hora,
  guardada en UTC y mostrada en hora argentina); ALERTA.estado guarda solo el estado actual.
  El DER no cambia.
- [ ] **Reglas del cambio de estado (decisión del 09/11):** si el estado nuevo es igual al
  actual, no se registra nada; se puede volver a «pendiente», y ese cambio también queda
  registrado. Solo Coordinación y Tutor/a pueden cambiar el estado (la API responde 403 a los
  demás roles), con la misma salvedad que la carga: sin inicio de sesión, el selector de
  usuario no es un control de acceso (HU-009).
- [ ] **Limitación: el tutor puede cambiar el estado de cualquier alerta**, no solo de sus
  estudiantes, porque la asignación a tutores es HU-011 (sumarlo a la aclaración de la
  Figura 6 sobre el listado).
- [ ] **Limitación: rendimiento del listado con muchas alertas.** Con las 529 alertas de la
  Demo, cada desplegable de estado hace que cambiar o quitar un filtro tarde unos 2 a 3
  segundos en el navegador (medido el 09/11 en Chrome: 2,4–2,7 s, frente a 0,6 s sin
  desplegables). Para volúmenes mayores, el diseño integral debería paginar el listado.

## Cierre técnico (09/11)

- [ ] **Respaldo y restauración (Seguridad, «Controles del prototipo»):** los scripts
  `scripts/respaldar`, `restaurar` y `verificar` (`.ps1` y `.sh`) ya existen. El respaldo usa
  `pg_dump -Fc` y la restauración, `pg_restore --clean --if-exists` en una sola transacción,
  con la aplicación detenida. La restauración **se probó el 09/11** sobre la base de la demo:
  respaldo → `docker compose down -v` → base recreada con 4 roles, 4 usuarios y 3 modelos →
  restauración → mismas cantidades (885 estudiantes, 3 cargas, 529 alertas: 137 alto,
  131 medio y 261 bajo; 2 cambios de estado). También se probó una restauración fallida:
  la base quedó intacta. El control pasa de «Cierre del sprint» a «Listo», y el
  procedimiento está documentado en el manual de instalación.
- [ ] **Manual de instalación = `README.md` del repositorio** (requisitos, instalación,
  uso, respaldo y restauración, pruebas, correspondencia HU-001 a HU-007 y problemas
  comunes). Citarlo con ese nombre en la sección Demo y en el Anexo, junto con el enlace
  al repositorio público.
- [ ] **Figura 10 y texto de Arquitectura («sin puertos publicados»):** vale para
  `compose.yaml`, que es la versión que se entrega: la base no publica puertos y la aplicación
  se publica solo en `127.0.0.1:8000`. Hay además un `compose.dev.yaml`, solo para
  desarrollo, que publica la base en `127.0.0.1` para que la usen las pruebas automáticas,
  los scripts y la aplicación con recarga. Si el documento describe cómo se prueban los
  criterios, mencionarlo.
- [ ] **Datos versionados (Datos y Demo):** `data/cargas/` (los tres archivos simulados) y
  `data/procesados/particion.csv` (índice y conjunto, sin la variable objetivo) **ahora se
  versionan**, para que un clon nuevo funcione solo con Docker. `data/raw/` sigue fuera del
  repositorio. Si el documento dice que los datos no se incluyen en el repositorio,
  corregirlo e indicar la atribución que pide CC BY 4.0: «derivados del conjunto de prueba
  de Realinho et al. (2021), con licencia CC BY 4.0; se agregaron identificadores sintéticos
  y se quitó la situación final».
- [ ] **Clave de seudonimización y respaldo compartido (Demo y Seguridad):** con otra
  `SEUDONIMO_CLAVE` cambian los códigos `EST-…`, pero no las probabilidades, los niveles ni
  las cantidades. Para ver los mismos códigos que el documento y el video, se restaura el
  respaldo de la carpeta compartida; después no hay que volver a cargar los archivos con
  otra clave, porque los mismos estudiantes entrarían con otros códigos.
- [ ] **Respaldo publicado (Seguridad):** el respaldo de la demo no tiene la clave, los
  identificadores sintéticos de los archivos de carga (0 de 885 legajos, documentos y
  nombres), los roles ni las contraseñas de PostgreSQL (`pg_dump` de una sola base no los
  incluye), y ninguna tabla tiene columnas para guardarlos. Solo trae los códigos
  seudonimizados. Como los archivos de carga también son públicos, alguien podría emparejar
  filas por sus variables y reconstruir la correspondencia entre el legajo **sintético** y
  el código: no expone a nadie real. Escribir en Seguridad: «la plataforma no guarda la
  correspondencia; con datos reales, el respaldo no se publicaría».
- [ ] **Pruebas automáticas:** 312 (312 passed, 0 skipped el 09/11, con la base de
  pruebas). Actualizar la cifra si el documento cita otra.
- [ ] **Etiqueta `v0.1`** de la versión entregada (Seguridad y `sprint-1/README.md`):
  pendiente. La crea Facundo al publicar el repositorio.

## Objetivo 4: el cuestionario no se aplica (decisión del 05/11)

El tutor indicó que el cuestionario no se aplica y que el instrumento va en el Anexo («se
valida la forma, no el contenido»). El objetivo 4 no se reformula: se informa lo que se
entrega, con el mismo criterio que HU-004, criterio 5. Lugares del documento que prometen
el resultado:

- [ ] **«Como resultado, se espera…»** (valoración media ≥ 4 sobre 5 en comprensibilidad y
  utilidad): aclarar que en esta entrega se presenta el instrumento, sin resultados de
  valoración.
- [ ] **Recolección de Datos:** la ventana de aplicación («entre el 28 de octubre y el 4 de
  noviembre») y la regla de análisis (promedios ≥ 4, mínimo de 5 evaluadores) se presentan
  como lo previsto para cuando se aplique, no como algo realizado.
- [ ] **HU-006, criterio 5** (valoración media ≥ 4 sobre 5): informarlo como no evaluado en
  esta entrega, igual que HU-004, criterio 5; los criterios no se reformulan. **En el
  prototipo no se verifica** (09/11): HU-006 se da por terminada con los criterios 1 a 4 y
  el 5 queda registrado como no verificado, porque depende de la aplicación del
  cuestionario. No hay `reportes/cuestionario/analisis.md` ni `scripts/analizar_cuestionario.py`.
- [ ] **Sprint backlog, tarea 6.4** («aplicar el cuestionario a tutores y docentes y analizar
  las respuestas»): queda hecha la parte del formulario y las seis fichas; la aplicación y
  el análisis, no.
- [ ] **Conclusiones, objetivo 4:** el instrumento (formulario y seis fichas) está en el
  Anexo, y su aplicación a tutores y docentes es el paso siguiente.
- [ ] **Anexo:** agregar el formulario (textos de `proyecto/07-cuestionario.md`) y las seis
  fichas (`reportes/cuestionario/caso_1.png` a `caso_6.png`).

## Para las Conclusiones y la Demo (cuando haya resultados)

- [ ] AUC-ROC de los tres momentos y comparación con la regresión logística.
- [ ] Comprobación de umbrales en prueba.
- [ ] Diferencias entre subgrupos.
- [ ] AUC-ROC con y sin «sigue cursando».
- [ ] Sección Demo: enlace al repositorio público, video y manual de instalación.
