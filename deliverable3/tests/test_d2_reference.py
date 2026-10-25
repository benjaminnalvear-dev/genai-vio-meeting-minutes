import json
import re

B = chr(92)

from fakes import FakeLLM
from minutes_agents.d2_reference import run_baseline, run_d2_combined
from minutes_agents.prompts import load_prompt


def test_d2_prompts_identical_to_notebook(repo_root):
    nb = json.loads((repo_root / 'GenAI Constrained+Tool use/Ministral_Minutas_Colab.ipynb').read_text('utf-8'))
    code = ''.join(nb['cells'][4]['source'])
    system = re.search(r'SYSTEM = """(.*?)"""', code, re.S).group(1)
    assert load_prompt('d2_system.v1').text == system
    code6 = ''.join(nb['cells'][6]['source'])
    review = re.search('review' + B + '+=' + chr(39) + B + B + 'n(Revisa todas.*?)' + chr(39) + chr(10), code6).group(1)
    assert load_prompt('d2_review.v1').text == review


def test_baseline_has_no_schema(m01):
    fake = FakeLLM(['{}'])
    out = run_baseline(m01, fake)
    assert fake.calls[0][1] is None
    assert out['calls'] == 1


def test_combined_two_calls_and_review_message(m01):
    draft = {'decisions': [], 'tasks': []}
    fake = FakeLLM([draft, draft])
    out = run_d2_combined(m01, fake)
    assert len(fake.calls) == 2 and out['calls'] == 2
    msgs, schema = fake.calls[1]
    assert schema is not None and len(msgs) == 4
    assert [m['role'] for m in msgs] == ['system', 'user', 'assistant', 'user']
    assert 'SALIDAS DE HERRAMIENTAS' in msgs[3]['content']
    assert '\n' + load_prompt('d2_review.v1').text in msgs[3]['content']
    assert msgs[3]['content'].endswith(load_prompt('d2_review.v1').text)
    assert out['tool_reports'] == [] and 'seconds_total' in out
