# Prompts · registro de versiones

Cada archivo `*.vN.md` es inmutable una vez usado en una corrida; un cambio crea `vN+1` y una entrada aquí. Las trazas guardan `prompt_file` y `prompt_sha256`.

## 2026-10-25

- `decisions.v1` — Primera versión. Motivo: F1 (estados de decisión no finales: el D2 solo encontró 10/30). Rol único (solo decisiones), estados copiados del `SYSTEM` del D2, procedimiento por tema (listar temas → recorrer cronológicamente → estado según el último turno), regla explícita de reemplazo = dos decisiones enlazadas, uso de `find_revision_cues`/`inspect_evidence` (ReAct), `thought` + `topic_plan` como CoT, modo revisión.
- `tasks.v1` — Primera versión. Motivo: F2 (plazos 12/39 correctos) y F3 (47/56 tareas como `pending`). Regla "tarea confirmada → `final`", responsable solo si es participante (`check_participant`), plazo anclado en `resolve_deadline` (ambiguo → `null`, hora solo si el texto la deja clara), nunca inventar fechas, modo revisión.
- `auditor.v1` — Primera versión. Motivo: F4 (nadie verifica respaldo de la cita; omisiones heredadas). Chain-of-Verification con checklist cerrado por ítem (enum `problem`), omisiones vía `find_uncovered_commitments` (`item_id = "NEW"`, `missing_item`), reglas de `route`.
- `fewshot/decisions.TR01` — Primera versión. Reunión de train TR01 resumida (dos reemplazos, un rechazo, un pendiente) con `topic_plan` y salida derivada de su rúbrica.
- `fewshot/tasks.TR01` — Primera versión. Reunión de train TR01 resumida (tres tareas `final`, hora ambigua completada desde el texto, tercero no asignable, pendiente que no es tarea). Se omite la tarea de "antes del viernes": su plazo en la rúbrica (fecha de reunión + 3 días) no coincide con `resolve_deadline` y contradiría la regla anclada en la herramienta.

## 2026-10-25 (enmienda antes de cualquier corrida)

- `decisions.v1` — Paso 4 corregido (aún no se había usado en ninguna corrida, por eso se enmienda v1 en vez de crear v2). Antes decía que la decisión anterior lleva `supersedes=null`, lo que impedía cadenas de más de dos pasos. Ahora: en toda decisión, superseded o final, `supersedes` = id de la que reemplaza (null si es la primera propuesta del tema), con ejemplo A → B → C. Motivo: F1, hay cadenas de reemplazo de 3 pasos. El few-shot TR01 ya cumple la regla (sus decisiones superseded son primeras propuestas).

## 2026-10-25 (referencias D2)

- `d2_system.v1` — Copia literal del `SYSTEM` del D2 (celda 4 del notebook), sin cambios. Lo usan las condiciones de referencia `baseline` y `combined_v2` para enviar exactamente los mismos mensajes que el D2; un test verifica la igualdad con el notebook.
- `d2_review.v1` — Copia literal del texto de revisión de `combined_v2` (celda 6, desde "Revisa todas las intervenciones."), sin cambios. El código antepone el borrador, las salidas de herramientas y los indicios de cambios, separados con un salto de línea.

## 2026-10-25 (v2, aprobada por Eduardo antes de la primera corrida)

- `decisions.v2` + `fewshot/decisions.TR01.v2` — Una decisión `superseded` cita el turno donde se PROPUSO esa opción, no el del reemplazo. Motivo: en test las 11 decisiones reemplazadas citan su propio turno (en train las 100 citan el turno del reemplazo: convención distinta entre splits). Con la regla v1 el sistema perdería coincidencia de evidencia justo en F1. El few-shot v2 se aparta a propósito de la rúbrica de TR01 en esos dos `evidence_id` (d01 → u05, d03 → u09).
- `decisions.v2`, `tasks.v2`, `auditor.v2` — "Mientras pidas herramientas (action=call_tools), deja las salidas vacías". Motivo: el esquema exige las claves de salida en todo paso, y el modelo escribía un borrador completo antes de cada llamada a herramientas, duplicando tiempo y contexto (riesgo de truncamiento en num_ctx=12288).
- `auditor.v2` — La pregunta 3 del checklist compara el plazo con `resolve_deadline` (herramienta nueva para el Auditor) y solo marca `wrong_deadline` si el texto no dice plazo o el día no coincide. Motivo: el Auditor no podía calcular fechas y podía marcar como error plazos bien resueltos por el Agente de Tareas.
- `fewshot/tasks.TR01` sin cambios: train no contiene tareas sin plazo ni horas "de la tarde", así que el ejemplo pedido en el spec §3.3 no puede venir de train. Decisión (Eduardo, 2026-10-25): se mantiene solo como regla escrita en `tasks.v2` (regla 4) y se declara como limitación en el PDF.
