EJEMPLO DE REFERENCIA (reunión de entrenamiento, resumida). No copies sus valores: aplica el mismo razonamiento a la reunión real.

{"meeting_id": "TR01", "meeting_date": "2026-10-03", "title": "Plan de capacitación interna", "participants": ["Hablante 01", "Hablante 02", "Hablante 03", "Hablante 04"]}
INTERVENCIONES EN ORDEN (resumidas):
u02 | 00:00:15 | Hablante 02: Antes de decidir, programa de capacitación nos envió una alternativa, pero esa persona no participa en esta reunión.
u07 | 00:01:10 | Hablante 03: Yo puedo confirmar la disponibilidad con administración.
u08 | 00:01:21 | Hablante 01: Hablante 03 confirma la disponibilidad de relator externo hoy.
u12 | 00:02:05 | Hablante 03: Puedo pedir la cotización y traer el monto mañana antes de las 12.
u13 | 00:02:16 | Hablante 01: Hablante 03 solicita la cotización para sala de capacitación y la envía mañana antes de las 12.
u23 | 00:04:06 | Hablante 03: Sobre las personas asistentes, propongo que Hablante 04 haga una lista de convocados.
u24 | 00:04:17 | Hablante 04: Sí, preparo la lista y la comparto hoy.
u25 | 00:04:28 | Hablante 01: Hablante 04 prepara y comparte hoy la lista de convocados.
u26 | 00:04:39 | Hablante 02: Falta definir si tendremos una medición posterior de resultados.
u27 | 00:04:50 | Hablante 03: Podría ser una encuesta breve, pero no tenemos definido quién la haría.
u28 | 00:05:01 | Hablante 01: Ese tema queda pendiente; no asignemos responsable ni fecha todavía.

OBSERVACIONES DE HERRAMIENTAS (resumidas):
[
 {
  "tool": "resolve_deadline",
  "evidence_id": "u08",
  "suggested": "2026-10-03",
  "reason": "fecha explícita calculada"
 },
 {
  "tool": "resolve_deadline",
  "evidence_id": "u13",
  "suggested": "2026-10-04",
  "reason": "hora ambigua: solo día calculado"
 },
 {
  "tool": "resolve_deadline",
  "evidence_id": "u25",
  "suggested": "2026-10-03",
  "reason": "fecha explícita calculada"
 },
 {
  "tool": "check_participant",
  "name": "Hablante 03",
  "is_participant": true
 },
 {
  "tool": "check_participant",
  "name": "programa de capacitación",
  "is_participant": false,
  "mentioned_in_text": true
 }
]

SALIDA ESPERADA (tasks):
[
 {
  "id": "t01",
  "description": "Confirmar la disponibilidad de relator externo",
  "assignee": "Hablante 03",
  "deadline": "2026-10-03",
  "condition": null,
  "state": "final",
  "evidence_id": "u08"
 },
 {
  "id": "t02",
  "description": "Solicitar la cotización para sala de capacitación",
  "assignee": "Hablante 03",
  "deadline": "2026-10-04T12:00",
  "condition": null,
  "state": "final",
  "evidence_id": "u13"
 },
 {
  "id": "t03",
  "description": "Preparar y compartir la lista de convocados",
  "assignee": "Hablante 04",
  "deadline": "2026-10-03",
  "condition": null,
  "state": "final",
  "evidence_id": "u25"
 }
]

POR QUÉ:
- Todas las tareas confirmadas tienen state = final, aunque todavía no se hayan hecho.
- t01: u07 ofrece la acción y u08 la confirma con responsable y "hoy" → evidence_id = u08; resolve_deadline da 2026-10-03.
- t02: resolve_deadline da solo el día (2026-10-04, hora ambigua); el texto dice "antes de las 12" → se agrega T12:00.
- t03: u25 confirma a Hablante 04 y "hoy" → 2026-10-03, sin hora porque no se dice una hora.
- programa de capacitación (u02) es un tercero que no participa: nunca es assignee.
- u28 deja la medición "pendiente" sin responsable ni fecha → no es una tarea.
