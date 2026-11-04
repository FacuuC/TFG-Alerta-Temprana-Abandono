# Informe de validación: Inscripción (modelo v1.0)

Generado por `scripts/entrenar.py`. Usa **solo entrenamiento y validación**; el conjunto de
prueba no se usó para nada de lo que aparece acá.

- Registros: 2654 de entrenamiento y 885 de validación; proporción de abandono 32,1 % y 32,2 %.
- Variables del momento: 19.
- Desbalance: pesos de clase (`class_weight=balanced` en la regresión logística y `scale_pos_weight` en XGBoost), sin casos sintéticos.

## Elección del modelo (AUC-ROC en validación)

| Modelo | AUC-ROC validación |
|---|---|
| Regresión logística (referencia) | 0,7673 |
| Mejor XGBoost de la grilla | 0,7701 |

**Elegido: xgboost** (supera a la referencia).
Hiperparámetros: `{"max_depth": 2, "learning_rate": 0.1, "n_estimators": 200, "scale_pos_weight": 2.115}`.

Se usa la misma grilla que en el cierre del 1.er semestre (extendida el 03/11, antes de entrenar
este momento), sin cambios: la grilla es la misma para los tres momentos.

El mejor XGBoost quedó en el borde de la grilla en: max_depth = 2, learning_rate = 0.1. Se informa y no se
extiende la grilla, para usar la misma en los tres momentos.

### Grilla de XGBoost (36 combinaciones: max_depth [2, 3, 4, 5], learning_rate [0.03, 0.05, 0.1], n_estimators [100, 200, 400])

| max_depth | learning_rate | n_estimators | AUC-ROC validación |
|---|---|---|---|
| 2 | 0,10 | 200 | 0,7701 |
| 2 | 0,05 | 400 | 0,7697 |
| 3 | 0,03 | 400 | 0,7692 |
| 5 | 0,03 | 400 | 0,7686 |
| 4 | 0,10 | 100 | 0,7684 |
| 5 | 0,05 | 200 | 0,7683 |
| 4 | 0,03 | 400 | 0,7679 |
| 3 | 0,05 | 200 | 0,7675 |
| 3 | 0,05 | 400 | 0,7668 |
| 5 | 0,03 | 200 | 0,7664 |
| 4 | 0,05 | 200 | 0,7663 |
| 2 | 0,10 | 400 | 0,7660 |
| 3 | 0,10 | 200 | 0,7659 |
| 4 | 0,10 | 200 | 0,7657 |
| 3 | 0,10 | 100 | 0,7643 |
| 2 | 0,03 | 400 | 0,7633 |
| 4 | 0,05 | 400 | 0,7632 |
| 4 | 0,03 | 200 | 0,7631 |
| 5 | 0,05 | 100 | 0,7613 |
| 4 | 0,05 | 100 | 0,7612 |
| 2 | 0,05 | 200 | 0,7608 |
| 2 | 0,10 | 100 | 0,7605 |
| 5 | 0,05 | 400 | 0,7599 |
| 3 | 0,03 | 200 | 0,7598 |
| 5 | 0,10 | 100 | 0,7587 |
| 5 | 0,03 | 100 | 0,7569 |
| 3 | 0,10 | 400 | 0,7566 |
| 3 | 0,05 | 100 | 0,7562 |
| 2 | 0,03 | 200 | 0,7544 |
| 4 | 0,03 | 100 | 0,7536 |
| 4 | 0,10 | 400 | 0,7531 |
| 2 | 0,05 | 100 | 0,7516 |
| 5 | 0,10 | 200 | 0,7488 |
| 3 | 0,03 | 100 | 0,7485 |
| 2 | 0,03 | 100 | 0,7440 |
| 5 | 0,10 | 400 | 0,7340 |

## Umbrales (fijados con validación)

- Umbral alto: **0,7293** (nivel alto ≤ 15,0 % de los estudiantes).
- Umbral medio: **0,4241** (alto + medio detectan ≥ 80,0 % de los abandonos).

| Comprobación en validación | Valor | Regla |
|---|---|---|
| Estudiantes en nivel alto | 14,9 % | ≤ 15,0 % |
| Abandonos detectados (alto + medio) | 80,0 % | ≥ 80,0 % |
| Abandono observado por nivel (alto / medio / bajo) | 65,9 % / 42,9 % / 13,4 % | decreciente: sí |
| Estudiantes en nivel medio / bajo | 37,2 % / 47,9 % | — |
| Precisión y sensibilidad de la alerta (alto + medio) | 0,495 / 0,800 | — |

## Variables que más pesan en promedio (SHAP, validación)

Media del valor absoluto de SHAP por variable. Muestra cuánto pesa cada variable en las
estimaciones del modelo, no las causas del abandono.

| Variable | Peso medio |
|---|---|
| Edad al ingresar | 0,403 |
| Becario | 0,367 |
| Carrera | 0,305 |
| Género | 0,231 |
| Modalidad de ingreso | 0,125 |
| Nivel educativo de la madre | 0,082 |
| Ocupación de la madre | 0,081 |
| Nota de los estudios previos | 0,078 |
| Nivel educativo del padre | 0,076 |
| Ocupación del padre | 0,061 |

Modelo guardado en `modelos/inscripcion/v1.0` (sin habilitar hasta la evaluación final).
