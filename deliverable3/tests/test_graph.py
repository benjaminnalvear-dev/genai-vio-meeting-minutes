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
    fake = FakeLLM([dec_finish, task_finish, audit_route('both', flag='d01'), dec_revised,
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
