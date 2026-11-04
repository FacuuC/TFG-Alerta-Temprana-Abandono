# Informe de validación: Cierre del 2.º semestre (modelo v1.0)

Generado por `scripts/entrenar.py`. Usa **solo entrenamiento y validación**; el conjunto de
prueba no se usó para nada de lo que aparece acá.

- Registros: 2654 de entrenamiento y 885 de validación; proporción de abandono 32,1 % y 32,2 %.
- Variables del momento: 31.
- Desbalance: pesos de clase (`class_weight=balanced` en la regresión logística y `scale_pos_weight` en XGBoost), sin casos sintéticos.

## Elección del modelo (AUC-ROC en validación)

| Modelo | AUC-ROC validación |
|---|---|
| Regresión logística (referencia) | 0,9128 |
| Mejor XGBoost de la grilla | 0,9147 |

**Elegido: xgboost** (supera a la referencia).
Hiperparámetros: `{"max_depth": 2, "learning_rate": 0.1, "n_estimators": 200, "scale_pos_weight": 2.115}`.

Se usa la misma grilla que en el cierre del 1.er semestre (extendida el 03/11, antes de entrenar
este momento), sin cambios: la grilla es la misma para los tres momentos.

El mejor XGBoost quedó en el borde de la grilla en: max_depth = 2, learning_rate = 0.1. Se informa y no se
extiende la grilla, para usar la misma en los tres momentos.

### Grilla de XGBoost (36 combinaciones: max_depth [2, 3, 4, 5], learning_rate [0.03, 0.05, 0.1], n_estimators [100, 200, 400])

| max_depth | learning_rate | n_estimators | AUC-ROC validación |
|---|---|---|---|
| 2 | 0,10 | 200 | 0,9147 |
| 2 | 0,05 | 400 | 0,9147 |
| 2 | 0,10 | 400 | 0,9141 |
| 2 | 0,03 | 400 | 0,9135 |
| 2 | 0,10 | 100 | 0,9132 |
| 3 | 0,05 | 400 | 0,9126 |
| 2 | 0,05 | 200 | 0,9125 |
| 3 | 0,03 | 400 | 0,9119 |
| 4 | 0,05 | 400 | 0,9117 |
| 4 | 0,03 | 400 | 0,9114 |
| 2 | 0,03 | 200 | 0,9111 |
| 4 | 0,05 | 200 | 0,9109 |
| 3 | 0,05 | 200 | 0,9105 |
| 5 | 0,05 | 200 | 0,9103 |
| 5 | 0,05 | 400 | 0,9103 |
| 2 | 0,05 | 100 | 0,9102 |
| 5 | 0,03 | 400 | 0,9099 |
| 3 | 0,10 | 100 | 0,9096 |
| 3 | 0,10 | 200 | 0,9096 |
| 5 | 0,03 | 200 | 0,9095 |
| 4 | 0,03 | 200 | 0,9094 |
| 3 | 0,03 | 200 | 0,9093 |
| 4 | 0,10 | 200 | 0,9091 |
| 3 | 0,05 | 100 | 0,9090 |
| 3 | 0,10 | 400 | 0,9086 |
| 3 | 0,03 | 100 | 0,9081 |
| 4 | 0,10 | 100 | 0,9081 |
| 4 | 0,05 | 100 | 0,9076 |
| 5 | 0,05 | 100 | 0,9076 |
| 4 | 0,03 | 100 | 0,9072 |
| 5 | 0,10 | 200 | 0,9068 |
| 5 | 0,03 | 100 | 0,9066 |
| 4 | 0,10 | 400 | 0,9063 |
| 2 | 0,03 | 100 | 0,9062 |
| 5 | 0,10 | 100 | 0,9055 |
| 5 | 0,10 | 400 | 0,9019 |

## Umbrales (fijados con validación)

- Umbral alto: **0,9164** (nivel alto ≤ 15,0 % de los estudiantes).
- Umbral medio: **0,5951** (alto + medio detectan ≥ 80,0 % de los abandonos).

| Comprobación en validación | Valor | Regla |
|---|---|---|
| Estudiantes en nivel alto | 14,9 % | ≤ 15,0 % |
| Abandonos detectados (alto + medio) | 80,0 % | ≥ 80,0 % |
| Abandono observado por nivel (alto / medio / bajo) | 95,5 % / 63,4 % / 9,6 % | decreciente: sí |
| Estudiantes en nivel medio / bajo | 18,2 % / 66,9 % | — |
| Precisión y sensibilidad de la alerta (alto + medio) | 0,778 / 0,800 | — |

## Variables que más pesan en promedio (SHAP, validación)

Media del valor absoluto de SHAP por variable. Muestra cuánto pesa cada variable en las
estimaciones del modelo, no las causas del abandono.

| Variable | Peso medio |
|---|---|
| Materias aprobadas en el 2.º semestre | 1,051 |
| Materias aprobadas en el 1.er semestre | 0,322 |
| Edad al ingresar | 0,299 |
| Nota promedio en el 2.º semestre | 0,278 |
| Carrera | 0,222 |
| Materias inscriptas en el 2.º semestre | 0,212 |
| Becario | 0,127 |
| Género | 0,113 |
| Nivel educativo de la madre | 0,090 |
| Materias acreditadas por equivalencia en el 2.º semestre | 0,086 |

Modelo guardado en `modelos/cierre_2s/v1.0` (sin habilitar hasta la evaluación final).
