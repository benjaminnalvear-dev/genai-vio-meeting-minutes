from jsonschema import Draft202012Validator
from minutes_agents.schemas import (step_schema, verdict_schema, make_schema,
                                    decision_item_schema, task_item_schema)

OUT = {'decisions': {'type': 'array'}}


def test_last_step_only_finish(m01):
    s = step_schema(m01, ['inspect_evidence'], OUT, allow_tools=False, with_thought=True)
    assert s['properties']['action']['enum'] == ['finish']
    assert s['properties']['tool_calls']['maxItems'] == 0


def test_no_cot_removes_thought(m01):
    s = step_schema(m01, ['inspect_evidence'], OUT, allow_tools=True, with_thought=False)
    assert 'thought' not in s['properties'] and 'thought' not in s['required']


def test_tool_and_evidence_enums(m01):
    s = step_schema(m01, ['inspect_evidence'], OUT, allow_tools=True, with_thought=True)
    call = s['properties']['tool_calls']['items']['properties']
    assert call['tool']['enum'] == ['inspect_evidence']
    assert 'u42' in call['evidence_id']['enum'] and 'u99' not in call['evidence_id']['enum']
    v = Draft202012Validator(s)
    ok = {'thought': 't', 'action': 'call_tools',
          'tool_calls': [{'tool': 'inspect_evidence', 'evidence_id': 'u05', 'name': None}], 'decisions': []}
    assert v.is_valid(ok)
    ok['tool_calls'][0]['evidence_id'] = None
    assert v.is_valid(ok)
    ok['tool_calls'][0]['evidence_id'] = 'u99'
    assert not v.is_valid(ok)


def test_item_schemas_match_make_schema(m01):
    full = make_schema(m01)
    assert decision_item_schema(m01) == full['properties']['decisions']['items']
    assert task_item_schema(m01) == full['properties']['tasks']['items']


def test_verdict_schema():
    s = verdict_schema(['d1', 't1'])
    p = s['properties']
    assert p['item_id']['enum'] == ['d1', 't1', 'NEW']
    assert None in p['problem']['enum'] and 'wrong_state' in p['problem']['enum']
    v = Draft202012Validator(s)
    assert v.is_valid({'item_id': 'NEW', 'ok': False, 'problem': 'missing_item', 'detail': 'x'})
    assert v.is_valid({'item_id': 'd1', 'ok': True, 'problem': None, 'detail': ''})
    assert not v.is_valid({'item_id': 'zz', 'ok': True, 'problem': None, 'detail': ''})


def test_tool_calls_max_items_when_tools_allowed(m01):
    s = step_schema(m01, ['inspect_evidence'], OUT, allow_tools=True, with_thought=True)
    assert s['properties']['tool_calls']['maxItems'] == 8
    call = {'tool': 'inspect_evidence', 'evidence_id': 'u05', 'name': None}
    v = Draft202012Validator(s)
    base = {'thought': 't', 'action': 'call_tools', 'decisions': []}
    assert v.is_valid({**base, 'tool_calls': [call] * 8})
    assert not v.is_valid({**base, 'tool_calls': [call] * 9})
