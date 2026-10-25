# Prompts · registro de versiones

Cada archivo `*.vN.md` es inmutable una vez usado en una corrida; un cambio crea `vN+1` y una entrada aquí. Las trazas guardan `prompt_file` y `prompt_sha256`.

## 2026-10-25

- `decisions.v1` — Primera versión. Motivo: F1 (estados de decisión no finales: el D2 solo encontró 10/30). Rol único (solo decisiones), estados copiados del `SYSTEM` del D2, procedimiento por tema (listar temas → recorrer cronológicamente → estado según el último turno), regla explícita de reemplazo = dos decisiones enlazadas, uso de `find_revision_cues`/`inspect_evidence` (ReAct), `thought` + `topic_plan` como CoT, modo revisión.
- `tasks.v1` — Primera versión. Motivo: F2 (plazos 12/39 correctos) y F3 (47/56 tareas como `pending`). Regla "tarea confirmada → `final`", responsable solo si es participante (`check_participant`), plazo anclado en `resolve_deadline` (ambiguo → `null`, hora solo si el texto la deja clara), nunca inventar fechas, modo revisión.
- `auditor.v1` — Primera versión. Motivo: F4 (nadie verifica respaldo de la cita; omisiones heredadas). Chain-of-Verification con checklist cerrado por ítem (enum `problem`), omisiones vía `find_uncovered_commitments` (`item_id = "NEW"`, `missing_item`), reglas de `route`.
- `fewshot/decisions.TR01` — Primera versión. Reunión de train TR01 resumida (dos reemplazos, un rechazo, un pendiente) con `topic_plan` y salida derivada de su rúbrica.
- `fewshot/tasks.TR01` — Primera versión. Reunión de train TR01 resumida (tres tareas `final`, hora ambigua completada desde el texto, tercero no asignable, pendiente que no es tarea). Se omite la tarea de "antes del viernes": su plazo en la rúbrica (fecha de reunión + 3 días) no coincide con `resolve_deadline` y contradiría la regla anclada en la herramienta.
