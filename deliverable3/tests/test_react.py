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


def _call(eid='u05'):
    return {'tool': 'inspect_evidence', 'evidence_id': eid, 'name': None}


def test_duplicate_tool_calls_reuse_observation(m01, toy_spec, monkeypatch):
    import minutes_agents.agents.base as base
    n = {'calls': 0}
    real = base.TOOLS['inspect_evidence']

    def counting(tr, call, ctx):
        n['calls'] += 1
        return real(tr, call, ctx)
    monkeypatch.setitem(base.TOOLS, 'inspect_evidence', counting)
    fake = FakeLLM([{'thought': '', 'action': 'call_tools', 'tool_calls': [_call(), _call()], 'decisions': []},
                    {'thought': '', 'action': 'call_tools', 'tool_calls': [_call(), _call('u06')], 'decisions': []},
                    {'thought': '', 'action': 'finish', 'tool_calls': [], 'decisions': []}])
    tr = Tracer(None)
    run_react(toy_spec, m01, 'x', fake, tr, RunConfig('full'), {'items': []})
    assert n['calls'] == 2  # u05 once, u06 once
    obs1, obs2 = tr.events[0]['observations'], tr.events[1]['observations']
    assert 'duplicate' not in obs1[0] and obs1[1]['duplicate'] is True
    assert obs1[1]['cited'] == obs1[0]['cited']
    assert obs2[0]['duplicate'] is True and 'duplicate' not in obs2[1]


def test_trace_logs_prompt_tokens_done_reason_and_context_warning(m01, toy_spec):
    from minutes_agents.agents.base import CONTEXT_WARNING_TOKENS, estimate_tokens
    assert estimate_tokens([{'role': 'user', 'content': 'a' * 30}]) == 10
    tr = Tracer(None)

    class _LLM(FakeLLM):
        def chat(self, messages, schema=None):
            r = super().chat(messages, schema)
            r['prompt_eval_count'] = 1234
            return r
    run_react(toy_spec, m01, 'x', _LLM([{'thought': '', 'action': 'finish', 'tool_calls': [], 'decisions': []}]),
              tr, RunConfig('full'), {'items': []})
    ev = tr.events[0]
    assert ev['prompt_tokens'] == 1234 and ev['done_reason'] == 'stop' and ev['context_warning'] is False
    big = 'x' * int(3 * (CONTEXT_WARNING_TOKENS + 10))
    tr2 = Tracer(None)
    run_react(toy_spec, m01, big, FakeLLM(['no es json']), tr2, RunConfig('full'), {'items': []})
    assert tr2.events[0]['context_warning'] is True and tr2.events[0]['prompt_tokens'] == 0


def test_tool_exception_becomes_error_observation(m01, toy_spec, monkeypatch):
    import minutes_agents.agents.base as base

    def boom(tr, call, ctx):
        raise KeyError('x')
    monkeypatch.setitem(base.TOOLS, 'inspect_evidence', boom)
    fake = FakeLLM([{'thought': '', 'action': 'call_tools', 'tool_calls': [_call()], 'decisions': []},
                    {'thought': '', 'action': 'finish', 'tool_calls': [], 'decisions': []}])
    tr = Tracer(None)
    run_react(toy_spec, m01, 'x', fake, tr, RunConfig('full'), {'items': []})
    assert tr.events[0]['observations'] == [{'tool': 'inspect_evidence', 'error': "KeyError('x')"}]
