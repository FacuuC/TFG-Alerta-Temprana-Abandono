# Pendientes para la versión final del documento

Inconsistencias entre el documento (entrega 3 + avance de la entrega 4, al 02/11) y lo que
se implementa. **No se editan ahora:** se aplican junto con las correcciones del tutor,
cuando lleguen. Al implementar, sumá acá cualquier diferencia nueva.

## Fechas del sprint y del cuestionario

- [ ] Herramientas Metodológicas: «El Sprint 1, que finaliza el 2 de noviembre» → fechas
  reales del sprint.
- [ ] Planificación: hito «sistema funcional integrado (02/11)» y Gantt de la fase 3.
- [ ] Recolección de Datos: ventana del cuestionario «entre el 28 de octubre y el 4 de
  noviembre» → nueva ventana (decisión P8).
- [ ] Sprint backlog: columna «Estado» y burndown con el avance real (`sprint-1/avance.md`).

## Prototipos de pantalla (al final, reemplazar por capturas reales)

- [ ] Figura 7 (ficha): «Factores que más influyen» → «Factores que más pesan»
  (término fijo de la obs. 18).
- [ ] Figura 7: aparece «Aranceles al día: no», una variable **excluida** del modelo.
- [ ] Figura 7: el aviso no dice que los factores no son causas (HU-006, criterio 4).
- [ ] Figura 5 (carga): «Momento del período» → «Momento de predicción»; en «Cargas
  anteriores», «Ingreso» → «Inscripción».
- [ ] Figuras 6 y 7: códigos de 6 caracteres (`EST-7F3A21`); con la decisión P1 son de 8
  (`EST-7F3A21C4`).
- [ ] Figuras 5 a 7: «Cerrar sesión» no existe en el Sprint 1 (selector de usuario de prueba).

## Texto

- [ ] Sprint backlog, tarea 1.1: «contenedores Docker de la API, la base de datos y el
  panel» → la Figura 9 muestra dos contenedores (aplicación y datos).
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
  explicarlo en el texto, porque los tutores pueden comentarlo en el cuestionario.

## Para las Conclusiones y la Demo (cuando haya resultados)

- [ ] AUC-ROC de los tres momentos y comparación con la regresión logística.
- [ ] Comprobación de umbrales en prueba.
- [ ] Diferencias entre subgrupos.
- [ ] AUC-ROC con y sin «sigue cursando».
- [ ] Resultados del cuestionario (objetivo 4).
- [ ] Sección Demo: enlace al repositorio público, video y manual de instalación.
