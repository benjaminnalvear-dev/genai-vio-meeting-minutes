# Entregable 3 · Spec de diseño: sistema de agentes para actas verificables

- **Fecha:** 2026-10-24 · **Entrega:** 2026-10-31 23:59
- **Rama:** `deliverable-3` (base: `main` @ `75004dc`, commit congelado del D2)
- **Estado:** diseño aprobado por secciones; pendiente revisión de este documento.

---

## 1. Objetivo y restricciones

Reconstruir la solución del D2 (JSON restringido + herramientas determinísticas en dos pasadas) como un **sistema de al menos tres agentes** con roles distintos, y medir qué técnicas de prompting explican la mejora.

Restricciones del enunciado:

- Un agente es una llamada al modelo con rol, prompt propio, entrada y salida definidas, que **decide** qué sigue (llamar herramienta, pasar trabajo, revisarse o detenerse). Una secuencia fija es un pipeline y no cuenta.
- Todos los agentes usan el mismo modelo open-weight ≤ 8B: `ministral-3:3b-instruct-2512-q4_K_M` vía Ollama (mismo del D2).
- Resultados para: baseline directo, solución D2, sistema completo y sistema sin cada técnica clave (una a la vez), con las mismas entradas y el mismo criterio de corrección.
- Trazas de los mensajes entre agentes para cada entrada; en el repo, las del video y la del caso de falla.
- Prompt de cada agente en archivo separado y versionado, fuera del código.
- Entregables: video ≤ 3 min, PDF LaTeX vertical de una página con grafo de agentes, repo reproducible.

Decisiones del equipo: ejecución en Google Colab T4; orquestación con LangGraph; paquete Python nuevo; mismas 10 reuniones de test y mismo evaluador del D2; PDF en inglés y README en español; taxonomía de técnicas: *The Prompt Report* (Schulhoff et al., 2024).

Comentarios del profesor sobre el D2 que este diseño atiende: (1) dejar clara la dificultad del benchmark; (2) formato más visual para comparar estrategias; (3) introducir el problema desde la problemática.

## 2. Diagnóstico de partida (análisis de dificultad, test M01–M10)

Calculado con el evaluador del D2 copiado sin cambios; el F1 recalculado coincide con el `summary.json` del D2 (0,477/0,559/0,667 decisiones; 0,667/0,709/0,716 tareas).

**Dificultad del benchmark.** 347 turnos (30–46 por reunión, ~1,2–2,1k tokens). 56 decisiones, de las cuales **30 (54 %) no son `final`**: 11 `superseded`, 11 `rejected`, 8 `pending`. 20 temas con revisión (cadena máxima 3 en M01; distancia media propuesta→reemplazo de 17–20 turnos en M01 y M03). 10 decisiones y 15 tareas condicionales. 53 tareas, todas `final` en gold; 29 con plazo relativo (8 con hora). 11 terceros ausentes mencionados 24 veces.

**Fallas medidas de la solución D2 (`combined_v2`):**

| Falla | Medición |
|---|---|
| F1 · Estados de decisión no finales | Encuentra 25/26 finales pero solo 10/30 no finales (rejected 3/11, superseded 3/11 y solo 1 con estado correcto, pending 4/8) |
| F2 · Plazos de tareas | 12/39 correctos (31 %): 12 día equivocado, 9 inventados, 5 hora mal/falta, 1 omitido |
| F3 · Estado de tareas | 47/56 tareas predichas como `pending` (gold: todas `final`) |
| F4 · Respaldo y omisiones (caso M01 del D2) | Nadie verifica que la cita respalde cada campo; la segunda pasada hereda omisiones del borrador |

Asignaciones a terceros ausentes: 0 en las tres configuraciones del D2 sobre test (trampa ya resuelta en este set; se sigue midiendo).

El script de este análisis (`scripts/benchmark_difficulty.py`) se incorpora al repo y alimenta la sección "dificultad del benchmark" del PDF.

## 3. Arquitectura (enfoque A: especialistas + auditor con loop)

```
                 ┌──► Agente Decisiones ──┐
Transcripción ───┤                        ├──► Agente Auditor ──► route=finish o ronda 2 ──► Finalizador ──► Acta JSON
                 └──► Agente Tareas ──────┘          │
                          ▲     ▲                    │ route ∈ {decisions, tasks, both}
                          └─────┴── ítems marcados + feedback ┘
```

Se descartaron: (B) extractor→verificador→corrector, demasiado cercano al pipeline del D2 y con roles no ligados a las fallas; (C) supervisor + trabajadores, poco fiable como router con un modelo de 3B y difícil de ablacionar.

### 3.1 Mecanismo de decisión: ReAct sobre JSON restringido

Cada paso de agente es una llamada a Ministral con `format=<schema>` (constrained decoding del D2). Esquema común de paso:

```json
{
  "thought": "string",
  "action": "call_tools | finish",
  "tool_calls": [{"tool": "<enum de herramientas del agente>", "evidence_id": "<enum de IDs reales | null>", "name": "string | null"}],
  "<salida del agente>": "...se llena solo cuando action = finish"
}
```

- Nombres de herramienta e IDs de evidencia son `enum` → no se pueden inventar.
- Python ejecuta las herramientas pedidas y devuelve las observaciones como mensaje siguiente; el agente decide de nuevo.
- Se pueden pedir varias herramientas por paso (máximo 8, `maxItems`); una llamada idéntica a otra ya ejecutada en la misma invocación reutiliza su observación (marcada `duplicate: true`).
- Límite: **3 pasos** por invocación de especialista y por invocación del Auditor; en el último paso el esquema solo admite `action = finish`.
- Se descartó function calling nativo de Ollama (poco fiable con 3B e incompatible con `format=schema`) y herramientas fijas (equivale al D2).

### 3.2 Herramientas (determinísticas)

| Herramienta | Origen | Devuelve | Agentes |
|---|---|---|---|
| `inspect_evidence(evidence_id)` | D2 | turno citado + vecinos ±1 + participantes | todos |
| `find_revision_cues()` | D2 `revision_cues` | turnos con marcas de reemplazo/rechazo/aprobación/pendiente | Decisiones, Auditor |
| `resolve_deadline(evidence_id)` | D2 | fecha ISO sugerida o "ambigua/no forzar" | Tareas, Auditor |
| `check_participant(name)` | D2 (`assignee_named_in_meeting`), ampliada | si `name` es un speaker participante; si es tercero mencionado | Tareas |
| `find_uncovered_commitments()` (Python le pasa los ítems actuales) | **nueva** | turnos con marcas de compromiso o acuerdo ("yo me encargo", "quedamos", "me comprometo", "yo preparo"…) que ningún ítem cita | Auditor |

### 3.3 Agentes

**Agente Decisiones** — ataca F1.
- Rol: identificar temas y seguir la historia de cada decisión (propuesta → reemplazo → rechazo → pendiente).
- Entrada: transcripción en el formato del D2 (`transcript_text`). En revisión: además, ítems marcados y feedback del Auditor.
- Herramientas: `find_revision_cues`, `inspect_evidence`.
- Salida (en `finish`): `decisions[]` con el esquema de decisión del D2, más `topic_plan` (lista de temas con IDs en orden cronológico) que el Finalizador descarta.
- Parada/traspaso: `finish` o 3 pasos → Auditor.
- Técnicas (The Prompt Report): *role prompting*; *decomposition* (plan por tema antes de clasificar); *few-shot* (un ejemplo de train con cadena de reemplazo y un rechazo); *thought generation / CoT* (campo `thought` + `topic_plan`); *agents: ReAct / tool use*.

**Agente Tareas** — ataca F2 y F3.
- Rol: extraer obligaciones: quién, qué, para cuándo, con qué condición.
- Entrada: transcripción, `meeting_date`, participantes. En revisión: ítems marcados y feedback.
- Herramientas: `resolve_deadline`, `check_participant`, `inspect_evidence`.
- Salida (en `finish`): `tasks[]` con el esquema de tarea del D2.
- Parada/traspaso: `finish` o 3 pasos → Auditor.
- Técnicas: *role prompting*; *few-shot* de train (tarea confirmada → `final`; plazo ausente en la cita → `null`; "antes de las seis" en la tarde → 18:00); regla anclada en herramienta (todo plazo no nulo debe venir de `resolve_deadline`; si la herramienta dice ambiguo → `null`); *ReAct / tool use*.
- El estado de tareas se corrige vía prompt; el esquema del D2 no cambia (sin desviación).

**Agente Auditor** — ataca F4.
- Rol: verificar cada ítem contra su cita, detectar omisiones y decidir la ruta.
- Entrada: `decisions[]`, `tasks[]`, transcripción.
- Herramientas: `inspect_evidence`, `find_uncovered_commitments`, `find_revision_cues`, `resolve_deadline` (para no marcar como error un plazo bien calculado).
- Salida (en `finish`): `verdicts[]` = `{item_id, ok, problem, detail}` con `problem ∈ {evidence_not_supporting, wrong_state, wrong_deadline, wrong_assignee, merged_items, missing_item, null}`; y `route ∈ {decisions, tasks, both, finish}`.
- Parada/traspaso: `route = finish` o ronda de auditoría 2 cumplida → Finalizador; si no, ítems marcados + feedback → especialista(s) indicados.
- Técnicas: *self-criticism / Chain-of-Verification* (pregunta de verificación por ítem); checklist cerrado (enum `problem`); *ReAct / tool use*.
- **Barandas determinísticas** (`src/minutes_agents/guards.py`, activas salvo en la condición `no_guards`). Motivo: en la corrida de validación (VA01, VA02) el Auditor de 3B propuso problemas falsos, los especialistas los obedecieron y agregaron ítems duplicados o falsos; el F1 antes de la auditoría superó al de después en 4/4 casos. El Auditor sigue proponiendo veredictos, pero Python verifica cada afirmación verificable con las mismas herramientas determinísticas antes de que llegue a un especialista: **G0** descarta veredictos sobre ítems inexistentes; **G1** acepta un `missing_item` solo con `item_id = NEW` y si `detail` cita un turno con compromiso sin cubrir (`find_uncovered_commitments`) o con señal de cambio que ninguna decisión cita (`find_revision_cues`); el NEW aceptado va solo al especialista correspondiente (tareas si el turno es un compromiso sin cubrir, decisiones si no); **G2** descarta `wrong_deadline` si el día del plazo coincide con `resolve_deadline`; **G3** descarta `wrong_state` sobre una decisión cuyo estado está respaldado (superseded con sucesora cuya evidencia es señal de cambio; rejected con "descart-/rechaz-" en la cita; pending con "pendiente"; final nunca se descarta); **G4** descarta todo `wrong_state` sobre tareas (una tarea confirmada es `final` por regla del proyecto); **G5** descarta `wrong_assignee` si el responsable es participante y habla o es nombrado en el turno citado; **G6** descarta `merged_items` sobre una decisión que es parte de una cadena de reemplazo. Tras filtrar, la ruta se **recalcula** desde los veredictos aceptados (la ruta original del Auditor queda en la traza como `auditor_route`). Después de cada fusión, **G7** descarta un ítem nuevo cuyo `evidence_id` ya cita un ítem existente. Cada veredicto o ítem descartado se registra en la traza como evento `guard` con su motivo. Riesgo declarado de G7: si dos tareas distintas se confirman en el mismo turno y la segunda solo aparece en una revisión, se pierde.

**Finalizador** — nodo determinístico, **no es un agente** (se declara así).
- Fusiona salidas: los ítems no marcados por el Auditor se conservan tal cual (una revisión no puede perder ítems).
- Renumera IDs (`d01…`, `t01…`) y reescribe `supersedes` coherentemente.
- Aplica `apply_safe_checks` del D2 (IDs inexistentes, fechas no ISO).
- Cierra la traza.

Justificación de la división: decisiones y tareas fallan distinto (estado vs plazo) y usan herramientas distintas; un 3B rinde mejor con una responsabilidad por prompt. El Auditor es el único que revisa el trabajo de otros y controla el loop; un especialista no se audita bien a sí mismo.

### 3.4 Estado del grafo (LangGraph `StateGraph`)

`meeting_id`, `transcript`, `decisions`, `tasks`, `verdicts`, `route`, `audit_round`, `flagged_items`, `trace`, `config` (condición de ablación), `call_count`.

Aristas: `START → decisions → tasks → auditor` (secuencial: una sola GPU T4 y orden determinístico de trazas); arista condicional `auditor → {decisions, tasks, both, finalize}` según `route` y `audit_round`; `finalize → END`.

## 4. Evaluación

### 4.1 Higiene de datos
- Train (50 reuniones): solo fuente de ejemplos few-shot.
- Validation (10): ajuste de prompts y límites.
- Test (M01–M10): una única corrida final con todo congelado.

### 4.2 Condiciones (misma sesión de Colab T4, mismas 10 reuniones de test, `temperature=0`, `seed=42`, `num_ctx=12288`)

| # | Condición | Mide |
|---|---|---|
| 1 | Baseline (prompt directo del D2) | punto de partida |
| 2 | D2 `combined_v2`, re-ejecutado | continuidad; números congelados del D2 se citan como referencia |
| 3 | Sistema completo | resultado principal |
| 4 | − ReAct (Python ejecuta todas las herramientas del agente sobre todos los IDs candidatos antes de la llamada y entrega los informes; cada agente hace un solo paso con `action = finish`) | valor de que el agente elija herramientas |
| 5 | − Auditor (0 rondas) | self-criticism / CoVe y loop |
| 6 | − Few-shot (ambos especialistas) | ejemplos de transiciones, plazos, estado de tareas |
| 7 | − Descomposición/CoT (sin `topic_plan` ni `thought`) | razonar antes de clasificar |
| 8 | − Barandas (`no_guards`: los veredictos del Auditor llegan sin filtrar a los especialistas, con su ruta original; sin G7) | valor de verificar con código lo que propone el Auditor |

No se ablacionan, y se declara: *role prompting* (bajo valor esperado, costo de una corrida) y constrained decoding (sin él se rompe el parseo ReAct; su efecto ya se midió en el D2).

### 4.3 Métricas
- **Principales (sin cambio):** F1 de decisiones y F1 de tareas con el evaluador del D2 (`content_score`, `match_items`, umbral 0,55).
- **Secundarias (nuevas, declaradas):** F1 estricto (emparejado y estado correcto); recall por tipo de trampa (final simple, final tras reemplazo, superseded, rejected, pending, condicional, plazo relativo, sin plazo); exactitud de plazo, estado de tareas y responsable; asignaciones a no participantes; llamadas, tokens y segundos por reunión.
- **Comparación pareada:** reuniones (de 10) en que el sistema completo gana/empata/pierde frente al D2 en F1 de decisiones, F1 de tareas y F1 estricto.

### 4.4 Figuras (generadas desde los JSON de resultados)
1. Barras agrupadas: F1 decisiones, F1 tareas y F1 estricto por condición.
2. Heatmap: condición × tipo de trampa → recall.
3. Grafo de agentes (TikZ): cada agente y herramienta como nodo, cada traspaso como arista etiquetada con lo que pasa, loops y paradas marcados.

### 4.5 Trazas
`traces/<condición>/<meeting_id>.jsonl`, una línea por evento: `ts`, `agent`, `step`, `prompt_file`, `prompt_sha256`, `thought`, `action`, `tool_calls`, `observations`, `output`, `seconds`, `tokens`, `prompt_tokens`, `done_reason`, `context_warning` (estimación del prompt > 9500 tokens). Los eventos `router` registran `route`, `flagged`, `next` (o `skipped` cuando el especialista no tiene veredictos y no se le llama) y, con barandas, `auditor_route` (la ruta que propuso el Auditor antes del filtro). Los eventos `guard` (`step = 0`) registran cada veredicto o ítem descartado por las barandas: `item_id`, `problem`, `guard` (`G0`–`G7`) y `reason`. El costo por reunión (`seconds`) es la suma de los `seconds` de los pasos (las respuestas en caché conservan su tiempo original); `wall_seconds` es el reloj de pared. Se versionan en el repo las de las reuniones del video y la del caso de falla. Caso de falla: la reunión con peor F1 estricto del sistema completo (criterio objetivo).

## 5. Repositorio y reproducibilidad

```
deliverable3/
├── requirements.txt          # versiones fijadas
├── prompts/                  # decisions.v1.md, tasks.v1.md, auditor.v1.md, fewshot/, CHANGELOG.md
├── configs/                  # full, no_react, no_auditor, no_fewshot, no_cot
├── src/minutes_agents/       # data, llm, schemas, tools, agents/, graph, finalize, d2_reference, evaluate, tracing
├── scripts/                  # run_experiment.py, make_figures.py, benchmark_difficulty.py
├── notebooks/D3_Colab.ipynb  # instala, clona commit fijo, corre DEMO (M01) o FULL, descarga resultados
├── tests/                    # herramientas, paridad del evaluador con D2, grafo con LLM falso
├── results/test/             # summary.json, salidas por condición, figuras
├── traces/
├── paper/                    # fuente LaTeX + build con verificación de una página
└── docs/spec.md              # este documento
```

- El código del D2 se reimplementa en módulos; `GenAI Constrained+Tool use/` queda intacto.
- Cada prompt se carga desde archivo; su ruta y hash quedan en cada traza.
- Tests sin GPU: herramientas; **paridad** (el evaluador reproduce el `summary.json` del D2 desde `minutas_resultados_test.zip`); grafo con LLM falso (rutas, loop, límites de pasos y rondas, conservación de ítems no marcados).
- Notebook: modo `DEMO` (M01, trazas impresas por agente, para el video) y `FULL` (8 condiciones).
- README en español con pasos para reproducir el video y las trazas.
- Video ≤ 3 min: Colab corriendo M01 en vivo con mensajes entre agentes visibles, acta final y figuras de la corrida completa. M01 por orden de archivo, igual que en el D2.
- PDF en inglés, LaTeX, una página: problemática → dificultad del benchmark → grafo → diseño y técnicas por agente → resultados visuales y ablaciones → caso de falla → limitaciones y reproducción.
- Nada se publica (push) sin instrucción explícita del autor.

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Costo de Colab (~6–10 llamadas/reunión × 8 condiciones ≈ 2–2,5 h T4) | Límites de pasos/rondas parametrizados; cache por llamada como en el D2 para reanudar |
| Ministral 3B no sigue el protocolo ReAct | Esquema fuerza estructura y enums; último paso fuerza `finish`; se valida en validation antes de test |
| El loop empeora ítems correctos | Solo se revisan ítems marcados; el Finalizador conserva los demás |
| Resultados dependen de versión de Ollama | Se registra versión de Ollama y digest del modelo; D2 se re-ejecuta en la misma sesión |
| 10 reuniones dan estimaciones inestables | Comparación pareada por reunión y desglose por trampa; se declara como limitación |
