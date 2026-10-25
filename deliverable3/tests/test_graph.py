import json

from jsonschema import Draft202012Validator

from minutes_agents.agents.base import RunConfig
from minutes_agents.graph import run_meeting
from minutes_agents.schemas import make_schema
from tests.fakes import (FakeLLM, audit_route, dec_finish, dec_revised, task_finish,
                         task_revised)


def test_full_route_with_one_revision(m01):
    fake = FakeLLM([dec_finish, task_finish, audit_route('tasks', flag='t01'), task_revised,
                    audit_route('finish')])
    out = run_meeting(m01, fake, RunConfig('full'), None)
    assert len(fake.calls) == 5 and out['calls'] == 5
    assert out['parsed']['tasks'][0]['description'] == 'Enviar el informe final'
    assert out['schema_valid'] is True and json.loads(out['raw']) == out['parsed']


def test_round_limit_forces_finalize(m01):
    fake = FakeLLM([dec_finish, task_finish] + [audit_route('tasks', flag='t01'), task_revised] * 2)
    run_meeting(m01, fake, RunConfig('full', auditor_rounds=2), None)
    assert len(fake.calls) == 6  # tras la 2.ª revisión va directo a finalize


def test_no_auditor(m01):
    fake = FakeLLM([dec_finish, task_finish])
    assert run_meeting(m01, fake, RunConfig('no_auditor', auditor_rounds=0), None)['calls'] == 2


def test_trace_written(m01, tmp_path):
    run_meeting(m01, FakeLLM([dec_finish, task_finish, audit_route('finish')]), RunConfig('full'),
                tmp_path / 'M01.jsonl')
    agents = [json.loads(l)['agent'] for l in (tmp_path / 'M01.jsonl').read_text('utf-8').splitlines()]
    assert agents[:3] == ['decisions', 'tasks', 'auditor'] and agents[-1] == 'finalize'
    assert 'router' in agents


def test_route_both_visits_decisions_then_tasks(m01, tmp_path):
    fake = FakeLLM([dec_finish, task_finish, audit_route('both', flag=['d01', 't01']), dec_revised,
                    task_revised, audit_route('finish')])
    out = run_meeting(m01, fake, RunConfig('full'), tmp_path / 'M01.jsonl')
    events = [json.loads(l) for l in (tmp_path / 'M01.jsonl').read_text('utf-8').splitlines()]
    agents = [e['agent'] for e in events]
    assert agents == ['decisions', 'tasks', 'auditor', 'router', 'decisions', 'tasks', 'auditor',
                      'router', 'finalize']
    assert out['calls'] == 6
    assert out['parsed']['decisions'][0]['statement'].endswith('(revisado)')
    assert events[-1]['mechanical_actions'] == [] and events[-1]['decisions'] == 1


def test_invalid_auditor_output_finalizes(m01):
    fake = FakeLLM([dec_finish, task_finish, 'no es json'])
    out = run_meeting(m01, fake, RunConfig('full'), None)
    assert out['calls'] == 3 and len(out['parsed']['decisions']) == 1
    assert Draft202012Validator(make_schema(m01)).is_valid(out['parsed'])


def test_seconds_sum_trace_events_and_survive_cache(m01, tmp_path):
    from minutes_agents.llm import CachedLLM

    class _Timed(FakeLLM):
        def chat(self, messages, schema=None):
            r = super().chat(messages, schema)
            r['seconds'] = 1.25
            return r
    script = [dec_finish, task_finish, audit_route('finish')]
    inner = _Timed(list(script))
    first = run_meeting(m01, CachedLLM(inner, tmp_path / 'c'), RunConfig('full'), None)
    assert first['seconds'] == 3.75 and 'wall_seconds' in first
    again = run_meeting(m01, CachedLLM(FakeLLM([]), tmp_path / 'c'), RunConfig('full'), None)
    assert again['seconds'] == first['seconds']  # aciertos de caché conservan su tiempo original


def test_invalid_steps_and_tool_calls_counted(m01):
    call = {'tool': 'inspect_evidence', 'evidence_id': 'u05', 'name': None}
    dec_tools = dict(dec_finish, action='call_tools', tool_calls=[call, call, dict(call, evidence_id='u06')])
    fake = FakeLLM([dec_tools, dec_finish, task_finish, 'no es json'])
    out = run_meeting(m01, fake, RunConfig('full'), None)
    assert out['invalid_steps'] == 1 and out['tool_calls'] == 2


def test_duplicate_ids_from_specialist_survive_audit_round(m01):
    from tests.fakes import _decision
    second = dict(_decision('Se posterga la compra'), evidence_id='u06')  # mismo id 'd01'
    dec_dup = dict(dec_finish, decisions=[_decision(), second])
    fake = FakeLLM([dec_dup, task_finish, audit_route('decisions', flag='d01'), dec_revised,
                    audit_route('finish')])
    out = run_meeting(m01, fake, RunConfig('full'), None)
    statements = [d['statement'] for d in out['parsed']['decisions']]
    assert statements == ['Se adopta el plan acordado (revisado)', 'Se posterga la compra']
    assert [d['id'] for d in out['parsed']['decisions']] == ['d01', 'd02']
    audit_items = fake.calls[2][0][1]['content']
    assert '"id": "d02"' in audit_items  # el Auditor ya ve ids únicos


def test_revision_skipped_when_no_verdicts_for_specialist(m01, tmp_path):
    # Sin barandas: con ellas la ruta se recalcula y este veredicto iría a Tareas.
    fake = FakeLLM([dec_finish, task_finish, audit_route('decisions', flag='t01'), audit_route('finish')])
    out = run_meeting(m01, fake, RunConfig('full', audit_guards=False), tmp_path / 'M01.jsonl')
    assert len(fake.calls) == 4 and out['calls'] == 4  # no se llamó al agente Decisiones
    events = [json.loads(l) for l in (tmp_path / 'M01.jsonl').read_text('utf-8').splitlines()]
    assert [e['agent'] for e in events] == ['decisions', 'tasks', 'auditor', 'router', 'router',
                                            'auditor', 'router', 'finalize']
    assert events[4]['skipped'] == 'decisions' and events[4]['route'] == 'decisions'


def test_normalize_ids_remaps_supersedes():
    from minutes_agents.graph import normalize_ids
    items = [{'id': 'd03', 'supersedes': None}, {'id': 'd03', 'supersedes': None},
             {'id': 'd07', 'supersedes': 'd03'}, {'id': 'x', 'supersedes': 'zz'}]
    out, actions = normalize_ids(items, 'decisions')
    assert [i['id'] for i in out] == ['d01', 'd02', 'd03', 'd04']
    assert out[2]['supersedes'] == 'd01' and out[3]['supersedes'] is None
    assert actions == ['supersedes sin resolver a null'] and items[0]['id'] == 'd03'  # sin mutar la entrada


# --- Barandas determinísticas del Auditor (guards.py) ---
def _events(path):
    return [json.loads(l) for l in path.read_text('utf-8').splitlines()]


def test_guards_drop_false_verdicts_and_skip_revision(m01, tmp_path):
    # t01 es tarea confirmada (G4) y el NEW no cita ningún turno (G1): ambos se descartan.
    audit = audit_route('tasks', flag=['t01'], problem='wrong_state')
    audit['verdicts'].append({'item_id': 'NEW', 'ok': False, 'problem': 'missing_item',
                              'detail': 'falta una tarea'})
    fake = FakeLLM([dec_finish, task_finish, audit])
    out = run_meeting(m01, fake, RunConfig('full'), tmp_path / 'M01.jsonl')
    assert len(fake.calls) == 3 and out['calls'] == 3  # sin revisión
    events = _events(tmp_path / 'M01.jsonl')
    guards = [e for e in events if e['agent'] == 'guard']
    assert [(g['item_id'], g['problem'], g['guard']) for g in guards] == [
        ('t01', 'wrong_state', 'G4'), ('NEW', 'missing_item', 'G1')]
    assert all(g['step'] == 0 and g['reason'] for g in guards)
    router = next(e for e in events if e['agent'] == 'router')
    assert router['route'] == 'finish' and router['auditor_route'] == 'tasks'
    assert router['flagged'] == [] and router['next'] == 'finalize'


def test_guards_off_keeps_auditor_route(m01, tmp_path):
    audit = audit_route('tasks', flag=['t01'], problem='wrong_state')
    fake = FakeLLM([dec_finish, task_finish, audit, task_revised, audit_route('finish')])
    out = run_meeting(m01, fake, RunConfig('no_guards', audit_guards=False), tmp_path / 'M01.jsonl')
    assert len(fake.calls) == 5 and out['calls'] == 5  # la revisión ocurre
    events = _events(tmp_path / 'M01.jsonl')
    assert not any(e['agent'] == 'guard' for e in events)
    assert 'auditor_route' not in next(e for e in events if e['agent'] == 'router')


def test_guards_recompute_route_and_send_new_by_kind_hint(m01, tmp_path):
    # El Auditor dice 'decisions', pero el NEW cita u19 (compromiso sin cubrir): va a Tareas.
    audit = audit_route('decisions', flag=['NEW'], problem='missing_item',
                        detail='u19: Speaker 04 queda a cargo de la demostración técnica')
    new_task = {'id': 'NEW', 'description': 'Presentar la demostración técnica', 'assignee': 'Speaker 04',
                'deadline': None, 'condition': None, 'state': 'final', 'evidence_id': 'u19'}
    task_new = dict(task_finish, tasks=[new_task])
    fake = FakeLLM([dec_finish, task_finish, audit, task_new, audit_route('finish')])
    out = run_meeting(m01, fake, RunConfig('full'), tmp_path / 'M01.jsonl')
    assert len(fake.calls) == 5
    assert [t['evidence_id'] for t in out['parsed']['tasks']] == ['u08', 'u19']
    feedback = fake.calls[3][0][1]['content'].split('FEEDBACK DEL AUDITOR:')[1]
    assert 'u19' in feedback and 'kind_hint' not in feedback
    router = [e for e in _events(tmp_path / 'M01.jsonl') if e['agent'] == 'router'][0]
    assert router['route'] == 'tasks' and router['auditor_route'] == 'decisions'


def test_g7_drops_new_item_duplicating_existing_evidence(m01, tmp_path):
    audit = audit_route('tasks', flag=['t01'])
    dup = {'id': 'NEW', 'description': 'Enviar el borrador', 'assignee': 'Speaker 02', 'deadline': None,
           'condition': None, 'state': 'final', 'evidence_id': 'u08'}
    revised = dict(task_revised, tasks=task_revised['tasks'] + [dup])
    fake = FakeLLM([dec_finish, task_finish, audit, revised, audit_route('finish')])
    out = run_meeting(m01, fake, RunConfig('full'), tmp_path / 'M01.jsonl')
    assert [t['description'] for t in out['parsed']['tasks']] == ['Enviar el informe final']
    g7 = [e for e in _events(tmp_path / 'M01.jsonl') if e['agent'] == 'guard']
    assert len(g7) == 1 and g7[0]['guard'] == 'G7' and g7[0]['item_id'] == 't02'


def test_g7_keeps_split_of_merged_item_but_drops_duplicate(m01, tmp_path):
    from tests.fakes import _task
    t2 = dict(_task('Entregar la versión estable'), id='t02', evidence_id='u33')
    tasks0 = dict(task_finish, tasks=[_task(), t2])
    audit = audit_route('tasks', flag=['t01'], problem='merged_items', detail='u08 junta dos acciones')
    split = [dict(_task('Preparar el borrador')), dict(_task('Enviar el borrador para revisión'))]
    dup = dict(_task('Entregar la versión'), id='NEW', evidence_id='u33')
    revised = dict(task_revised, tasks=split + [dup])
    fake = FakeLLM([dec_finish, tasks0, audit, revised, audit_route('finish')])
    out = run_meeting(m01, fake, RunConfig('full'), tmp_path / 'M01.jsonl')
    assert [t['description'] for t in out['parsed']['tasks']] == [
        'Preparar el borrador', 'Enviar el borrador para revisión', 'Entregar la versión estable']
    g7 = [e for e in _events(tmp_path / 'M01.jsonl') if e['agent'] == 'guard']
    assert [(e['guard'], e['item_id']) for e in g7] == [('G7', 't03')]  # merge numera primero los NEW, luego las divisiones


def test_router_event_records_auditor_and_recomputed_route(m01, tmp_path):
    # El Auditor dice 'finish' pero deja un veredicto válido: la ruta recalculada manda a Tareas.
    fake = FakeLLM([dec_finish, task_finish, audit_route('finish', flag='t01'), task_revised,
                    audit_route('finish')])
    run_meeting(m01, fake, RunConfig('full'), tmp_path / 'M01.jsonl')
    router = [e for e in _events(tmp_path / 'M01.jsonl') if e['agent'] == 'router'][0]
    assert router['auditor_route'] == 'finish' and router['route'] == 'tasks'
    assert router['next'] == 'revise_tasks' and len(fake.calls) == 5
