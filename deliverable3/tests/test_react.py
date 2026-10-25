from pathlib import Path

import pytest

from fakes import FakeLLM
from minutes_agents.agents.base import AgentSpec, RunConfig, run_react
from minutes_agents.prompts import Prompt
from minutes_agents.tracing import Tracer


@pytest.fixture
def toy_spec():
    prompt = Prompt(name='toy', text='SISTEMA', path=Path('prompts/toy.md'), sha256='abc')
    return AgentSpec(
        name='toy', prompt=prompt, fewshot=None, tools=['inspect_evidence'],
        output=lambda tr, ctx, cfg: {'decisions': {'type': 'array', 'items': {'type': 'object'}}},
        precompute=lambda tr, ctx: [])


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
    tr = Tracer(None)
    out = run_react(toy_spec, m01, 'x', FakeLLM(['no es json']), tr, RunConfig('full'), {'items': []})
    assert out['output'] == {'decisions': []}
    assert tr.events[0]['error'] == 'invalid_json'


def test_no_react_single_step_with_reports(m01, toy_spec):
    fake = FakeLLM([{'thought': '', 'action': 'finish', 'tool_calls': [], 'decisions': []}])
    run_react(toy_spec, m01, 'x', fake, Tracer(None), RunConfig('no_react', react=False), {'items': []})
    assert len(fake.calls) == 1 and 'INFORMES DE HERRAMIENTAS' in fake.calls[0][0][-1]['content']


def test_unknown_tool_yields_error_observation(m01, toy_spec):
    fake = FakeLLM([{'thought': '', 'action': 'call_tools', 'tool_calls': [{'tool': 'inspect_evidence', 'evidence_id': 'u05', 'name': None}], 'decisions': []},
                    {'thought': '', 'action': 'finish', 'tool_calls': [], 'decisions': []}])
    import minutes_agents.agents.base as base
    orig = base.TOOLS
    base.TOOLS = {}
    try:
        tr = Tracer(None)
        run_react(toy_spec, m01, 'x', fake, tr, RunConfig('full'), {'items': []})
    finally:
        base.TOOLS = orig
    assert tr.events[0]['observations'] == [{'tool': 'inspect_evidence', 'error': 'unknown tool'}]
