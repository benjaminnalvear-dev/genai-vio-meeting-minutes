# Entregable 3 · Plan de implementación: sistema de agentes para actas verificables

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconstruir la solución del D2 como un grafo LangGraph de tres agentes ReAct (Decisiones, Tareas, Auditor) sobre Ministral 3B, con trazas, ablaciones medidas con el evaluador del D2 y entregables (figuras, notebook, README, PDF).

**Architecture:** Paquete `minutes_agents` en `deliverable3/src/`. Cada agente es un bucle ReAct cuyo paso es una llamada a Ollama con `format=<json schema>`; Python ejecuta las herramientas determinísticas que el agente pide. LangGraph conecta Decisiones → Tareas → Auditor con arista condicional de vuelta (máx. 2 rondas) y un Finalizador determinístico. Todo el código que toca el modelo recibe un objeto `LLM` inyectable, así que los tests corren con un `FakeLLM` sin GPU; las corridas reales se hacen en Colab T4.

**Tech Stack:** Python 3.11 local / Colab, LangGraph, requests, jsonschema, matplotlib, pytest; Ollama + `ministral-3:3b-instruct-2512-q4_K_M`.

**Spec:** `deliverable3/docs/spec.md`

## Global Constraints

- Modelo único en todos los agentes: `ministral-3:3b-instruct-2512-q4_K_M`.
- Parámetros de inferencia: `{'temperature': 0, 'seed': 42, 'num_ctx': 12288, 'num_predict': 2400}` (igual que D2).
- El evaluador del D2 (`norm`, `recover_baseline`, `comparable_date`, `content_score`, `match_items`, umbral `0.55`, pesos `0.70/0.15/0.15` y `0.80/0.20`) se copia **sin cambios**.
- El esquema de decisión y tarea del D2 (`make_schema`) no cambia; estados `['final','superseded','rejected','pending']`.
- Límites por defecto: `max_steps = 3` por invocación de agente; `auditor_rounds = 2`.
- Few-shot solo desde train (IDs `TR..`); ajuste solo en validation (`VA..`); test (`M01–M10`) se corre una vez al final.
- Todo prompt vive en `deliverable3/prompts/*.md`; ninguna string de prompt en `.py`.
- `GenAI Constrained+Tool use/` y el resto del repo del D2 no se modifican.
- Commits locales en la rama `deliverable-3`; **nunca `git push`** sin orden explícita de Eduardo.
- Mensajes de commit terminan con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Todos los comandos se ejecutan desde `deliverable3/` con el venv activo (`.venv`).

## Review Focus

- La salida del modelo no parsea como JSON (o `parsed` es `None`) en medio de un bucle ReAct → el agente termina con su salida previa (o vacía) y lo registra en la traza; nunca lanza excepción ni pierde ítems ya aceptados. Test en Task 6.
- El modelo pide una herramienta con argumento nulo o inexistente (`evidence_id: null`, nombre vacío) → la herramienta devuelve `{'error': ...}` como observación, no excepción. Test en Task 3.
- El Auditor sigue pidiendo revisiones al agotar `auditor_rounds` → el grafo va igual al Finalizador. Test en Task 8.
- Una revisión devuelve un ítem con `id` que no estaba marcado o un `supersedes` que apunta a un id inexistente → el merge solo reemplaza ids marcados, agrega nuevos y el Finalizador pone `supersedes = null` si no resuelve. Test en Task 7.
- Una corrida de Colab se corta a la mitad → al reejecutar, el cache de llamadas reutiliza respuestas y no repite llamadas. Test en Task 4.

---

### Task 1: Andamiaje, carga de datos y evaluador D2 con test de paridad

**Por qué primero:** si el evaluador no reproduce exactamente los números del D2, ninguna comparación posterior vale (rúbrica de continuidad).

**Files:**
- Create: `deliverable3/requirements.txt`, `deliverable3/pytest.ini`, `deliverable3/.gitignore`
- Create: `deliverable3/src/minutes_agents/__init__.py`, `data.py`, `evaluate.py`
- Create: `deliverable3/tests/conftest.py`, `deliverable3/tests/test_evaluate_parity.py`

**Interfaces:**
- Produces:
  - `data.extract_dataset(zip_path: Path, dest: Path) -> Path` (descomprime `train/validation/test` como en la celda 2 del D2; devuelve `dest`).
  - `data.load_split(root: Path, split: str) -> tuple[dict[str, dict], dict[str, dict]]` → `(transcripts, gold)` indexados por `meeting_id`, con las mismas validaciones del D2.
  - `evaluate.norm`, `recover_baseline`, `comparable_date`, `content_score(a, b, kind) -> float`, `match_items(pred, gold, kind) -> list[tuple[dict, dict, float]]` (verbatim del D2).
  - `evaluate.evaluate_arm(outputs: dict[str, dict], transcripts: dict, gold: dict, is_baseline: bool, arm: str) -> dict` con las mismas claves que cada elemento del `summary.json` del D2 (`json_valid`, `schema_valid`, `decisions{matched,predicted,gold,precision,recall,f1}`, `tasks{...}`, `state_accuracy_matched`, `assignee_accuracy_matched`, `deadline_accuracy_matched`, `evidence_exact_matched`, `evidence_id_exists`, `seconds_total`, `per_meeting`). `outputs[mid]` es el dict de resultado de una llamada (`raw`, `parsed`, `seconds`, ...).
  - `evaluate.make_schema(tr) -> dict` vive en `schemas.py` (Task 5); aquí `evaluate_arm` lo importa de `minutes_agents.schemas`. Para no adelantar Task 5, en esta task se crea `schemas.py` con **solo** `STATES` y `make_schema` copiados del D2.
- Fixture compartida (`tests/conftest.py`): `repo_root()`, `dataset_dir(tmp_path_factory)` (extrae `GenAI Constrained+Tool use/Fine Tuning.zip` una vez por sesión) y `d2_results_dir(tmp_path_factory)` (extrae `minutas_resultados_test.zip`).

- [ ] **Step 1: Crear venv e instalar dependencias**

```bash
cd deliverable3
python -m venv .venv && .venv/Scripts/activate
pip install langgraph requests jsonschema matplotlib pytest
pip freeze | grep -iE "^(langgraph|langchain-core|requests|jsonschema|matplotlib|pytest)==" > requirements.txt
```
Expected: `requirements.txt` con versiones exactas. `.gitignore` incluye `.venv/`, `__pycache__/`, `.cache/`. `pytest.ini` define `pythonpath = src` y `testpaths = tests`.

- [ ] **Step 2: Escribir el test de paridad (falla)**

```python
# tests/test_evaluate_parity.py
ARMS = {'baseline': 'baseline', 'structured': 'structured', 'combined': 'combined_v2'}
KEYS = ['json_valid', 'schema_valid', 'state_accuracy_matched', 'assignee_accuracy_matched',
        'deadline_accuracy_matched', 'evidence_exact_matched', 'evidence_id_exists', 'seconds_total']

def test_evaluator_reproduces_d2_summary(dataset_dir, d2_results_dir):
    transcripts, gold = load_split(dataset_dir, 'test')
    expected = {row['arm']: row for row in json.loads((d2_results_dir / 'summary.json').read_text('utf-8'))}
    for arm, suffix in ARMS.items():
        outputs = {m: json.loads((d2_results_dir / f'{m}_{suffix}.json').read_text('utf-8')) for m in sorted(transcripts)}
        got = evaluate_arm(outputs, transcripts, gold, is_baseline=(arm == 'baseline'), arm=arm)
        for kind in ('decisions', 'tasks'):
            assert got[kind] == expected[arm][kind]
        for k in KEYS:
            assert got[k] == expected[arm][k]

def test_load_split_counts(dataset_dir):
    assert [len(load_split(dataset_dir, s)[0]) for s in ('train', 'validation', 'test')] == [50, 10, 10]
```

- [ ] **Step 3: Correr y ver que falla**

Run: `pytest tests/test_evaluate_parity.py -v` → Expected: FAIL (`ImportError`).

- [ ] **Step 4: Implementar `data.py`, `schemas.py` (solo `STATES`, `make_schema`) y `evaluate.py`**

Copiar del notebook D2 (`GenAI Constrained+Tool use/Ministral_Minutas_Colab.ipynb`, celdas 2, 4 y 9) cambiando solo los globales (`MEETING_IDS`, `RUNS`, `TRANSCRIPTS`, `GOLD`) por parámetros. `evaluate_arm` itera `sorted(outputs)`.

- [ ] **Step 5: Correr y ver que pasa**

Run: `pytest -v` → Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add deliverable3/requirements.txt deliverable3/pytest.ini deliverable3/.gitignore deliverable3/src deliverable3/tests
git commit -m "feat(d3): port D2 data loader and evaluator with parity test"
```

---

### Task 2: Métricas extendidas y análisis de dificultad

**Por qué:** responde al comentario del profe (dificultad del benchmark) y da el F1 estricto y el desglose por trampa que mostrarán la mejora en estados.

**Files:**
- Create: `deliverable3/src/minutes_agents/metrics.py`, `deliverable3/scripts/benchmark_difficulty.py`
- Test: `deliverable3/tests/test_metrics.py`

**Interfaces:**
- Consumes: `evaluate.match_items`, `recover_baseline`, `comparable_date`, `norm`; `data.load_split`.
- Produces:
  - `metrics.ABSENT: dict[str, list[str]]` = `{'M01':['paula'],'M02':['sofia'],'M03':['martin','organizador'],'M04':['camila'],'M05':['javier'],'M06':['paula'],'M07':['andres'],'M08':['agencia'],'M09':['lucia'],'M10':['gerente']}` (de `evaluation_notes`).
  - `metrics.deadline_kind(task: dict, tr: dict) -> str` ∈ `{'sin plazo (null)', 'fecha explícita', 'relativo (hoy/mañana/día)', 'plazo no está en la cita'}`.
  - `metrics.decision_kind(d: dict) -> str` ∈ `{'final simple', 'final tras reemplazo', 'superseded', 'rejected', 'pending'}`.
  - Claves de `per_trap`: `'D: ' + decision_kind(d)`, `'T: ' + deadline_kind(t, tr)`, más `'D: con condición'` y `'T: con condición'`.
  - `metrics.difficulty_table(transcripts, gold) -> list[dict]` (una fila por reunión, columnas como en el análisis del 2026-10-24).
  - `metrics.extended_metrics(outputs, transcripts, gold, is_baseline: bool) -> dict` con claves `strict_f1{decisions,tasks}`, `per_trap{categoría:{gold,found,state_ok,deadline_ok,assignee_ok}}`, `deadline_errors{ok,dia equivocado,inventado,hora mal/falta,omitido}`, `task_states_predicted{estado:n}`, `non_participant_assignees: int`, `per_meeting{mid:{decisions_f1,tasks_f1,strict_f1}}`, `calls_total`, `tokens_total`.
  - `metrics.paired_comparison(per_meeting_a: dict, per_meeting_b: dict, key: str) -> dict` → `{'wins': int, 'ties': int, 'losses': int}` (a frente a b; empate si |Δ| < 1e-9).
  - `scripts/benchmark_difficulty.py --data <dir> --out <dir>`: escribe `difficulty_per_meeting.json` e imprime totales.

- [ ] **Step 1: Escribir tests (fallan)**

```python
def test_difficulty_totals(dataset_dir):
    rows = difficulty_table(*load_split(dataset_dir, 'test'))
    tot = lambda k: sum(r[k] for r in rows)
    assert (tot('turnos'), tot('decisiones'), tot('tareas')) == (347, 56, 53)
    assert (tot('superseded'), tot('rejected'), tot('pending'), tot('final')) == (11, 11, 8, 26)
    assert (tot('plazo_relativo'), tot('terceros_ausentes'), tot('menciones_ausentes')) == (29, 11, 24)

def test_extended_metrics_d2_combined(dataset_dir, d2_results_dir):
    tr, gold = load_split(dataset_dir, 'test')
    outs = {m: json.loads((d2_results_dir / f'{m}_combined_v2.json').read_text('utf-8')) for m in sorted(tr)}
    em = extended_metrics(outs, tr, gold, is_baseline=False)
    found = lambda c: em['per_trap'][c]['found']
    assert found('D: final simple') + found('D: final tras reemplazo') == 25
    assert found('D: superseded') + found('D: rejected') + found('D: pending') == 10
    assert em['deadline_errors']['ok'] == 12 and sum(em['deadline_errors'].values()) == 39
    assert em['task_states_predicted']['pending'] == 47
    assert em['non_participant_assignees'] == 2

def test_paired_comparison():
    a = {'M01': {'f': .5}, 'M02': {'f': .7}, 'M03': {'f': .2}}
    b = {'M01': {'f': .4}, 'M02': {'f': .7}, 'M03': {'f': .3}}
    assert paired_comparison(a, b, 'f') == {'wins': 1, 'ties': 1, 'losses': 1}
```

- [ ] **Step 2: Correr y ver que falla** — `pytest tests/test_metrics.py -v` → FAIL (`ImportError`).

- [ ] **Step 3: Implementar `metrics.py` y el script**

Portar la lógica de `scratchpad/scripts/benchmark_difficulty.py` (análisis del 2026-10-24). F1 estricto: un par emparejado cuenta como TP solo si `pred.state == gold.state`; precisión y recall sobre los mismos totales que el F1 del D2. `calls_total`/`tokens_total` suman `calls` y `eval_count` cuando existan en `outputs[mid]` (0 si no).

- [ ] **Step 4: Correr y ver que pasa** — `pytest -v` → todo pasa.

- [ ] **Step 5: Commit** — `git commit -m "feat(d3): add extended metrics and benchmark difficulty analysis"`

---

### Task 3: Herramientas determinísticas

**Por qué:** son las acciones que los agentes eligen; deben ser idénticas al D2 donde ya existían para que la ablación −ReAct sea comparable.

**Files:**
- Create: `deliverable3/src/minutes_agents/tools.py`
- Test: `deliverable3/tests/test_tools.py`

**Interfaces:**
- Produces (todas puras, `tr` = transcripción):
  - `inspect_evidence(tr, evidence_id) -> dict` (D2 verbatim).
  - `resolve_deadline(tr, evidence_id, draft_value=None) -> dict` (D2 verbatim, incluidas las constantes `MONTHS`, `WEEKDAYS`, `WORD_HOURS`).
  - `find_revision_cues(tr) -> list[dict]` (D2 `revision_cues` verbatim).
  - `check_participant(tr, name) -> dict` → `{'name', 'is_participant': bool, 'mentioned_in_text': bool, 'participants': list[str]}`; `is_participant` = `name` coincide exactamente con un `speaker`; `mentioned_in_text` = `norm(name)` aparece en `norm(text)` de algún turno.
  - `find_uncovered_commitments(tr, items: list[dict]) -> list[dict]` → turnos `{'id','speaker','text'}` cuyo texto normalizado contiene `COMMITMENT_PATTERN` y que **ni ellos ni sus vecinos ±1** son citados por algún `item['evidence_id']`.
  - `COMMITMENT_PATTERN = r'\b(yo (puedo|me encargo|reviso|preparo|presento|armo|consolido|envio|entrego)|me encargo|me comprometo|queda a cargo|quedamos en|lo envio|voy a)\b'` (aplicado sobre `norm(text)`).
  - `TOOLS: dict[str, Callable[[dict, dict, dict], dict | list]]` = adaptadores `(tr, call, ctx) -> observación` para los nombres `inspect_evidence`, `find_revision_cues`, `resolve_deadline`, `check_participant`, `find_uncovered_commitments`. `call` es un elemento de `tool_calls` (`{'tool','evidence_id','name'}`); `ctx` trae `{'items': [...]}`. Argumento faltante/inexistente → `{'tool': ..., 'error': '<motivo>'}`.

- [ ] **Step 1: Escribir tests (fallan)**

```python
def test_resolve_deadline_matches_d2(m01):
    assert resolve_deadline(m01, 'u33')['suggested'] == '2026-09-18T17:00'
    r = resolve_deadline(m01, 'u08')
    assert (r['suggested'], r['reason']) == ('2026-09-14', 'hora ambigua: solo día calculado')

def test_check_participant(m01):
    assert check_participant(m01, 'Speaker 02')['is_participant'] is True
    p = check_participant(m01, 'Paula')
    assert (p['is_participant'], p['mentioned_in_text']) == (False, True)
    assert check_participant(m01, 'Reunión posterior')['mentioned_in_text'] is False

def test_uncovered_commitments_m01(m01, m01_gold):
    items = [x for x in m01_gold['decisions'] + m01_gold['tasks'] if x['evidence_id'] != 'u19']
    assert {u['id'] for u in find_uncovered_commitments(m01, items)} == {'u18', 'u19'}

def test_tool_adapters_return_error_not_raise(m01):
    assert 'error' in TOOLS['inspect_evidence'](m01, {'tool': 'inspect_evidence', 'evidence_id': None}, {'items': []})
    assert 'error' in TOOLS['check_participant'](m01, {'tool': 'check_participant', 'name': ''}, {'items': []})
```
(`m01`/`m01_gold` son fixtures nuevas en `conftest.py` sobre el split test.)

- [ ] **Step 2: Correr y ver que falla** — `pytest tests/test_tools.py -v` → FAIL.
- [ ] **Step 3: Implementar `tools.py`** (copiar celda 6 del D2 para las tres primeras).
- [ ] **Step 4: Correr y ver que pasa** — `pytest -v` → todo pasa.
- [ ] **Step 5: Commit** — `git commit -m "feat(d3): add deterministic tools incl. participant and commitment checks"`

---

### Task 4: Cliente LLM, cache, prompts versionados y trazas

**Por qué:** separa el modelo del resto (tests sin GPU), permite reanudar Colab y deja cada mensaje entre agentes en la traza con el hash del prompt usado.

**Files:**
- Create: `deliverable3/src/minutes_agents/llm.py`, `prompts.py`, `tracing.py`
- Create: `deliverable3/tests/fakes.py`
- Test: `deliverable3/tests/test_infra.py`

**Interfaces:**
- Produces:
  - `llm.MODEL = 'ministral-3:3b-instruct-2512-q4_K_M'`, `llm.PARAMS` (Global Constraints).
  - `class LLM(Protocol): def chat(self, messages: list[dict], schema: dict | None) -> dict` → resultado con claves del D2 `raw, parsed, seconds, eval_count, prompt_eval_count, schema_valid`.
  - `llm.OllamaLLM(host='http://127.0.0.1:11434', model=MODEL, params=PARAMS)` (cuerpo = `inference()` del D2).
  - `llm.CachedLLM(inner: LLM, cache_dir: Path)`: clave = sha256 de `json.dumps({'messages','schema','model','params'}, sort_keys=True)`; guarda/lee `<clave>.json`; contador `calls_made`.
  - `prompts.Prompt` (dataclass: `name, text, path, sha256`); `prompts.load_prompt(name: str, prompts_dir: Path = PROMPTS_DIR) -> Prompt` lee `prompts/<name>.md` (p. ej. `'decisions.v1'`, `'fewshot/decisions.TR01'`).
  - `tracing.Tracer(path: Path | None)`: `.log(agent: str, step: int, **fields)` agrega una línea JSON con `ts` y los campos del spec §4.5; `path=None` guarda solo en memoria; `.events: list[dict]`.
  - `tests/fakes.FakeLLM(script: list[dict | str])`: devuelve en orden; cada elemento es el objeto JSON que "responde el modelo" (o un string crudo inválido); registra `.calls` con `(messages, schema)`.

- [ ] **Step 1: Escribir tests (fallan)**

```python
def test_cached_llm_reuses_responses(tmp_path):
    fake = FakeLLM([{'a': 1}])
    c = CachedLLM(fake, tmp_path)
    msgs = [{'role': 'user', 'content': 'x'}]
    assert c.chat(msgs, None)['parsed'] == {'a': 1}
    assert CachedLLM(FakeLLM([]), tmp_path).chat(msgs, None)['parsed'] == {'a': 1}  # no llama al modelo

def test_prompt_hash(tmp_path):
    (tmp_path / 'x.v1.md').write_text('hola', encoding='utf-8')
    p = load_prompt('x.v1', tmp_path)
    assert p.sha256 == hashlib.sha256('hola'.encode()).hexdigest()

def test_tracer_writes_jsonl(tmp_path):
    t = Tracer(tmp_path / 't.jsonl'); t.log('decisions', 1, action='finish')
    line = json.loads((tmp_path / 't.jsonl').read_text('utf-8').splitlines()[0])
    assert (line['agent'], line['step'], line['action']) == ('decisions', 1, 'finish') and 'ts' in line
```

- [ ] **Step 2: Correr y ver que falla.**
- [ ] **Step 3: Implementar** los tres módulos y `fakes.py`.
- [ ] **Step 4: Correr y ver que pasa** — `pytest -v`.
- [ ] **Step 5: Commit** — `git commit -m "feat(d3): add LLM client with cache, versioned prompt loader and tracer"`

---

### Task 5: Esquemas ReAct

**Por qué:** el esquema es lo que obliga al 3B a respetar el protocolo (herramientas e IDs como `enum`, último paso solo `finish`).

**Files:**
- Modify: `deliverable3/src/minutes_agents/schemas.py`
- Test: `deliverable3/tests/test_schemas.py`

**Interfaces:**
- Consumes: `make_schema(tr)` (Task 1).
- Produces:
  - `decision_item_schema(tr) -> dict`, `task_item_schema(tr) -> dict` (los `items` de `make_schema`).
  - `verdict_schema(item_ids: list[str]) -> dict` → `{item_id: enum(item_ids + ['NEW']), ok: bool, problem: enum([...spec §3.3...]) | null, detail: string}`.
  - `step_schema(tr, tools: list[str], output: dict[str, dict], *, allow_tools: bool, with_thought: bool) -> dict`: objeto con `action` (`enum ['call_tools','finish']` o `['finish']` si `not allow_tools`), `tool_calls` (array de `{tool: enum(tools), evidence_id: enum(ids)|null, name: string|null}`; `maxItems: 0` si `not allow_tools`), `thought` solo si `with_thought`, y cada clave de `output` (p. ej. `{'decisions': {'type':'array','items':...}, 'topic_plan': {...}}`). `required` = todas las claves presentes; `additionalProperties: False`.

- [ ] **Step 1: Escribir tests (fallan)**

```python
def test_last_step_only_finish(m01):
    s = step_schema(m01, ['inspect_evidence'], {'decisions': {'type': 'array'}}, allow_tools=False, with_thought=True)
    assert s['properties']['action']['enum'] == ['finish']

def test_no_cot_removes_thought(m01):
    s = step_schema(m01, ['inspect_evidence'], {'decisions': {'type': 'array'}}, allow_tools=True, with_thought=False)
    assert 'thought' not in s['properties']

def test_tool_and_evidence_enums(m01):
    s = step_schema(m01, ['inspect_evidence'], {'decisions': {'type': 'array'}}, allow_tools=True, with_thought=True)
    call = s['properties']['tool_calls']['items']['properties']
    assert call['tool']['enum'] == ['inspect_evidence']
    assert 'u42' in call['evidence_id']['enum'] and 'u99' not in call['evidence_id']['enum']
    ok = {'thought': 't', 'action': 'call_tools', 'tool_calls': [{'tool': 'inspect_evidence', 'evidence_id': 'u05', 'name': None}], 'decisions': []}
    assert Draft202012Validator(s).is_valid(ok)
```

- [ ] **Step 2–4:** fallar → implementar → pasar (`pytest -v`).
- [ ] **Step 5: Commit** — `git commit -m "feat(d3): add ReAct step schemas with enums and forced finish"`

---

### Task 6: Motor ReAct genérico

**Por qué:** los tres agentes comparten el mismo bucle; implementarlo una vez y probarlo con `FakeLLM` asegura que las decisiones (herramienta / terminar) se ejecutan y registran.

**Files:**
- Create: `deliverable3/src/minutes_agents/agents/__init__.py`, `agents/base.py`
- Test: `deliverable3/tests/test_react.py`

**Interfaces:**
- Consumes: `schemas.step_schema`, `tools.TOOLS`, `LLM`, `Tracer`, `Prompt`.
- Produces:
  - `RunConfig` (dataclass, en `agents/base.py`): `name: str`, `react: bool = True`, `auditor_rounds: int = 2`, `fewshot: bool = True`, `cot: bool = True`, `max_steps: int = 3`.
  - `AgentSpec` (dataclass): `name: str`, `prompt: Prompt`, `fewshot: Prompt | None`, `tools: list[str]`, `output: Callable[[dict, dict, RunConfig], dict[str, dict]]` (`(tr, ctx, cfg)` → claves de salida para `step_schema`), `precompute: Callable[[dict, dict], list[dict]]` (informes para modo −ReAct).
  - `run_react(spec: AgentSpec, tr: dict, user_content: str, llm: LLM, tracer: Tracer, cfg: RunConfig, ctx: dict) -> dict`:
    - mensajes: `system = spec.prompt.text (+ '\n\n' + spec.fewshot.text si cfg.fewshot)`, `user = user_content`.
    - `cfg.react=False`: agrega al user `'INFORMES DE HERRAMIENTAS:\n' + json(spec.precompute(tr, ctx))` y hace **un** paso con `allow_tools=False`.
    - `cfg.react=True`: hasta `cfg.max_steps` pasos; el último con `allow_tools=False`. Si `action == 'call_tools'`: ejecuta cada `tool_call` con `TOOLS[name](tr, call, ctx)`, agrega `assistant` (raw) y `user` `'OBSERVACIONES:\n' + json(obs)`.
    - Si `parsed is None` o no valida: termina devolviendo `{k: [] ...}` para las claves de salida y loguea `error='invalid_json'`.
    - Cada paso loguea `agent, step, prompt_file, prompt_sha256, thought, action, tool_calls, observations, output, seconds, tokens`.
    - Devuelve `{'output': {claves de salida}, 'steps': int, 'calls': int}`.

- [ ] **Step 1: Escribir tests (fallan)** con un `AgentSpec` de juguete (`tools=['inspect_evidence']`, salida `{'decisions': array}`):

```python
def test_executes_tool_then_finishes(m01, toy_spec):
    fake = FakeLLM([{'thought': 'ver', 'action': 'call_tools', 'tool_calls': [{'tool': 'inspect_evidence', 'evidence_id': 'u05', 'name': None}], 'decisions': []},
                    {'thought': 'listo', 'action': 'finish', 'tool_calls': [], 'decisions': [{'id': 'd01'}]}])
    tr = Tracer(None)
    out = run_react(toy_spec, m01, 'x', fake, tr, RunConfig('full'), {'items': []})
    assert out['output']['decisions'] == [{'id': 'd01'}] and out['calls'] == 2
    assert 'OBSERVACIONES' in fake.calls[1][0][-1]['content'] and 'u05' in fake.calls[1][0][-1]['content']
    assert [e['action'] for e in tr.events] == ['call_tools', 'finish']

def test_last_step_forced_finish(m01, toy_spec):
    loop = {'thought': '', 'action': 'call_tools', 'tool_calls': [], 'decisions': []}
    fake = FakeLLM([loop, loop, {'thought': '', 'action': 'finish', 'tool_calls': [], 'decisions': []}])
    run_react(toy_spec, m01, 'x', fake, Tracer(None), RunConfig('full', max_steps=3), {'items': []})
    assert fake.calls[2][1]['properties']['action']['enum'] == ['finish']

def test_invalid_json_returns_empty(m01, toy_spec):
    out = run_react(toy_spec, m01, 'x', FakeLLM(['no es json']), Tracer(None), RunConfig('full'), {'items': []})
    assert out['output'] == {'decisions': []}

def test_no_react_single_step_with_reports(m01, toy_spec):
    fake = FakeLLM([{'thought': '', 'action': 'finish', 'tool_calls': [], 'decisions': []}])
    run_react(toy_spec, m01, 'x', fake, Tracer(None), RunConfig('no_react', react=False), {'items': []})
    assert len(fake.calls) == 1 and 'INFORMES DE HERRAMIENTAS' in fake.calls[0][0][-1]['content']
```

- [ ] **Step 2–4:** fallar → implementar → pasar.
- [ ] **Step 5: Commit** — `git commit -m "feat(d3): add generic ReAct runner with tracing and no-react mode"`

---

### Task 7: Los tres agentes, sus prompts y el Finalizador

**Por qué:** aquí vive el contenido de cada rol (spec §3.3). Los prompts son archivos versionados; los few-shot vienen de `TR01` (train: 2 superseded, 1 rejected, 1 pending).

**Files:**
- Create: `deliverable3/prompts/decisions.v1.md`, `tasks.v1.md`, `auditor.v1.md`, `prompts/fewshot/decisions.TR01.md`, `prompts/fewshot/tasks.TR01.md`, `prompts/CHANGELOG.md`
- Create: `deliverable3/src/minutes_agents/agents/decisions.py`, `agents/tasks.py`, `agents/auditor.py`, `deliverable3/src/minutes_agents/finalize.py`
- Test: `deliverable3/tests/test_agents.py`, `deliverable3/tests/test_finalize.py`

**Interfaces:**
- Consumes: `AgentSpec`, `RunConfig`, `run_react`, esquemas de Task 5, `load_prompt`, `tools`.
- Produces:
  - `decisions.build(cfg: RunConfig) -> AgentSpec` (tools `['find_revision_cues','inspect_evidence']`; output `decisions` + `topic_plan` si `cfg.cot`; precompute = `find_revision_cues` + `inspect_evidence` de cada cue).
  - `tasks.build(cfg) -> AgentSpec` (tools `['resolve_deadline','check_participant','inspect_evidence']`; output `tasks`; precompute = `resolve_deadline` para todo turno con `suggested` no nulo + `check_participant` de cada participante).
  - `auditor.build(cfg) -> AgentSpec` (tools `['inspect_evidence','find_uncovered_commitments','find_revision_cues']`; output `verdicts` (`verdict_schema` sobre los ids actuales) + `route` enum `['decisions','tasks','both','finish']`; precompute = `find_uncovered_commitments` + `inspect_evidence` de cada ítem).
  - `user_message(tr, *, feedback: list[dict] | None = None, items: dict | None = None) -> str` en `agents/base.py`: `transcript_text(tr)` del D2 (+ bloques `ÍTEMS A REVISAR` y `FEEDBACK DEL AUDITOR` si hay revisión).
  - `finalize.merge(current: list[dict], revised: list[dict], flagged_ids: set[str]) -> list[dict]`: reemplaza ítems con id en `flagged_ids`, conserva los demás, agrega los de id nuevo (o `'NEW'`).
  - `finalize.finalize(tr, decisions, tasks) -> dict` → `{'decisions', 'tasks'}` renumerados `d01..`/`t01..` en orden de aparición de `evidence_id`, `supersedes` remapeado (o `None` si no resuelve), luego `apply_safe_checks` del D2 (copiado a `finalize.py`); devuelve también `mechanical_actions`.
- Contenido mínimo de cada prompt (Eduardo lo revisa antes del commit):
  - `decisions.v1.md`: rol; definiciones de estados copiadas del `SYSTEM` del D2; procedimiento por tema (listar temas → recorrer cada uno en orden cronológico → asignar estado); cuándo pedir herramientas; formato de salida.
  - `tasks.v1.md`: rol; "toda tarea confirmada en la reunión tiene `state = final`"; responsable solo si es participante (usar `check_participant`); todo plazo no nulo debe provenir de `resolve_deadline`, si es ambiguo resolver con el contexto o dejar `null`; nunca inventar fecha.
  - `auditor.v1.md`: rol; checklist por ítem (¿la cita dice esto?, estado, plazo, responsable, ¿fusiona dos acciones?); usar `find_uncovered_commitments` para omisiones (`item_id = 'NEW'`, `problem = 'missing_item'`); `route = finish` si todos `ok`.
  - Few-shot: transcripción resumida de `TR01` + salida esperada derivada de su rúbrica.

- [ ] **Step 1: Escribir tests (fallan)**

```python
def test_fewshot_comes_from_train():
    for f in Path('prompts/fewshot').glob('*.md'):
        assert '.TR' in f.name and not re.search(r'\bM(0[1-9]|10)\b', f.read_text('utf-8'))

def test_no_prompt_strings_in_code():
    for py in Path('src/minutes_agents/agents').glob('*.py'):
        assert 'Eres ' not in py.read_text('utf-8')

def test_merge_keeps_unflagged():
    cur = [{'id': 'd01', 'x': 1}, {'id': 'd02', 'x': 2}]
    out = merge(cur, [{'id': 'd02', 'x': 9}, {'id': 'd03', 'x': 3}, {'id': 'd01', 'x': 7}], {'d02'})
    assert out == [{'id': 'd01', 'x': 1}, {'id': 'd02', 'x': 9}, {'id': 'd03', 'x': 3}]

def test_finalize_remaps_supersedes_and_drops_dangling(m01):
    ds = [{'id': 'a', 'evidence_id': 'u31', 'supersedes': 'b', 'state': 'final'},
          {'id': 'b', 'evidence_id': 'u05', 'supersedes': 'zz', 'state': 'superseded'}]
    out = finalize(m01, ds, [])['decisions']
    assert [d['id'] for d in out] == ['d01', 'd02'] and out[1]['supersedes'] == 'd01' and out[0]['supersedes'] is None

def test_auditor_output_has_route(m01):
    keys = auditor.build(RunConfig('full')).output(m01, {'items': []}, RunConfig('full'))
    assert keys['route']['enum'] == ['decisions', 'tasks', 'both', 'finish']
```

- [ ] **Step 2–4:** fallar → implementar módulos y redactar prompts → pasar.
- [ ] **Step 5: Explicar los prompts a Eduardo y esperar su visto bueno** antes del commit.
- [ ] **Step 6: Commit** — `git commit -m "feat(d3): add decision, task and auditor agents with versioned prompts and finalizer"`

---

### Task 8: Grafo LangGraph y ejecución por reunión

**Por qué:** materializa las aristas, el loop y las paradas que se dibujan en el PDF.

**Files:**
- Create: `deliverable3/src/minutes_agents/graph.py`
- Test: `deliverable3/tests/test_graph.py`

**Interfaces:**
- Consumes: Tasks 4–7.
- Produces:
  - `MeetingState` (TypedDict): `transcript, decisions, tasks, verdicts, route, audit_round, flagged, trace_events, calls`.
  - `audit_round` = número de revisiones ya hechas. `route_after_audit(state, cfg) -> str` → `'finalize'` si `route == 'finish'`; si no `'decisions'` (para `decisions`/`both`) o `'tasks'`, e incrementa `audit_round`. `route_after_revision(state, cfg) -> str` → tras revisar `decisions` con `route == 'both'` va a `tasks`; si no, `'finalize'` cuando `audit_round >= cfg.auditor_rounds`, o `'auditor'` en otro caso. (La última revisión no se vuelve a auditar: ahorra una llamada cuya ruta no podría ejecutarse; se declara.)
  - `build_graph(llm: LLM, tracer: Tracer, cfg: RunConfig)` → grafo compilado: `START → decisions → tasks → (auditor si cfg.auditor_rounds > 0, si no finalize)`; arista condicional desde `auditor`; `finalize → END`.
  - `run_meeting(tr: dict, llm: LLM, cfg: RunConfig, trace_path: Path | None) -> dict` → `{'parsed': {'decisions','tasks'}, 'raw': json.dumps(parsed), 'seconds', 'calls', 'eval_count', 'schema_valid', 'trace_path'}` (compatible con `evaluate_arm`).

- [ ] **Step 1: Escribir tests (fallan)** — con `FakeLLM` guionizado (respuestas `finish` directas):

```python
def test_full_route_with_one_revision(m01):
    # decisions, tasks, auditor(route=tasks, flags t01), tasks(revisión), auditor(route=finish)
    fake = FakeLLM([dec_finish, task_finish, audit_route('tasks', flag='t01'), task_revised, audit_route('finish')])
    out = run_meeting(m01, fake, RunConfig('full'), None)
    assert len(fake.calls) == 5 and out['calls'] == 5

def test_round_limit_forces_finalize(m01):
    fake = FakeLLM([dec_finish, task_finish] + [audit_route('tasks', flag='t01'), task_revised] * 2)
    run_meeting(m01, fake, RunConfig('full', auditor_rounds=2), None)
    assert len(fake.calls) == 6  # tras la 2.ª revisión va directo a finalize

def test_no_auditor(m01):
    fake = FakeLLM([dec_finish, task_finish])
    assert run_meeting(m01, fake, RunConfig('no_auditor', auditor_rounds=0), None)['calls'] == 2

def test_trace_written(m01, tmp_path):
    run_meeting(m01, FakeLLM([dec_finish, task_finish, audit_route('finish')]), RunConfig('full'), tmp_path / 'M01.jsonl')
    agents = [json.loads(l)['agent'] for l in (tmp_path / 'M01.jsonl').read_text('utf-8').splitlines()]
    assert agents[:3] == ['decisions', 'tasks', 'auditor'] and agents[-1] == 'finalize'
```
(`dec_finish`, `task_finish`, `audit_route`, `task_revised` son helpers en `tests/fakes.py`.)

- [ ] **Step 2–4:** fallar → implementar → pasar.
- [ ] **Step 5: Commit** — `git commit -m "feat(d3): wire agents into LangGraph with audit loop and stop conditions"`

---

### Task 9: Referencias D2 (baseline y combined_v2) con prompts en archivo

**Por qué:** las condiciones 1 y 2 deben correr con exactamente los mismos mensajes del D2, pero el enunciado exige prompts fuera del código.

**Files:**
- Create: `deliverable3/prompts/d2_system.v1.md`, `deliverable3/prompts/d2_review.v1.md`
- Create: `deliverable3/src/minutes_agents/d2_reference.py`
- Test: `deliverable3/tests/test_d2_reference.py`

**Interfaces:**
- Produces: `run_baseline(tr, llm) -> dict`; `run_d2_combined(tr, llm) -> dict` (borrador estructurado + `tool_bundle` + revisión + `apply_safe_checks`, como `run_one` del D2; devuelve el resultado de `combined_v2`, con `calls = 2`).

- [ ] **Step 1: Escribir tests (fallan)**

```python
def test_d2_prompts_identical_to_notebook(repo_root):
    nb = json.loads((repo_root / 'GenAI Constrained+Tool use/Ministral_Minutas_Colab.ipynb').read_text('utf-8'))
    code = ''.join(nb['cells'][4]['source'])
    system = re.search(r'SYSTEM = """(.*?)"""', code, re.S).group(1)
    assert load_prompt('d2_system.v1').text == system

def test_baseline_has_no_schema(m01):
    fake = FakeLLM(['{}']); run_baseline(m01, fake)
    assert fake.calls[0][1] is None
```

- [ ] **Step 2–4:** fallar → implementar (`d2_review.v1.md` = texto de la revisión de la celda 6, desde `'Revisa todas las intervenciones.'`) → pasar.
- [ ] **Step 5: Commit** — `git commit -m "feat(d3): add D2 baseline and combined_v2 references with prompts in files"`

---

### Task 10: Configuraciones y runner del experimento

**Files:**
- Create: `deliverable3/configs/full.json`, `no_react.json`, `no_auditor.json`, `no_fewshot.json`, `no_cot.json`
- Create: `deliverable3/src/minutes_agents/experiment.py`, `deliverable3/scripts/run_experiment.py`
- Test: `deliverable3/tests/test_experiment.py`

**Interfaces:**
- Produces:
  - `experiment.CONDITIONS = ['baseline', 'd2', 'full', 'no_react', 'no_auditor', 'no_fewshot', 'no_cot']`.
  - `experiment.load_config(name) -> RunConfig` desde `configs/<name>.json`.
  - `experiment.run_experiment(conditions: list[str], transcripts, gold, llm: LLM, out_dir: Path, trace_dir: Path) -> dict`: escribe `out_dir/<cond>/<mid>.json`, `trace_dir/<cond>/<mid>.jsonl` y `out_dir/summary.json` = `{cond: {'primary': evaluate_arm(...), 'extended': extended_metrics(...)}, 'paired_full_vs_d2': {...}, 'meta': {model, params, ollama_version, prompts: {nombre: sha256}}}`; se salta reuniones ya escritas (reanudar).
  - CLI: `python scripts/run_experiment.py --data <dir> --split {validation,test} --conditions full,d2 --out results/<split> --traces traces --host http://127.0.0.1:11434 [--demo]` (`--demo` = solo la primera reunión ordenada).

- [ ] **Step 1: Test (falla)** — `run_experiment(['full', 'no_auditor'], {M01}, ..., FakeLLM(...), tmp_path, tmp_path/'tr')` produce `summary.json` con ambas condiciones, `primary.decisions.f1` numérico, y una segunda llamada no consume respuestas del fake.
- [ ] **Step 2–4:** fallar → implementar → pasar.
- [ ] **Step 5: Commit** — `git commit -m "feat(d3): add ablation configs and experiment runner"`

---

### Task 11: Figuras

**Files:**
- Create: `deliverable3/scripts/make_figures.py`
- Test: `deliverable3/tests/test_figures.py`

**Interfaces:**
- Produces: `make_figures(summary_path: Path, out_dir: Path) -> list[Path]` → `f1_by_condition.pdf` (barras agrupadas: F1 decisiones, F1 tareas, F1 estricto) y `trap_heatmap.pdf` (condición × categoría de `per_trap`, valor `found/gold`). Orden de condiciones = `CONDITIONS`. Usar la skill `dataviz` al implementar (paleta y legibilidad en una página).

- [ ] **Step 1: Test (falla)** — con un `summary.json` sintético de 2 condiciones, se generan ambos archivos no vacíos.
- [ ] **Step 2–4:** fallar → implementar → pasar.
- [ ] **Step 5: Commit** — `git commit -m "feat(d3): add result figures"`

---

### Task 12: Notebook de Colab y prueba de humo en validation (manual, Colab T4)

**Por qué:** primer contacto con el modelo real; aquí se descubre si Ministral sigue el protocolo ReAct.

**Files:**
- Create: `deliverable3/notebooks/D3_Colab.ipynb`

Celdas: (1) GPU + Ollama + `ollama pull` (de la celda 1 del D2) + `ollama --version`; (2) `git clone` del repo y `git checkout <COMMIT>` (variable al inicio); (3) `pip install -r deliverable3/requirements.txt`; (4) subir/extraer `Fine Tuning.zip`; (5) `MODE = 'DEMO' | 'VALIDATION' | 'FULL'`; (6) correr `run_experiment.py`; (7) imprimir la traza de M01 agente por agente; (8) figuras; (9) zip y descarga de `results/` y `traces/`.

- [ ] **Step 1:** Ensamblar el notebook y hacer commit local; como el repo no se publica todavía, para Colab se sube un zip de `deliverable3/` (celda alternativa a `git clone`).
- [ ] **Step 2 (Eduardo en Colab):** `MODE='VALIDATION'`, condición `full` sobre `VA01`–`VA02`. Expected: corre sin excepción, trazas con `call_tools` y `finish`, `schema_valid` en todas las llamadas.
- [ ] **Step 3:** Revisar juntos las trazas descargadas; anotar problemas.
- [ ] **Step 4: Commit** — `git commit -m "feat(d3): add Colab notebook"`

---

### Task 13: Ajuste de prompts en validation (iterativo, manual)

- [ ] **Step 1 (Colab):** `full` y `d2` sobre las 10 de validation.
- [ ] **Step 2:** Analizar `per_trap` y trazas; proponer cambios a prompts/límites, explicarlos a Eduardo.
- [ ] **Step 3:** Cada cambio aprobado = nueva versión de archivo (`decisions.v2.md`…) + entrada en `prompts/CHANGELOG.md` con motivo y métrica de validation.
- [ ] **Step 4:** Repetir hasta que `full` supere a `d2` en validation o se acabe el tiempo (límite: 2026-10-28). Nota: validation parece más homogénea que test (todas con 2 superseded, 1 rejected, 1 pending); se declara como limitación.
- [ ] **Step 5: Commit** por versión — `git commit -m "tune(d3): prompts vN on validation"`

---

### Task 14: Corrida final en test y selección de trazas (manual, Colab T4)

- [ ] **Step 1:** Congelar: commit local con prompts finales; anotar hash en el notebook.
- [ ] **Step 2 (Colab, sesión nueva):** `MODE='FULL'`, las 7 condiciones, test M01–M10. Descargar `results/` y `traces/`.
- [ ] **Step 3:** `python scripts/make_figures.py --summary results/test/summary.json --out results/test/figures`.
- [ ] **Step 4:** Caso de falla = reunión con menor `extended.per_meeting[mid].strict_f1` en `full`. Copiar al repo `traces/full/M01.jsonl` (video) y la del caso de falla; el resto queda en el zip de resultados.
- [ ] **Step 5: Commit** — `git commit -m "results(d3): final test run, figures and selected traces"`

---

### Task 15: README, PDF de una página y guion del video

**Files:**
- Modify: `README.md` (sección Entregable 3 al inicio; resto intacto)
- Create: `deliverable3/README.md`, `deliverable3/VIDEO_D3.md`
- Create: `deliverable3/paper/Deliverable_3.tex`, `deliverable3/paper/agent_graph.tex` (TikZ), `deliverable3/scripts/build_paper.ps1`

- [ ] **Step 1:** `README` en español: qué es, grafo (mermaid), cómo reproducir (Colab DEMO/FULL, local con Ollama, `pytest`), dónde están prompts, trazas y resultados.
- [ ] **Step 2:** PDF en inglés, una página, en el orden del spec §5 (problemática → dificultad → grafo → agentes y técnicas → resultados y ablaciones → falla → limitaciones/reproducción). Números leídos de `summary.json`.
- [ ] **Step 3:** `build_paper.ps1` compila y falla si el PDF no tiene exactamente 1 página (como `scripts/build_deliverable2.ps1`). Run: `powershell -File deliverable3/scripts/build_paper.ps1` → Expected: "1 page".
- [ ] **Step 4:** Guion del video ≤ 3 min en `VIDEO_D3.md` (Colab DEMO M01 con trazas visibles → acta final → figuras).
- [ ] **Step 5: Commit** — `git commit -m "docs(d3): README, one-page paper and video script"`
- [ ] **Step 6:** Preguntar a Eduardo si autoriza `git push` y PR. No antes.
