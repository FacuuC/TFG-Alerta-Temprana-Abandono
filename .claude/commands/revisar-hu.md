---
description: Verificar si una historia cumple sus criterios de aceptación (ejemplo: /revisar-hu HU-002)
argument-hint: HU-00X
---

Revisá si la historia $ARGUMENTS está terminada, según la definición de terminado de
`docs/sprint-1/README.md`. No modifiques código en esta revisión.

1. Leé `docs/sprint-1/$ARGUMENTS.md`.
2. Corré `pytest` y anotá el resultado.
3. Armá una tabla con cada criterio de aceptación: **cumple / no cumple / parcial**, y la
   evidencia concreta (prueba que lo verifica, archivo y función, o salida de un comando).
   No des un criterio por cumplido sin evidencia.
4. Verificá las reglas de `CLAUDE.md` que apliquen: conjunto de prueba usado una sola vez,
   variables por momento, sin datos identificatorios, términos fijos en la interfaz y en
   los textos.
5. Listá lo que falta y cualquier diferencia con el documento que haya que anotar en
   `docs/pendientes-documento.md`.
6. Si todo cumple, proponé el mensaje de commit (`$ARGUMENTS: …`) y la fila para
   `docs/sprint-1/avance.md`.
