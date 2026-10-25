import hashlib
import json

import pytest

from fakes import FakeLLM
from minutes_agents.llm import CachedLLM
from minutes_agents.prompts import load_prompt
from minutes_agents.tracing import Tracer


def test_cached_llm_reuses_responses(tmp_path):
    fake = FakeLLM([{'a': 1}])
    c = CachedLLM(fake, tmp_path)
    msgs = [{'role': 'user', 'content': 'x'}]
    assert c.chat(msgs, None)['parsed'] == {'a': 1}
    assert c.calls_made == 1
    assert c.chat(msgs, None)['parsed'] == {'a': 1}
    assert c.calls_made == 1
    c2 = CachedLLM(FakeLLM([]), tmp_path)
    assert c2.chat(msgs, None)['parsed'] == {'a': 1}
    assert c2.calls_made == 0


def test_prompt_hash(tmp_path):
    (tmp_path / 'x.v1.md').write_text('hola', encoding='utf-8')
    p = load_prompt('x.v1', tmp_path)
    assert p.sha256 == hashlib.sha256('hola'.encode()).hexdigest()
    assert p.text == 'hola' and p.name == 'x.v1'


def test_prompt_subdir_utf8(tmp_path):
    (tmp_path / 'fewshot').mkdir()
    (tmp_path / 'fewshot' / 'd.TR01.md').write_text('acción', encoding='utf-8')
    assert load_prompt('fewshot/d.TR01', tmp_path).text == 'acción'


def test_tracer_writes_jsonl(tmp_path):
    t = Tracer(tmp_path / 'sub' / 't.jsonl')
    t.log('decisions', 1, action='finish', note='acción')
    line = json.loads((tmp_path / 'sub' / 't.jsonl').read_text('utf-8').splitlines()[0])
    assert (line['agent'], line['step'], line['action']) == ('decisions', 1, 'finish') and 'ts' in line
    assert line['note'] == 'acción' and t.events[0] == line


def test_tracer_memory_only():
    t = Tracer(None)
    t.log('a', 0, x=1)
    assert t.events[0]['x'] == 1


def test_fake_llm_shape_and_exhaustion():
    schema = {'type': 'object', 'required': ['a'], 'properties': {'a': {'type': 'integer'}}}
    f = FakeLLM([{'a': 1}, 'no json'])
    r = f.chat([{'role': 'user', 'content': 'q'}], schema)
    assert r['parsed'] == {'a': 1} and r['schema_valid'] is True and r['seconds'] == 0.0
    r = f.chat([], schema)
    assert r['raw'] == 'no json' and r['parsed'] is None and r['schema_valid'] is False
    assert len(f.calls) == 2
    with pytest.raises(AssertionError):
        f.chat([], None)
