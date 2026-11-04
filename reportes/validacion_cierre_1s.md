# Informe de validación: Cierre del 1.er semestre (modelo v1.0)

Generado por `scripts/entrenar.py`. Usa **solo entrenamiento y validación**; el conjunto de
prueba no se usó para nada de lo que aparece acá.

- Registros: 2654 de entrenamiento y 885 de validación; proporción de abandono 32,1 % y 32,2 %.
- Variables del momento: 25.
- Desbalance: pesos de clase (`class_weight=balanced` en la regresión logística y `scale_pos_weight` en XGBoost), sin casos sintéticos.

## Elección del modelo (AUC-ROC en validación)

| Modelo | AUC-ROC validación |
|---|---|
| Regresión logística (referencia) | 0,8871 |
| Mejor XGBoost de la grilla | 0,8878 |

**Elegido: xgboost** (supera a la referencia).
Hiperparámetros: `{"max_depth": 2, "learning_rate": 0.1, "n_estimators": 400, "scale_pos_weight": 2.115}`.

La primera grilla (profundidad 3 a 5, tasa 0,05 y 0,1, 200 y 400 árboles) dejó su mejor
resultado en el borde (profundidad 3, 200 árboles, tasa 0,1; AUC-ROC 0,8833, por debajo de la
referencia). Por eso se extendió hacia modelos más simples. La regla de elección no cambió.

### Grilla de XGBoost (36 combinaciones: max_depth [2, 3, 4, 5], learning_rate [0.03, 0.05, 0.1], n_estimators [100, 200, 400])

| max_depth | learning_rate | n_estimators | AUC-ROC validación |
|---|---|---|---|
| 2 | 0,10 | 400 | 0,8878 |
| 2 | 0,05 | 400 | 0,8875 |
| 2 | 0,10 | 200 | 0,8870 |
| 2 | 0,03 | 400 | 0,8850 |
| 2 | 0,10 | 100 | 0,8844 |
| 2 | 0,05 | 200 | 0,8838 |
| 3 | 0,10 | 200 | 0,8833 |
| 3 | 0,10 | 100 | 0,8827 |
| 4 | 0,05 | 200 | 0,8819 |
| 3 | 0,05 | 200 | 0,8817 |
| 3 | 0,03 | 400 | 0,8815 |
| 4 | 0,03 | 400 | 0,8812 |
| 4 | 0,05 | 400 | 0,8809 |
| 3 | 0,05 | 400 | 0,8808 |
| 4 | 0,03 | 200 | 0,8807 |
| 2 | 0,03 | 200 | 0,8806 |
| 4 | 0,05 | 100 | 0,8805 |
| 3 | 0,03 | 200 | 0,8796 |
| 5 | 0,03 | 400 | 0,8795 |
| 5 | 0,03 | 200 | 0,8794 |
| 5 | 0,10 | 100 | 0,8793 |
| 2 | 0,05 | 100 | 0,8791 |
| 4 | 0,03 | 100 | 0,8790 |
| 3 | 0,05 | 100 | 0,8787 |
| 3 | 0,10 | 400 | 0,8786 |
| 5 | 0,05 | 200 | 0,8783 |
| 5 | 0,05 | 100 | 0,8783 |
| 5 | 0,03 | 100 | 0,8779 |
| 3 | 0,03 | 100 | 0,8779 |
| 5 | 0,10 | 200 | 0,8776 |
| 4 | 0,10 | 100 | 0,8776 |
| 5 | 0,05 | 400 | 0,8773 |
| 4 | 0,10 | 200 | 0,8770 |
| 4 | 0,10 | 400 | 0,8739 |
| 2 | 0,03 | 100 | 0,8737 |
| 5 | 0,10 | 400 | 0,8706 |

## Umbrales (fijados con validación)

- Umbral alto: **0,8936** (nivel alto ≤ 15,0 % de los estudiantes).
- Umbral medio: **0,5301** (alto + medio detectan ≥ 80,0 % de los abandonos).

| Comprobación en validación | Valor | Regla |
|---|---|---|
| Estudiantes en nivel alto | 14,9 % | ≤ 15,0 % |
| Abandonos detectados (alto + medio) | 80,0 % | ≥ 80,0 % |
| Abandono observado por nivel (alto / medio / bajo) | 93,9 % / 53,1 % / 10,2 % | decreciente: sí |
| Estudiantes en nivel medio / bajo | 22,1 % / 62,9 % | — |
| Precisión y sensibilidad de la alerta (alto + medio) | 0,695 / 0,800 | — |

## Variables que más pesan en promedio (SHAP, validación)

Media del valor absoluto de SHAP por variable. Muestra cuánto pesa cada variable en las
estimaciones del modelo, no las causas del abandono.

| Variable | Peso medio |
|---|---|
| Materias aprobadas en el 1.er semestre | 1,295 |
| Edad al ingresar | 0,356 |
| Materias inscriptas en el 1.er semestre | 0,330 |
| Carrera | 0,291 |
| Nota promedio en el 1.er semestre | 0,278 |
| Becario | 0,184 |
| Género | 0,181 |
| Materias acreditadas por equivalencia en el 1.er semestre | 0,165 |
| Desempleo del año de ingreso | 0,164 |
| Nivel educativo del padre | 0,130 |

Modelo guardado en `modelos/cierre_1s/v1.0` (sin habilitar hasta la evaluación final).
