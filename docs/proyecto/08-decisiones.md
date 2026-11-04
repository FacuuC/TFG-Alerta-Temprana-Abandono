# Decisiones

## Tomadas (están en el documento o confirmadas por Facundo)

| Fecha | Decisión |
|---|---|
| 14/10 | Se excluye «necesidades educativas especiales» (dato sensible) |
| 14/10 | La plataforma no muestra nombres ni documentos; el tutor identifica al estudiante por el código en el sistema de gestión |
| 14/10 | Los datos de la plataforma son «seudonimizados»; el dataset de Realinho es «anonimizado» |
| 15/10 | Núcleo del Sprint 1: HU-001 a HU-006, con HU-007 como última historia (primera en salir si hay atraso) |
| 15/10 | Stack: Dash + FastAPI (backend interno) + PostgreSQL, en Docker |
| 15/10 | Partición estratificada 60/20/20; la prueba se usa una sola vez |
| 15/10 | Capacidad supuesta del Programa de Tutorías: nivel alto ≤ 15 %; alto + medio detectan ≥ 80 % de los abandonos |
| 15/10 | Etiqueta binaria: abandono frente a no abandono (graduado o sigue cursando); se informa también el AUC-ROC sin «sigue cursando» |
| 15/10 | Objetivo 4 en versión liviana: formulario con capturas de 6 casos, mínimo 5 evaluadores |
| 16/10 | SHAP muestra cuánto pesa cada variable, no causas; sesgos con evaluación por subgrupos (AUC-ROC, sensibilidad, precisión) |
| 17/10 | Tres momentos del primer año, un modelo por momento; meta de AUC-ROC > 0,80 en el cierre del 1.er semestre |
| 17/10 | Regresión logística como modelo de referencia; desbalance con pesos de clase, sin casos sintéticos |
| 19/10 | Se excluyen deudor, aranceles al día, orden de postulación y nota de admisión: quedan 31 predictoras (19, 25 y 31 por momento) |
| 24/10 | Inicio de sesión por rol (HU-009) en un Sprint 2, después del 09/11 |
| 02/11 | Desarrollo historia por historia con Claude Code en modo plan, verificando los criterios de aceptación entre una y otra |
| 02/11 | Repositorio en `TFG - Desarrollo Plataforma`; entorno con Python 3.13 y Docker Desktop en Windows 11 |
| 03/11 | **Código seudonimizado (P1):** `EST-` + 8 caracteres hexadecimales del HMAC-SHA256 del legajo (12 en total, VARCHAR(12)). Se descartan los 6 caracteres de las pantallas dibujadas: con 4.424 estudiantes había alrededor de un 44 % de probabilidad de que dos compartieran código; con 8 baja a alrededor del 0,2 %. Igual, la carga controla que no haya códigos repetidos |
| 03/11 | **Cuestionario (P8):** se envía apenas estén las seis fichas (objetivo: martes 03/11 a la noche o miércoles 04/11) y se cierra el domingo 08/11 a las 20; análisis el lunes 09/11 a la mañana. El modelo de `cierre_1s` queda congelado desde que se generan las fichas |
| 03/11 | **Códigos de las categóricas (P10):** el archivo de UCI usa los códigos originales (carrera 33 a 9991, ocupaciones 0 a 195), no los correlativos del anexo; la correspondencia está verificada en `docs/datos/anexo-codigos-realinho-2022.md`. Dataset verificado: 4.424 × 37, distribución 2.209/1.421/794, SHA-256 `3ef126de…c45ae` |
| 03/11 | **P6, P7 y P9 confirmadas:** modelos en `modelos/<momento>/v<versión>/` (pipeline + `metadatos.json`, versionados en Git); los 6 casos del cuestionario se eligen al azar con semilla 42, dos por nivel; las variables macroeconómicas se mantienen |
| 03/11 | **Modelo de cierre_1s v1.0 (congelado):** XGBoost con profundidad 2, tasa 0,1 y 400 árboles (`scale_pos_weight` 2,115). AUC-ROC de validación 0,8878 frente a 0,8871 de la regresión logística: empate práctico, se aplica la regla del documento (XGBoost si supera a la referencia). La grilla inicial (profundidad 3-5, tasa 0,05-0,1, 200-400 árboles; mejor 0,8833) dejó el óptimo en el borde y se extendió a profundidad 2-5, tasa 0,03-0,1 y 100-400 árboles; las dos están en `reportes/validacion_cierre_1s.md`. Umbrales: alto 0,8936; medio 0,5301. Las fichas del cuestionario salen de este modelo, así que no se reentrena |
| 03/11 | **Versiones (P11):** fijadas y probadas con Python 3.13 (15 pruebas en verde, app y base conectadas); todas tienen ruedas para Windows. Se usa `uvicorn` sin el extra `[standard]`, porque incluye uvloop, que no existe para Windows |

## Pendientes (propuestas por defecto, a confirmar)

Si una historia depende de una de estas, se confirma antes de implementarla. Cuando se
confirme, pasa a la tabla de arriba con la fecha.

| N.º | Tema | Propuesta por defecto | Afecta a |
|---|---|---|---|
| P2 | **Formato de los archivos de carga** | Tres CSV del conjunto de prueba, uno por momento, cada uno con todo lo disponible hasta ese momento, más identificadores sintéticos y las variables excluidas, para demostrar el descarte (`04-datos.md`) | HU-001, HU-003 |
| P3 | **Alertas al recalcular** | Una alerta por estudiante. Si el nuevo nivel es alto o medio y no tenía alerta, se crea en «pendiente». Si ya tenía, se actualiza su predicción y **se conserva el estado** (HU-007, criterio 4). Si baja a nivel bajo, la alerta queda con su estado y su nivel actual, y desaparece del filtro por defecto («Alto y medio») sin perder el seguimiento | HU-003, HU-004, HU-007 |
| P4 | **Dash y la API interna** | Los callbacks de Dash llaman directamente a las funciones de `servicio/`; FastAPI expone las mismas funciones en `/api/` | Todas las de interfaz |
| P5 | **Usuario sin inicio de sesión** | Selector de usuario de prueba en la barra superior; queda registrado en CARGA y CAMBIO_ESTADO | HU-001, HU-007 |
| P12 | **Repositorio público** | GitHub, nombre sugerido `alerta-temprana-abandono`, público desde la entrega (lo pide el encuentro 4) | Demo |
