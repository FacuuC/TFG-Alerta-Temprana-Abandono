# Informe de evaluación final

Generado por `scripts/evaluar_final.py` el **04/11/2026 01:07** (tareas 2.4 y 2.5; CRISP-DM, fase 5, etapa B). Conjunto evaluado: **prueba** (885 estudiantes, 284 abandonos).

El conjunto de prueba se usa **una sola vez**, en esta ejecución, que autorizó una persona
desde una terminal interactiva (`reportes/uso_conjunto_prueba.json`). Si un resultado no
alcanza el objetivo, se informa como tal: la prueba no se usa para reajustar nada.

**La elección del modelo de cada momento se hizo con el conjunto de validación, antes de ver la prueba. La comparación en prueba con la alternativa no elegida es solo informativa: aunque la alternativa salga mejor, el modelo habilitado no cambia.**

## 1. Modelos evaluados

| Momento | Versión | Algoritmo | Hiperparámetros | Entrenado | SHA-256 de `pipeline.joblib` |
|---|---|---|---|---|---|
| Inscripción | 1.0 | XGBoost | `{"max_depth": 2, "learning_rate": 0.1, "n_estimators": 200, "scale_pos_weight": 2.115}` | 2026-11-04 | `d0ca7ddeca8eb481…` |
| Cierre del 1.er semestre | 1.0 | XGBoost | `{"max_depth": 2, "learning_rate": 0.1, "n_estimators": 400, "scale_pos_weight": 2.115}` | 2026-11-04 | `fd37e9f99a4ac0f6…` |
| Cierre del 2.º semestre | 1.0 | XGBoost | `{"max_depth": 2, "learning_rate": 0.1, "n_estimators": 200, "scale_pos_weight": 2.115}` | 2026-11-04 | `dc737546a69ec77d…` |

## 2. Desempeño por momento (prueba)

Alerta = nivel alto o medio (probabilidad ≥ umbral medio). Precisión: de los estudiantes con
alerta, qué proporción abandonó. Sensibilidad: de los que abandonaron, qué proporción tuvo alerta.

| Momento | AUC-ROC (prueba) | Precisión | Sensibilidad | AUC-ROC en validación (al elegir el modelo) |
|---|---|---|---|---|
| Inscripción | 0,7861 | 0,473 | 0,792 | 0,7701 |
| Cierre del 1.er semestre | 0,8928 | 0,716 | 0,746 | 0,8878 |
| Cierre del 2.º semestre | 0,9177 | 0,806 | 0,761 | 0,9147 |

**Meta del objetivo 1** (AUC-ROC > 0,80 en el cierre del 1.er semestre): **alcanzada** (0,8928).

Matriz de confusión de la alerta:

| Momento | Abandonos con alerta | Abandonos sin alerta | No abandonos con alerta | No abandonos sin alerta |
|---|---|---|---|---|
| Inscripción | 225 | 59 | 251 | 350 |
| Cierre del 1.er semestre | 212 | 72 | 84 | 517 |
| Cierre del 2.º semestre | 216 | 68 | 52 | 549 |

## 3. Umbrales (fijados en validación) y su comprobación en prueba

| Momento | Umbral alto | Umbral medio | En nivel alto (≤ 15 %) | Abandonos detectados (≥ 80 %) | Abandono por nivel (alto / medio / bajo) | Decreciente |
|---|---|---|---|---|---|---|
| Inscripción | 0,7293 | 0,4241 | 13,2 % (sí) | 79,2 % (no) | 76,1 % / 37,9 % / 14,4 % | sí |
| Cierre del 1.er semestre | 0,8936 | 0,5301 | 15,1 % (no) | 74,6 % (no) | 95,5 % / 51,9 % / 12,2 % | sí |
| Cierre del 2.º semestre | 0,9164 | 0,5951 | 15,5 % (no) | 76,1 % (no) | 97,8 % / 62,6 % / 11,0 % | sí |

Entre paréntesis, si se cumple la regla. Los umbrales no se modifican con estos resultados.

## 4. Comparación con la alternativa no elegida (prueba, solo informativa)

La elección del modelo de cada momento se hizo con el conjunto de validación, antes de ver la prueba. La comparación en prueba con la alternativa no elegida es solo informativa: aunque la alternativa salga mejor, el modelo habilitado no cambia.

La alternativa es la regresión logística de referencia cuando el elegido es XGBoost, y el mejor
XGBoost de la grilla cuando el elegido es la regresión logística. Se volvió a ajustar con
entrenamiento y, antes de leer la prueba, se comprobó que reproduce su AUC-ROC de validación
registrado (tolerancia ±0,0005).

| Momento | Elegido | AUC-ROC elegido (prueba) | Alternativa | AUC-ROC alternativa (prueba) | Precisión / sensibilidad alternativa | AUC-ROC validación alternativa: registrado / recalculado |
|---|---|---|---|---|---|---|
| Inscripción | XGBoost | 0,7861 | Regresión logística | 0,7752 | 0,469 / 0,789 | 0,7673 / 0,7673 |
| Cierre del 1.er semestre | XGBoost | 0,8928 | Regresión logística | 0,8838 | 0,698 / 0,757 | 0,8871 / 0,8871 |
| Cierre del 2.º semestre | XGBoost | 0,9177 | Regresión logística | 0,9159 | 0,786 / 0,764 | 0,9128 / 0,9128 |

La alternativa usa los umbrales del modelo elegido para la alerta (alto + medio).

## 5. Desempeño por subgrupos (cierre del 1.er semestre, prueba)

AUC-ROC no definido («—») si el grupo tiene una sola clase.

| Subgrupo | Grupo | Estudiantes | Abandonos | AUC-ROC | Sensibilidad | Precisión |
|---|---|---|---|---|---|---|
| Género | femenino | 580 | 142 | 0,8808 | 0,683 | 0,708 |
| Género | masculino | 305 | 142 | 0,8815 | 0,810 | 0,723 |
| Edad de ingreso | hasta 20 | 508 | 101 | 0,8401 | 0,564 | 0,543 |
| Edad de ingreso | 21 a 25 | 150 | 52 | 0,8571 | 0,731 | 0,731 |
| Edad de ingreso | más de 25 | 227 | 131 | 0,9330 | 0,893 | 0,842 |
| Becario | no | 668 | 256 | 0,8865 | 0,770 | 0,719 |
| Becario | sí | 217 | 28 | 0,8356 | 0,536 | 0,682 |

## 6. AUC-ROC con y sin «sigue cursando» (cierre del 1.er semestre, prueba)

| Cálculo | Estudiantes | AUC-ROC |
|---|---|---|
| Con todos (graduado y sigue cursando = no abandono) | 885 | 0,8928 |
| Sin quienes siguen cursando | 741 | 0,9255 |

Quienes siguen cursando todavía pueden abandonar más adelante. Si el AUC-ROC sube al sacarlos,
parte de los «errores» del modelo está en ese grupo de situación incierta.

## 7. Variables que más pesan en las estimaciones (SHAP, cierre del 1.er semestre, prueba)

Media del valor absoluto de SHAP por variable. Muestra cuánto pesa cada variable en las
estimaciones del modelo, **no las causas** del abandono.

| Puesto | Variable | Peso medio |
|---|---|---|
| 1 | Materias aprobadas en el 1.er semestre | 1,339 |
| 2 | Edad al ingresar | 0,365 |
| 3 | Materias inscriptas en el 1.er semestre | 0,322 |
| 4 | Carrera | 0,294 |
| 5 | Nota promedio en el 1.er semestre | 0,262 |
| 6 | Género | 0,182 |
| 7 | Becario | 0,175 |
| 8 | Desempleo del año de ingreso | 0,164 |
| 9 | Materias acreditadas por equivalencia en el 1.er semestre | 0,163 |
| 10 | Nivel educativo del padre | 0,126 |

**Revisión de variables demográficas.** Se considera «peso alto» estar entre las 5
variables de mayor peso medio.

| Variable demográfica | Puesto | Peso medio | Peso alto |
|---|---|---|---|
| Edad al ingresar | 2 | 0,365 | sí |
| Género | 6 | 0,182 | no |
| Vive fuera de su lugar de origen para estudiar | 18 | 0,042 | no |
| Estado civil | 20 | 0,020 | no |
| Nacionalidad | 24 | 0,009 | no |
| Estudiante internacional | 25 | 0,000 | no |

Tienen peso alto: Edad al ingresar. Conviene leerlo junto
con las diferencias entre subgrupos de la sección 5: el peso indica que el modelo usa la
variable para estimar, no que esa característica cause el abandono.

## 8. Habilitación

| Momento | Habilitado | Motivo |
|---|---|---|
| Inscripción | sí | Se habilita con el desempeño obtenido (AUC-ROC en prueba 0,7861), que queda informado. |
| Cierre del 1.er semestre | sí | AUC-ROC en prueba 0,8928 > 0,80: alcanza la meta y se habilita. |
| Cierre del 2.º semestre | sí | Se habilita con el desempeño obtenido (AUC-ROC en prueba 0,9177), que queda informado. |

Cada modelo queda registrado en `modelos/<momento>/v<versión>/metadatos.json` con su versión, la
fecha de entrenamiento, la fecha de esta evaluación, sus métricas y sus umbrales.
