import json
import subprocess
import sys
from pathlib import Path

import pytest

from minutes_agents.experiment import CONDITIONS, load_config, run_experiment
from tests.fakes import FakeLLM, audit_route, dec_finish, task_finish

ROOT = Path(__file__).resolve().parents[1]


def _script():
    return [dec_finish, task_finish, audit_route('finish'), dec_finish, task_finish]


def test_run_experiment_and_resume(m01, m01_gold, tmp_path):
    trs, gold = {'M01': m01}, {'M01': m01_gold}
    out, tr = tmp_path / 'out', tmp_path / 'tr'
    s = run_experiment(['full', 'no_auditor'], trs, gold, FakeLLM(_script()), out, tr,
                       meta_extra={'split': 'test'}, log=lambda m: None)
    assert isinstance(s['full']['primary']['decisions']['f1'], float)
    assert isinstance(s['no_auditor']['primary']['tasks']['f1'], float)
    assert (out / 'full' / 'M01.json').exists() and (tr / 'full' / 'M01.jsonl').exists()
    assert json.loads((out / 'summary.json').read_text('utf-8'))['meta']['split'] == 'test'
    assert s['meta']['ollama_version'] is None and s['meta']['prompts']
    assert set(s['paired_full_vs_d2'] if 'paired_full_vs_d2' in s else []) == set()
    empty = FakeLLM([])
    s2 = run_experiment(['full', 'no_auditor'], trs, gold, empty, out, tr, log=lambda m: None)
    assert empty.calls == []
    for c in ('full', 'no_auditor'):
        assert s2[c]['primary']['decisions'] == s[c]['primary']['decisions']
        assert s2[c]['primary']['tasks'] == s[c]['primary']['tasks']


def test_unknown_condition(m01, m01_gold, tmp_path):
    with pytest.raises(ValueError):
        run_experiment(['nope'], {'M01': m01}, {'M01': m01_gold}, FakeLLM([]), tmp_path, tmp_path)


@pytest.mark.parametrize('name', CONDITIONS[2:])
def test_load_config(name):
    cfg = load_config(name)
    assert cfg.name == name
    defaults = load_config('full')
    changed = [k for k in ('react', 'auditor_rounds', 'fewshot', 'cot') if getattr(cfg, k) != getattr(defaults, k)]
    assert len(changed) == (0 if name == 'full' else 1)


def test_cli_help():
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'run_experiment.py'), '--help'],
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0 and '--conditions' in r.stdout
