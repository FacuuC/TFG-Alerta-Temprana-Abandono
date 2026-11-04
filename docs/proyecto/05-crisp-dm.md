# Procedimiento CRISP-DM (cómo se construye y evalúa el modelo)

Fuente: Diseño Metodológico → Herramientas Metodológicas del documento (Wirth y Hipp,
2000). Las tareas son las del sprint backlog. Este procedimiento es lo que el tutor va a
contrastar con el código y con el informe de evaluación.

## 1. Comprensión del negocio (antes del sprint, ya hecha)

Clasificación binaria abandono frente a no abandono; tres momentos del primer año;
criterios de éxito de los objetivos 1, 3 y 4 (`00-contexto.md`).

## 2. Comprensión de los datos (tarea 2.1)

- Análisis exploratorio: distribución de cada variable, proporción de abandonos,
  correlaciones y momento en que cada variable está disponible.
- **Solo con los datos completos, sin entrenar nada**; mejor todavía, después de fijar la
  partición, mirar solo entrenamiento para las decisiones que puedan influir en el modelo.
- **Producto:** `reportes/informe_exploratorio.md` (con figuras en `reportes/figuras/`) y la
  lista de variables de cada momento con las exclusiones justificadas.
- Revisar: macroeconómicas (un valor por año de ingreso), códigos de las categóricas
  (anexo o códigos originales) y categorías con muy pocos casos.

## 3. Preparación de los datos (tarea 2.2)

1. Variable objetivo binaria: abandono = 1; graduado o sigue cursando = 0.
2. Partición estratificada 60/20/20 con semilla fija, **la misma para los tres momentos**,
   guardada en `data/procesados/particion.csv`.
3. Transformaciones dentro de un `Pipeline`/`ColumnTransformer` de scikit-learn,
   ajustadas **solo con entrenamiento**:
   - categóricas codificadas → one-hot (`handle_unknown="ignore"`);
   - numéricas → estandarización (para la regresión logística; XGBoost no la necesita,
     pero puede compartir el mismo preprocesamiento);
   - binarias → sin cambios.
4. **Producto:** un conjunto preparado por momento (las listas de `VARIABLES_POR_MOMENTO`).

## 4. Modelado (tarea 2.3)

Para **cada momento**, dos modelos:

- **Regresión logística** de referencia (Bettahi et al., 2025, p. 18, se acercó bastante a
  XGBoost con este mismo conjunto), con `class_weight="balanced"`.
- **XGBoost** con `scale_pos_weight = negativos / positivos` del entrenamiento. Grilla
  acotada de hiperparámetros: profundidad de los árboles, tasa de aprendizaje y cantidad
  de árboles. Se elige la combinación con mayor **AUC-ROC en validación**. Grilla usada:
  profundidad 2, 3, 4 y 5; tasa 0,03, 0,05 y 0,1; 100, 200 y 400 árboles (36
  combinaciones). Se extendió el 03/11 porque la grilla inicial (profundidad 3 a 5, tasa
  0,05 y 0,1, 200 y 400 árboles) dejaba el óptimo en el borde.
- **Nada de casos sintéticos** (SMOTE u otros).
- **Producto:** modelos candidatos de cada momento y una tabla con el AUC-ROC de validación
  de cada combinación (va al informe).

## 5. Evaluación (tareas 2.4, 4.1 y 2.5)

**Etapa A: con validación** (se puede repetir todas las veces que haga falta)

1. Elegir el modelo de cada momento: XGBoost **solo si supera** a la regresión logística
   en AUC-ROC de validación; si no, queda la regresión logística.
2. Fijar los umbrales de cada momento sobre las probabilidades de validación:
   - `umbral_alto`: el menor valor tal que la proporción de estudiantes con
     probabilidad ≥ `umbral_alto` **no supere el 15 %** (`CAPACIDAD_TUTORIAS`);
   - `umbral_medio`: el mayor valor tal que, entre alto y medio
     (probabilidad ≥ `umbral_medio`), se detecte **al menos el 80 %** de los abandonos
     de validación (`DETECCION_MINIMA`). Debe ser ≤ `umbral_alto`; si no lo es, avisar.
   - Nivel: alto si p ≥ umbral_alto; medio si umbral_medio ≤ p < umbral_alto; bajo si no.

**Etapa B: con prueba, una sola vez** (script `scripts/evaluar_final.py` o similar, que
deja constancia de la fecha de ejecución en el informe)

1. AUC-ROC, precisión y sensibilidad de cada momento (alerta = nivel alto o medio).
2. **Meta:** AUC-ROC > 0,80 en `cierre_1s`. Si se alcanza, se habilita; `inscripcion` y
   `cierre_2s` se habilitan con el desempeño obtenido, que queda informado.
3. Comprobación de umbrales en prueba: nivel alto ≤ 15 % de los estudiantes; alto + medio
   detectan ≥ 80 % de los abandonos; proporción de abandonos observada decreciente de
   alto a bajo.
4. Solo sobre `cierre_1s`:
   - AUC-ROC, sensibilidad y precisión por subgrupos: género, edad de ingreso
     (hasta 20, de 21 a 25, más de 25) y condición de becario;
   - AUC-ROC calculado **sin** quienes siguen cursando;
   - revisión con SHAP de si alguna variable demográfica tiene un peso alto.
5. **Si un resultado no alcanza el objetivo, se informa como tal. La prueba no se usa
   para volver a ajustar nada.**
6. **Productos:** `reportes/informe_evaluacion.md` (métricas por momento, comparación con
   la referencia, umbrales, comprobaciones, subgrupos, AUC sin «sigue cursando», resumen
   SHAP global), y los modelos habilitados guardados con versión, fecha, métricas y
   umbrales (tarea 2.5).

## 6. Despliegue (tareas 3.1 a 3.3)

El servicio de predicción aplica, en cada carga, el modelo habilitado del momento y guarda
cada predicción con su fecha y la versión del modelo. El reentrenamiento periódico es del
diseño integral (HU-014).

## Explicaciones (tareas 6.1 y 6.2)

- `shap.TreeExplainer` para XGBoost (`LinearExplainer` si el elegido es la regresión
  logística).
- Las columnas one-hot de una misma variable se **suman** para obtener el aporte de la
  variable original, así los cinco factores son variables comprensibles («Carrera», no
  «carrera_9500»).
- Se guardan los cinco factores con mayor valor absoluto, con el signo (aumenta o
  disminuye el riesgo).
- Texto obligatorio en la ficha: la alerta no reemplaza el criterio del tutor y los
  factores muestran cuánto pesa cada variable en la estimación, **no las causas** del
  abandono.

## Números que van a las Conclusiones del documento

El informe de evaluación tiene que dejar listos: AUC-ROC de los tres momentos (anticipación
frente a precisión), comparación con la regresión logística, comprobación de umbrales,
diferencias entre subgrupos y AUC-ROC con y sin «sigue cursando».
