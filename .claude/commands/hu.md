---
description: Planificar una historia de usuario del Sprint 1 (ejemplo: /hu HU-002)
argument-hint: HU-00X
---

Vamos a trabajar la historia $ARGUMENTS del Sprint 1.

1. Leé `docs/sprint-1/README.md`, `docs/sprint-1/$ARGUMENTS.md` y todos los documentos
   que esa historia lista en «Leer antes». Revisá también `docs/proyecto/08-decisiones.md`
   y `docs/sprint-1/avance.md`.
2. Revisá el código existente para saber qué ya está hecho y qué historias anteriores
   dejaron disponible.
3. Si la historia depende de una decisión **pendiente** de `08-decisiones.md`, preguntame
   antes de seguir, mostrando la propuesta por defecto.
4. Proponé un plan **sin escribir código todavía**, con:
   - los archivos que vas a crear o modificar;
   - cada tarea del sprint backlog de la historia y cómo la resolvés;
   - una tabla «criterio de aceptación → cómo se cumple → prueba que lo verifica»;
   - riesgos o dudas, y cualquier diferencia con el documento.
5. Esperá mi aprobación. Después implementá tarea por tarea, corriendo `pytest` al final
   de cada una, y avisame si algo del plan cambia.

Respetá las reglas de `CLAUDE.md`, en especial el uso del conjunto de prueba, las
variables por momento, la seudonimización y los términos fijos.
