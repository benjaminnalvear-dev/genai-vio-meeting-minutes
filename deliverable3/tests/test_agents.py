import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from minutes_agents.agents import auditor, decisions, tasks
from minutes_agents.agents.base import RunConfig, user_message
from minutes_agents.schemas import step_schema

PROMPTS = Path(__file__).resolve().parents[1] / 'prompts'
AGENTS_SRC = Path(__file__).resolve().parents[1] / 'src' / 'minutes_agents' / 'agents'


def test_fewshot_comes_from_train():
    files = list((PROMPTS / 'fewshot').glob('*.md'))
    assert files
    for f in files:
        assert '.TR' in f.name and not re.search(r'\bM(0[1-9]|10)\b', f.read_text('utf-8'))


def test_prompts_never_mention_test_meetings():
    for f in PROMPTS.rglob('*.md'):
        assert not re.search(r'\bM(0[1-9]|10)\b', f.read_text('utf-8')), f.name


def test_no_prompt_strings_in_code():
    for py in AGENTS_SRC.glob('*.py'):
        assert 'Eres ' not in py.read_text('utf-8')


def test_auditor_output_has_route(m01):
    keys = auditor.build(RunConfig('full')).output(m01, {'items': []}, RunConfig('full'))
    assert keys['route']['enum'] == ['decisions', 'tasks', 'both', 'finish']


def test_specs_tools_and_prompts():
    cfg = RunConfig('full')
    d, t, a = decisions.build(cfg), tasks.build(cfg), auditor.build(cfg)
    assert d.tools == ['find_revision_cues', 'inspect_evidence']
    assert t.tools == ['resolve_deadline', 'check_participant', 'inspect_evidence']
    assert a.tools == ['inspect_evidence', 'find_uncovered_commitments', 'find_revision_cues']
    assert d.prompt.name == 'decisions.v1' and d.fewshot.name == 'fewshot/decisions.TR01'
    assert t.prompt.name == 'tasks.v1' and t.fewshot.name == 'fewshot/tasks.TR01'
    assert a.prompt.name == 'auditor.v1' and a.fewshot is None


def test_topic_plan_only_with_cot(m01):
    assert 'topic_plan' in decisions.build(RunConfig('full')).output(m01, {}, RunConfig('full'))
    no_cot = RunConfig('no_cot', cot=False)
    assert set(decisions.build(no_cot).output(m01, {}, no_cot)) == {'decisions'}


def _decision(eid='u05'):
    return {'id': 'd01', 'topic': 'T', 'statement': 's', 'state': 'final',
            'condition': None, 'supersedes': None, 'evidence_id': eid}


def _task(eid='u05'):
    return {'id': 't01', 'description': 'x', 'assignee': None, 'deadline': None,
            'condition': None, 'state': 'final', 'evidence_id': eid}


@pytest.mark.parametrize('cot', [True, False])
def test_built_specs_validate_minimal_finish(m01, cot):
    cfg = RunConfig('c', cot=cot)
    items = [_decision(), _task()]
    cases = [
        (decisions.build(cfg), {}, {'decisions': [_decision()],
                                    **({'topic_plan': [{'topic': 'T', 'evidence_ids': ['u05']}]} if cot else {})}),
        (tasks.build(cfg), {}, {'tasks': [_task()]}),
        (auditor.build(cfg), {'items': items},
         {'verdicts': [{'item_id': 'd01', 'ok': True, 'problem': None, 'detail': ''},
                       {'item_id': 'NEW', 'ok': False, 'problem': 'missing_item', 'detail': 'u07'}],
          'route': 'tasks'}),
    ]
    for spec, ctx, out in cases:
        schema = step_schema(m01, spec.tools, spec.output(m01, ctx, cfg), allow_tools=False, with_thought=cot)
        obj = {'action': 'finish', 'tool_calls': [], **out}
        if cot:
            obj['thought'] = 'ok'
        assert Draft202012Validator(schema).is_valid(obj), spec.name
    bad = step_schema(m01, [], auditor.build(cfg).output(m01, {'items': items}, cfg),
                      allow_tools=False, with_thought=cot)
    wrong = {'action': 'finish', 'tool_calls': [], 'route': 'finish',
             'verdicts': [{'item_id': 'd99', 'ok': True, 'problem': None, 'detail': ''}],
             **({'thought': ''} if cot else {})}
    assert not Draft202012Validator(bad).is_valid(wrong)


def test_precompute_reports(m01):
    d = decisions.build(RunConfig('x')).precompute(m01, {})
    assert d[0]['tool'] == 'find_revision_cues'
    assert {r['tool'] for r in d[1:]} == {'inspect_evidence'} and len(d) == len(d[0]['result']) + 1
    t = tasks.build(RunConfig('x')).precompute(m01, {})
    assert all(r['result']['suggested'] for r in t if r['tool'] == 'resolve_deadline')
    assert {r['result']['name'] for r in t if r['tool'] == 'check_participant'} == set(m01['participants'])
    a = auditor.build(RunConfig('x')).precompute(m01, {'items': [_decision('u05'), _task('u12')]})
    assert a[0]['tool'] == 'find_uncovered_commitments'
    assert [r['result']['evidence_id'] for r in a[1:]] == ['u05', 'u12']


def test_user_message_plain_and_revision(m01):
    plain = user_message(m01)
    assert 'INTERVENCIONES EN ORDEN:' in plain and 'ÍTEMS A REVISAR' not in plain
    rev = user_message(m01, feedback=[{'item_id': 'd01', 'ok': False, 'problem': 'wrong_state', 'detail': 'á'}],
                       items={'decisions': [_decision()]})
    assert rev.startswith(plain)
    assert 'ÍTEMS A REVISAR:' in rev and 'FEEDBACK DEL AUDITOR:' in rev and 'wrong_state' in rev and 'á' in rev
