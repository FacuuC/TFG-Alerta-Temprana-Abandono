/**
 * Crea el cuestionario a tutores y docentes en Google Forms (Objetivo específico 4).
 * Instrumento: docs/proyecto/07-cuestionario.md. Fichas: reportes/cuestionario/caso_1.png a caso_6.png.
 *
 * Uso:
 *  1. Subí las 6 fichas (caso_1.png … caso_6.png) a una carpeta de Google Drive llamada
 *     exactamente como CARPETA_FICHAS.
 *  2. En https://script.google.com: «Nuevo proyecto», pegá este archivo y guardá.
 *  3. Elegí la función crearCuestionario y tocá «Ejecutar». Autorizá los permisos (Google
 *     avisa que la app no está verificada: «Configuración avanzada» → «Ir a … (no seguro)»;
 *     es tu propio script).
 *  4. En el «Registro de ejecución» aparecen el enlace para editar y el enlace para responder.
 *  5. Opcional: ejecutá programarCierre para que el formulario deje de aceptar respuestas
 *     solo, el domingo 08/11/2026 a las 20:00 (hora argentina).
 */

const CARPETA_FICHAS = 'Fichas cuestionario TFG';
const CIERRE = '2026-11-08T20:00:00-03:00';

function crearCuestionario() {
  const fichas = cargarFichas_();

  const form = FormApp.create('Evaluación de fichas de alerta temprana de abandono universitario');
  form.setDescription(
    'Este cuestionario forma parte de un Trabajo Final de Grado de la Licenciatura en ' +
    'Inteligencia Artificial y Robótica sobre una plataforma de alerta temprana del riesgo de ' +
    'abandono universitario. La plataforma estima el riesgo de abandono de estudiantes de primer ' +
    'año y lo presenta en una ficha para que el Programa de Tutorías decida a quién contactar primero.\n\n' +
    'Le vamos a pedir que revise las fichas de seis estudiantes y valore qué tan claras y qué tan ' +
    'útiles le resultan. Los casos provienen de un conjunto de datos público y anonimizado de una ' +
    'institución de educación superior de Portugal: no corresponden a estudiantes de su institución ' +
    'ni a personas identificables.\n\n' +
    'La participación es voluntaria y anónima: solo se registra su rol. Puede dejar el cuestionario ' +
    'en cualquier momento. Las respuestas se usan solo con fines académicos. Tiempo estimado: 10 minutos. ' +
    'Disponible hasta el domingo 8 de noviembre a las 20 h.'
  );
  intentar_(function () { form.setCollectEmail(false); });
  form.setLimitOneResponsePerUser(false); // true obligaría a iniciar sesión y dejaría de ser anónimo
  form.setProgressBar(true);
  form.setAllowResponseEdits(false);
  form.setShowLinkToRespondAgain(false);
  form.setPublishingSummary(false);
  form.setConfirmationMessage(
    'Gracias por su participación. Sus respuestas ayudan a evaluar si las alertas son comprensibles ' +
    'y útiles para el acompañamiento.'
  );

  // Sección 1: consentimiento (si no acepta, se envía el formulario sin más preguntas)
  const consentimiento = form.addMultipleChoiceItem()
    .setTitle('¿Acepta participar en este cuestionario?')
    .setRequired(true);
  consentimiento.setChoices([
    consentimiento.createChoice('Sí, acepto', FormApp.PageNavigationType.CONTINUE),
    consentimiento.createChoice('No acepto', FormApp.PageNavigationType.SUBMIT),
  ]);

  // Sección 2: rol (único dato del evaluador que se registra)
  form.addPageBreakItem().setTitle('Datos del evaluador');
  form.addMultipleChoiceItem()
    .setTitle('¿Cuál es su rol?')
    .setHelpText('Si cumple ambos roles, elija el que ejerce principalmente.')
    .setChoiceValues(['Tutor/a', 'Docente'])
    .setRequired(true);

  // Sección 3: instrucciones
  form.addPageBreakItem()
    .setTitle('Instrucciones')
    .setHelpText(
      'A continuación verá seis fichas. Cada una muestra la probabilidad estimada de abandono, el ' +
      'nivel de urgencia (alto, medio o bajo) y los cinco factores que más pesan en la estimación de ' +
      'ese estudiante. Léalas como si tuviera que decidir si contacta al estudiante y con qué prioridad.'
    );

  // Secciones 4 a 9: un caso por sección (el orden de las fichas ya está mezclado por nivel)
  fichas.forEach(function (imagen, i) {
    const numero = i + 1;
    form.addPageBreakItem().setTitle('Caso ' + numero);
    form.addImageItem()
      .setImage(imagen)
      .setTitle('Ficha del caso ' + numero)
      .setAlignment(FormApp.Alignment.CENTER)
      .setWidth(740);
    form.addScaleItem()
      .setTitle('¿Qué tan claro le resulta lo que indica la ficha?')
      .setBounds(1, 5)
      .setLabels('Nada claro', 'Totalmente claro')
      .setRequired(true);
    form.addScaleItem()
      .setTitle('¿Qué tan útil le resulta esta información para decidir una intervención?')
      .setBounds(1, 5)
      .setLabels('Nada útil', 'Totalmente útil')
      .setRequired(true);
    form.addParagraphTextItem()
      .setTitle('¿Qué cambiaría o agregaría a esta ficha?')
      .setRequired(false);
  });

  // Sección 10: pregunta de control
  form.addPageBreakItem().setTitle('Para terminar');
  form.addMultipleChoiceItem()
    .setTitle('Según la ficha, los factores indican…')
    .setChoiceValues([
      'las causas del abandono del estudiante',
      'cuánto pesa cada variable en la estimación del modelo',
      'una recomendación de intervención',
    ])
    .setRequired(true);

  intentar_(function () { form.setPublished(true); }); // cuentas donde los formularios nuevos nacen sin publicar
  PropertiesService.getScriptProperties().setProperty('FORM_ID', form.getId());

  Logger.log('Formulario creado.');
  Logger.log('Editar: ' + form.getEditUrl());
  Logger.log('Responder (este es el que se envía): ' + form.getPublishedUrl());
  intentar_(function () { Logger.log('Enlace corto: ' + form.shortenFormUrl(form.getPublishedUrl())); });
}

/** Programa el cierre automático del formulario (domingo 08/11 a las 20:00, hora argentina). */
function programarCierre() {
  ScriptApp.getProjectTriggers()
    .filter(function (t) { return t.getHandlerFunction() === 'cerrarCuestionario'; })
    .forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('cerrarCuestionario').timeBased().at(new Date(CIERRE)).create();
  Logger.log('Cierre programado para ' + CIERRE);
}

function cerrarCuestionario() {
  const id = PropertiesService.getScriptProperties().getProperty('FORM_ID');
  FormApp.openById(id)
    .setAcceptingResponses(false)
    .setCustomClosedFormMessage('El cuestionario ya cerró. ¡Gracias por su interés!');
}

function cargarFichas_() {
  const carpetas = DriveApp.getFoldersByName(CARPETA_FICHAS);
  if (!carpetas.hasNext()) {
    throw new Error('No encontré en Drive la carpeta "' + CARPETA_FICHAS + '". Creala y subí caso_1.png a caso_6.png.');
  }
  const carpeta = carpetas.next();
  const imagenes = [];
  for (let n = 1; n <= 6; n++) {
    const archivos = carpeta.getFilesByName('caso_' + n + '.png');
    if (!archivos.hasNext()) {
      throw new Error('Falta caso_' + n + '.png en la carpeta "' + CARPETA_FICHAS + '".');
    }
    imagenes.push(archivos.next().getBlob());
  }
  return imagenes;
}

function intentar_(accion) {
  try {
    accion();
  } catch (e) {
    Logger.log('Aviso: ' + e.message);
  }
}
