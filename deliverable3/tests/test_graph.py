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
    fake = FakeLLM([dec_finish, task_finish, audit_route('decisions', flag='t01'), audit_route('finish')])
    out = run_meeting(m01, fake, RunConfig('full'), tmp_path / 'M01.jsonl')
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
