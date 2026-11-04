# Contexto del proyecto

Fuente: «TFG 4 – Costamagna-Facundo.docx» (entrega 3 más el avance de la entrega 4),
al 02/11/2026. Si llegan correcciones del tutor que cambien algo de acá, se actualiza
este archivo y se anota en `08-decisiones.md`.

## Problema

En las universidades nacionales argentinas el abandono se concentra en el primer año.
En la organización de referencia (un caso modelado, no una universidad real), la
detección del riesgo depende de lo que tutores y docentes alcanzan a observar, con
señales tardías (inasistencias, ausentismo en exámenes) y criterios heterogéneos,
mientras que la información académica ya existe en el sistema de gestión (SIU-Guaraní)
y se usa solo con fines administrativos.

La propuesta es una plataforma SaaS de alerta temprana. **Que detectar antes reduzca
el abandono es una hipótesis que este trabajo no comprueba**: se evalúa el desempeño
predictivo (objetivo 1) y la valoración de tutores y docentes (objetivo 4).

## Organización de referencia (supuestos que importan para el código)

- Universidad nacional de gestión estatal, organizada en facultades, que usa SIU-Guaraní
  y tiene un Programa de Tutorías para ingresantes en la Secretaría Académica.
- El Área de Sistemas de Información **exporta un CSV** al inicio y al cierre de cada
  semestre del primer año. No hay integración en línea.
- El Programa de Tutorías puede acompañar como máximo al **15 %** de los estudiantes
  evaluados en cada momento (supuesto, con referencia a Shaikhanova et al., 2025, p. 8).
- La universidad define la base legal para tratar los datos (fuera del alcance).

## Roles (de las historias de usuario)

| Rol | Uso en el Sprint 1 |
|---|---|
| Área de Sistemas de Información | Carga el archivo de cada momento (HU-001) y entrena el modelo (HU-002) |
| Coordinación del Programa de Tutorías | Consulta y filtra el listado de alertas (HU-005); recibe el riesgo actualizado (HU-003, HU-004) |
| Tutor/a | Abre la ficha (HU-006) y registra el estado de seguimiento (HU-007) |
| Secretaría Académica | Solo en el diseño integral (panel de métricas, HU-008) |

Sin inicio de sesión en el Sprint 1: un usuario de prueba por rol, precargado.

## Objetivo general

Optimizar la detección temprana del riesgo de abandono estudiantil en la organización
de referencia, para que el Programa de Tutorías pueda priorizar o intervenir a tiempo
en los casos de mayor riesgo.

## Objetivos específicos (criterios de éxito)

1. Un modelo por momento de predicción del primer año (inscripción, cierre del primer
   semestre y cierre del segundo), con las variables disponibles en ese momento.
   **AUC-ROC > 0,80 al cierre del primer semestre sobre el conjunto de prueba
   reservado**, e informe de desempeño por subgrupos de género, edad de ingreso y
   condición de becario.
2. Un servicio que recalcule automáticamente los índices de riesgo cada vez que se
   incorporan los datos de un momento, con el modelo de ese momento, antes del inicio
   del período siguiente.
3. Tres niveles de urgencia, con umbrales definidos sobre validación y comprobados sobre
   prueba, presentados en un panel de alertas con los factores que más pesan en cada
   estimación.
4. Valoración media ≥ 4 sobre 5 en comprensibilidad y en utilidad, según el cuestionario
   a tutores y docentes sobre casos generados por el modelo (`07-cuestionario.md`).

Reglas de los umbrales: el nivel alto no supera el 15 % de los estudiantes; entre alto y
medio se detecta al menos el 80 % de los abandonos; en prueba, la proporción de abandonos
observada disminuye del nivel alto al bajo.

## Objetivo del prototipo

Desarrollar una plataforma web basada en aprendizaje automático que, a partir de los
datos académicos y socioeconómicos de los estudiantes, estime su riesgo de abandono y
genere alertas tempranas explicables, clasificadas por nivel de urgencia, para guiar el
acompañamiento del Programa de Tutorías.

## Límites

Desde la incorporación de los datos académicos y socioeconómicos de los estudiantes, en
cada momento de predicción del primer año, hasta el registro del estado de seguimiento
de las alertas tempranas por parte del Programa de Tutorías.

## Alcance (procesos incluidos)

1. Incorporación, validación y seudonimización de los datos, con descarte de las
   variables que el modelo no utiliza.
2. Entrenamiento y evaluación de modelos, incluida la evaluación por subgrupos.
3. Estimación del riesgo y actualización de los índices en cada carga, con el modelo del
   momento correspondiente.
4. Explicaciones individuales con los factores que más pesan en la estimación.
5. Clasificación en niveles de urgencia y emisión de alertas tempranas.
6. Consulta de las alertas y de sus factores por parte del Programa de Tutorías.
7. Registro del estado de seguimiento de cada alerta.

**Fuera del prototipo** (diseño integral): API de consulta, panel de métricas, acceso por
roles, reentrenamiento periódico, asignación de alertas a tutores, registro de
intervenciones y uso por varias instituciones. Los momentos se limitan al primer año.

## Product backlog (proyecto integral)

| ID | Historia | Prioridad | Puntos | Dependencia | Sprint |
|---|---|---|---|---|---|
| HU-001 | Carga y validación de datos de estudiantes | Alta | 8 | – | 1 |
| HU-002 | Entrenamiento y evaluación del modelo de riesgo | Alta | 13 | HU-001 | 1 |
| HU-003 | Estimación y actualización automática del riesgo | Alta | 5 | HU-002 | 1 |
| HU-004 | Clasificación por niveles de urgencia | Alta | 3 | HU-003 | 1 |
| HU-005 | Listado de alertas tempranas | Alta | 5 | HU-004 | 1 |
| HU-006 | Ficha del estudiante con la explicación del riesgo | Alta | 8 | HU-005 | 1 |
| HU-007 | Registro del estado de seguimiento | Alta | 3 | HU-005 | 1 |
| HU-008 | Panel de métricas institucionales | Media | 8 | HU-004 | — |
| HU-009 | Acceso de usuarios según rol | Alta | 5 | – | 2 (después del 09/11) |
| HU-010 | Consulta de predicciones mediante API | Media | 3 | HU-003, HU-009 | — |
| HU-011 | Asignación de alertas a tutores | Media | 5 | HU-005, HU-009 | — |
| HU-012 | Registro de intervenciones | Media | 5 | HU-007 | — |
| HU-013 | Ajuste de umbrales de urgencia | Media | 3 | HU-004 | — |
| HU-014 | Reentrenamiento periódico del modelo | Media | 8 | HU-002 | — |
| HU-015 | Evaluación de resultados del acompañamiento | Baja | 8 | HU-012 | — |

Sprint 1: 7 historias, 45 puntos, 14,5 días estimados.

## Entregables de la entrega final (09/11/2026, M4 y encuentro 4)

En la sección «Demo» del PDF va un enlace público (repositorio y carpeta en la nube),
accesible hasta la defensa, con:

1. Código fuente funcional (el profesor verifica la coherencia con el documento).
2. Video de 3 a 5 minutos con el funcionamiento y una explicación del código.
3. Documentación de instalación (cómo montar el proyecto).
4. Opcional: manual de usuario.

No hace falta desplegarlo en la nube: en la defensa se muestra funcionando en la
máquina propia. Tiene que haber una interfaz visible; un notebook no alcanza.
