# Sprint 1: núcleo del prototipo

Siete historias, 45 puntos, 14,5 días estimados en el documento. El documento fija el
cierre del sprint el 02/11; el desarrollo real arranca el 02/11 y termina antes de la
entrega del 09/11 (anotado en `../pendientes-documento.md`).

## Orden de trabajo

No es el orden numérico: primero va lo que destraba el cuestionario y lo que más riesgo
tiene.

| Paso | Historia y tareas | Por qué en este orden | Produce |
|---|---|---|---|
| 0 | Entorno (tarea 1.1) | Base de todo | Repositorio, dependencias, dataset verificado, Docker |
| 1 | **HU-002** (2.1 a 2.5) + **4.1** (umbrales) + **6.1 y 6.2** (SHAP y etiquetas) | Es el riesgo principal del objetivo 1 y destraba las fichas del cuestionario | Informe exploratorio, informe de evaluación, modelos habilitados |
| 2 | **Fichas del cuestionario** (6.4, primera parte) | El objetivo 4 necesita tiempo para juntar respuestas | 6 fichas PNG + formulario enviado |
| 3 | **HU-001** (1.2 a 1.4) | Tablas, carga, validación y seudonimización | Carga funcionando por API y en pantalla |
| 4 | **HU-003** (3.1 a 3.3) + **HU-004** (4.2) | Recálculo automático, niveles y alertas | Cargas sucesivas que actualizan el riesgo |
| 5 | **HU-005** (5.1, 5.2) | Pantalla principal del Programa de Tutorías | Listado con filtros |
| 6 | **HU-006** (6.3) | Ficha con los factores | Ficha (y capturas finales) |
| 7 | **HU-007** (7.1, 7.2) | Última: primera en salir si hay atraso | Estados con historial |
| 8 | Cierre | Entregables de la Demo | Respaldo, manual de instalación, video, etiqueta `v0.1` |

## Cronograma propuesto (unas 5 h por día hábil; fin de semana completo)

El formulario se envía apenas estén las fichas (decisión del 03/11). Por eso HU-002 se
parte en dos: primero el **camino rápido** hasta las fichas (ver `HU-002.md`), después el
resto.

| Día | Trabajo |
|---|---|
| Mar 03/11 | Paso 0 (instalar, descargar datos, primer commit). HU-002 camino rápido: partición, modelo de `cierre_1s`, umbrales, SHAP y etiquetas → **6 fichas**. Armar el formulario en paralelo y **enviarlo** a la noche si las fichas están |
| Mié 04/11 | Si no salió el martes, enviar el formulario a primera hora. HU-002 completa: análisis exploratorio, modelos de `inscripcion` y `cierre_2s`, evaluación final sobre prueba, informe y guardado (2.5) |
| Jue 05/11 | HU-001 (tablas, carga, validación, seudonimización) |
| Vie 06/11 | HU-003 y HU-004 (recálculo, niveles y alertas); HU-005 |
| Sáb 07/11 | HU-006 (pantalla de la ficha) y HU-007 |
| Dom 08/11 | Cierre técnico (respaldo, manual, video, `v0.1`); cierre del formulario a las 20 |
| Lun 09/11 | Análisis del cuestionario, Conclusiones y Demo en el documento, entrega |

Las correcciones de la E3 llegan en paralelo: si consumen un día, se recorta en este orden:
HU-007 → filtros de HU-005 (dejar solo nivel y estado) → tarjetas de resumen del listado.

## Definición de terminado (para cada historia)

Una historia está terminada cuando:

1. Se cumplen **todos** sus criterios de aceptación (son la Definición de Terminado del
   documento).
2. Cada criterio automatizable tiene al menos una prueba en `tests/` y todas pasan
   (`pytest`). Los que no se pueden automatizar (por ejemplo, el cuestionario) tienen una
   verificación manual descripta en el archivo de la historia.
3. No se rompió ninguna regla de `CLAUDE.md` (conjunto de prueba, variables por momento,
   seudonimización, términos).
4. Se hizo el commit `HU-00X: …` y se actualizó `avance.md`.

## Cómo trabajar cada historia con Claude Code

1. Abrí la carpeta del repositorio en VS Code y el panel de Claude Code. `CLAUDE.md` se
   lee solo.
2. Escribí `/hu HU-002` (comando del proyecto, en `.claude/commands/hu.md`). Claude lee la
   historia, el contexto y las decisiones; si hay una decisión pendiente, pregunta; y
   propone un plan **sin escribir código**. Conviene hacerlo en modo plan.
3. Revisá el plan contra los criterios de aceptación. Pedí cambios si hace falta y aprobalo.
4. Claude implementa tarea por tarea y corre las pruebas.
5. Escribí `/revisar-hu HU-002`: Claude verifica criterio por criterio, con evidencia
   (prueba, archivo o salida), y lista lo que falta.
6. Si todo está, commit y actualización de `avance.md`. Siguiente historia.

Una historia por conversación funciona mejor: al terminar, empezá una conversación nueva
para la siguiente, así el contexto no se llena con la historia anterior.

## Archivos

- `HU-001.md` … `HU-007.md`: especificación de cada historia (copia del documento +
  notas de implementación + pruebas sugeridas).
- `avance.md`: registro diario para el burndown real.
