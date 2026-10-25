EJEMPLO DE REFERENCIA (reunión de entrenamiento, resumida). No copies sus valores: aplica el mismo razonamiento a la reunión real.
(En las decisiones superseded, evidence_id es el turno donde se propuso la opción, aunque la rúbrica original de esta reunión cite el turno del reemplazo.)

{"meeting_id": "TR01", "meeting_date": "2026-10-03", "title": "Plan de capacitación interna", "participants": ["Hablante 01", "Hablante 02", "Hablante 03", "Hablante 04"]}
INTERVENCIONES EN ORDEN (resumidas):
u03 | 00:00:26 | Hablante 03: La primera propuesta es taller presencial.
u05 | 00:00:48 | Hablante 01: Propongo aprobar taller presencial y avanzar hoy mismo.
u06 | 00:00:59 | Hablante 02: Todavía no. Si relator externo no está disponible, esa opción no sirve.
u09 | 00:01:32 | Hablante 04: En materiales, inicialmente pensé en guía digital.
u10 | 00:01:43 | Hablante 02: Eso elevaría bastante el costo. Prefiero sala de capacitación.
u11 | 00:01:54 | Hablante 01: Por ahora no cerremos los materiales; primero veamos el presupuesto.
u14 | 00:02:27 | Hablante 02: También se mencionó materiales impresos, pero no lo considero necesario.
u15 | 00:02:38 | Hablante 04: Estoy de acuerdo: lo descartamos para esta etapa.
u16 | 00:02:49 | Hablante 01: Entonces queda rechazada la propuesta de materiales impresos.
u18 | 00:03:11 | Hablante 02: Con esa confirmación, prefiero taller híbrido; es más acotado y permite partir.
u19 | 00:03:22 | Hablante 01: De acuerdo: aprobamos taller híbrido. Esto reemplaza la propuesta inicial de taller presencial.
u26 | 00:04:39 | Hablante 02: Falta definir si tendremos una medición posterior de resultados.
u27 | 00:04:50 | Hablante 03: Podría ser una encuesta breve, pero no tenemos definido quién la haría.
u28 | 00:05:01 | Hablante 01: Ese tema queda pendiente; no asignemos responsable ni fecha todavía.
u29 | 00:05:12 | Hablante 04: Llegó la cotización: sala de capacitación cabe en el presupuesto.
u30 | 00:05:23 | Hablante 01: Listo, aprobamos sala de capacitación. Esto reemplaza la propuesta de guía digital.
u31 | 00:05:34 | Hablante 02: Para cerrar, queda taller híbrido, sala de capacitación, y las tres tareas ya asignadas.

PLAN POR TEMA (va en topic_plan si el formato lo incluye):
[
 {
  "topic": "Modalidad",
  "evidence_ids": [
   "u03",
   "u05",
   "u06",
   "u18",
   "u19"
  ]
 },
 {
  "topic": "Materiales",
  "evidence_ids": [
   "u09",
   "u10",
   "u11",
   "u29",
   "u30"
  ]
 },
 {
  "topic": "Propuesta descartada",
  "evidence_ids": [
   "u14",
   "u15",
   "u16"
  ]
 },
 {
  "topic": "Medición posterior",
  "evidence_ids": [
   "u26",
   "u27",
   "u28"
  ]
 }
]

SALIDA ESPERADA (decisions):
[
 {
  "id": "d01",
  "topic": "Modalidad",
  "statement": "taller presencial",
  "state": "superseded",
  "condition": null,
  "supersedes": null,
  "evidence_id": "u05"
 },
 {
  "id": "d02",
  "topic": "Modalidad",
  "statement": "taller híbrido",
  "state": "final",
  "condition": null,
  "supersedes": "d01",
  "evidence_id": "u19"
 },
 {
  "id": "d03",
  "topic": "Materiales",
  "statement": "guía digital",
  "state": "superseded",
  "condition": null,
  "supersedes": null,
  "evidence_id": "u09"
 },
 {
  "id": "d04",
  "topic": "Materiales",
  "statement": "sala de capacitación",
  "state": "final",
  "condition": null,
  "supersedes": "d03",
  "evidence_id": "u30"
 },
 {
  "id": "d05",
  "topic": "Propuesta descartada",
  "statement": "materiales impresos",
  "state": "rejected",
  "condition": null,
  "supersedes": null,
  "evidence_id": "u16"
 },
 {
  "id": "d06",
  "topic": "Medición posterior",
  "statement": "Definir una encuesta breve de resultados",
  "state": "pending",
  "condition": null,
  "supersedes": null,
  "evidence_id": "u28"
 }
]

POR QUÉ:
- Modalidad: u05 propone taller presencial, u06 lo frena y u19 aprueba taller híbrido y dice que "reemplaza" al presencial → dos decisiones: d01 superseded y d02 final con supersedes = "d01". d01 cita u05 (donde se propuso el presencial) y d02 cita u19 (donde se aprueba el híbrido).
- Materiales: u11 deja el tema abierto, pero u30 lo cierra después → no es pending. Guía digital queda superseded y cita u09 (donde se propuso); sala de capacitación queda final y cita u30.
- Materiales impresos: u16 dice "queda rechazada" → rejected (descarte explícito, no reemplazo).
- Medición posterior: u28 dice "queda pendiente" y no hay cierre después → pending.
