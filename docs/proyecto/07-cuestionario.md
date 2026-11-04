# Cuestionario a tutores y docentes (Objetivo específico 4)

Fuente: Recolección de Datos del documento y bloque 4.2 del «Paquete de cambios E3».
El instrumento **ya está definido**; lo que falta son las seis fichas, que salen del
modelo de `cierre_1s`.

## Diseño

- **Participantes:** tutores y docentes con experiencia en el acompañamiento de
  estudiantes, a los que el autor tiene acceso. Mínimo **5 evaluadores**. Muestra no
  probabilística: los resultados son una validación inicial y no se generalizan.
- **Casos:** las fichas de **6 estudiantes del conjunto de prueba, 2 por nivel de
  urgencia** (alto, medio, bajo), generadas por el modelo del cierre del 1.er semestre.
  Cada ficha muestra la probabilidad, el nivel y los cinco factores que más pesan, en
  lenguaje comprensible. Todos ven los mismos seis casos.
- **Tarea:** leer cada ficha como si de ella dependiera decidir si contacta al estudiante
  y con qué prioridad.
- **Ventana de aplicación:** el documento dice del 28/10 al 4/11. Decisión del 03/11: se
  envía apenas estén las fichas (martes 03/11 a la noche o miércoles 04/11) y se cierra
  el domingo 08/11 a las 20. La fecha del documento se corrige en la versión final.

## Estructura del formulario (Google Forms o similar)

1. **Presentación y consentimiento.** Objetivo del estudio, participación voluntaria y
   anónima, los casos provienen de un conjunto de datos público y anonimizado (no son
   estudiantes reales de su institución), duración estimada (10 minutos). Pregunta:
   «¿Acepta participar?» (Sí / No; si responde No, termina).
2. **Rol:** Tutor/a o Docente. Es el único dato del evaluador que se registra.
3. **Instrucción:** «A continuación verá seis fichas. Léalas como si tuviera que decidir
   si contacta al estudiante y con qué prioridad.»
4. **Por cada caso (×6),** con la captura de la ficha:
   - «¿Qué tan claro le resulta lo que indica la ficha?»: escala de 1 (nada) a 5
     (totalmente).
   - «¿Qué tan útil le resulta esta información para decidir una intervención?»: escala
     de 1 (nada) a 5 (totalmente).
   - «¿Qué cambiaría o agregaría a esta ficha?»: respuesta abierta, opcional.
5. **Pregunta de control, al final:** «Según la ficha, los factores indican…»
   - las causas del abandono del estudiante;
   - cuánto pesa cada variable en la estimación del modelo *(correcta)*;
   - una recomendación de intervención.

## Regla de análisis

- Para cada aspecto (comprensibilidad y utilidad) se promedian **todas** las respuestas
  (6 casos × evaluadores). El objetivo se cumple si **ambos promedios son ≥ 4**.
- Se informan también los promedios por nivel de urgencia y por rol.
- Las respuestas abiertas se agrupan por tema (claridad de las variables, información
  faltante, diseño de la ficha, etc.) y se cuenta cuántas veces aparece cada uno.
- Si el promedio da menos de 4, se analiza como hallazgo en las Conclusiones.
- Producto: `reportes/cuestionario/analisis.md`, generado por un script a partir del CSV
  exportado del formulario.

## Cómo se generan las seis fichas (tarea 6.4)

1. Con el modelo de `cierre_1s` elegido en validación y los umbrales fijados (no hace
   falta la evaluación final; ver el «camino rápido» de `sprint-1/HU-002.md`), calcular
   probabilidad, nivel y los cinco factores SHAP de los estudiantes de prueba.
2. Elegir 2 casos por nivel con una regla reproducible (propuesta: al azar con la semilla
   fija, entre los casos de cada nivel; ver `08-decisiones.md`).
3. Generar las imágenes con el mismo diseño que la ficha de Dash. Si la pantalla todavía
   no está, un script con matplotlib (`scripts/generar_fichas_cuestionario.py`) produce
   PNG con la misma información y textos; se guardan en `reportes/cuestionario/`.
4. Las fichas usan el código seudonimizado; no se muestra la situación final real.

## Textos listos para el formulario (Google Forms)

Se puede armar el formulario mientras se entrena el modelo y agregar las imágenes al final.

**Configuración:** no recopilar direcciones de correo; no limitar a una respuesta (eso
obliga a iniciar sesión y deja de ser anónimo); mostrar barra de progreso; en la pregunta
de control, orden aleatorio de las opciones.

**Título:** Evaluación de fichas de alerta temprana de abandono universitario

**Descripción (sección 1):**

> Este cuestionario forma parte de un Trabajo Final de Grado de la Licenciatura en
> Inteligencia Artificial y Robótica sobre una plataforma de alerta temprana del riesgo de
> abandono universitario. La plataforma estima el riesgo de abandono de estudiantes de primer año y lo
> presenta en una ficha para que el Programa de Tutorías decida a quién contactar primero.
>
> Le vamos a pedir que revise las fichas de seis estudiantes y valore qué tan claras y qué
> tan útiles le resultan. Los casos provienen de un conjunto de datos público y anonimizado
> de una institución de educación superior de Portugal: no corresponden a estudiantes de su
> institución ni a personas identificables.
>
> La participación es voluntaria y anónima: solo se registra su rol. Puede dejar el
> cuestionario en cualquier momento. Las respuestas se usan solo con fines académicos.
> Tiempo estimado: 10 minutos.

1. **¿Acepta participar en este cuestionario?** (opción múltiple, obligatoria)
   Sí, acepto · No acepto → si elige «No acepto», ir a «Enviar formulario».
2. **¿Cuál es su rol?** (opción múltiple, obligatoria)
   Tutor/a · Docente. Ayuda: «Si cumple ambos roles, elija el que ejerce principalmente».

**Sección 2: Instrucciones**

> A continuación verá seis fichas. Cada una muestra la probabilidad estimada de abandono,
> el nivel de urgencia (alto, medio o bajo) y los cinco factores que más pesan en la
> estimación de ese estudiante. Léalas como si tuviera que decidir si contacta al
> estudiante y con qué prioridad.

**Secciones 3 a 8: Caso 1 a Caso 6** (una por caso, con la imagen de la ficha)

- **¿Qué tan claro le resulta lo que indica la ficha?** Escala lineal de 1 a 5,
  etiquetas «Nada claro» (1) y «Totalmente claro» (5). Obligatoria.
- **¿Qué tan útil le resulta esta información para decidir una intervención?** Escala
  lineal de 1 a 5, etiquetas «Nada útil» (1) y «Totalmente útil» (5). Obligatoria.
- **¿Qué cambiaría o agregaría a esta ficha?** Párrafo. Opcional.

Orden sugerido de los casos (mezclado, igual para todos): alto, bajo, medio, alto, medio,
bajo. El título de cada sección es solo «Caso N»: no anticipa el nivel.

**Sección 9: Para terminar**

- **Según la ficha, los factores indican…** (opción múltiple, obligatoria)
  - las causas del abandono del estudiante;
  - cuánto pesa cada variable en la estimación del modelo;
  - una recomendación de intervención.

**Mensaje de confirmación:** «Gracias por su participación. Sus respuestas ayudan a
evaluar si las alertas son comprensibles y útiles para el acompañamiento.»

Al cerrar el formulario: exportar las respuestas a CSV en `reportes/cuestionario/respuestas.csv`
(no se versiona si tiene texto libre con datos personales; revisar antes) y correr el
script de análisis.
