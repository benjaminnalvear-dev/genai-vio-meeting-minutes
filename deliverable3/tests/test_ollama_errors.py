import pytest
import requests

import minutes_agents.llm as llm
from minutes_agents.llm import OllamaError, OllamaLLM, preflight


class _Resp:
    def __init__(self, status, payload=None, text=''):
        self.status_code, self._payload, self.text = status, payload, text
        self.ok = status < 400

    def json(self):
        if self._payload is None:
            raise ValueError('no json')
        return self._payload


def _ok_chat(content='{"ok": true}'):
    return _Resp(200, {'message': {'content': content}, 'eval_count': 3, 'prompt_eval_count': 5, 'done_reason': 'stop'})


def test_http_500_raises_with_ollama_message(monkeypatch):
    monkeypatch.setattr(llm.time, 'sleep', lambda s: None)
    monkeypatch.setattr(llm.requests, 'post', lambda *a, **k: _Resp(500, {'error': 'model requires more system memory (5.1 GiB) than is available (4.0 GiB)'}))
    with pytest.raises(OllamaError) as e:
        OllamaLLM().chat([{'role': 'user', 'content': 'x'}])
    assert 'HTTP 500' in str(e.value) and 'more system memory' in str(e.value)


def test_http_error_without_json_uses_text(monkeypatch):
    monkeypatch.setattr(llm.time, 'sleep', lambda s: None)
    monkeypatch.setattr(llm.requests, 'post', lambda *a, **k: _Resp(502, None, 'Bad Gateway'))
    with pytest.raises(OllamaError, match='Bad Gateway'):
        OllamaLLM().chat([{'role': 'user', 'content': 'x'}])


def test_transient_5xx_is_retried(monkeypatch):
    monkeypatch.setattr(llm.time, 'sleep', lambda s: None)
    answers = [_Resp(500, {'error': 'llama runner process has terminated'}), _ok_chat()]
    monkeypatch.setattr(llm.requests, 'post', lambda *a, **k: answers.pop(0))
    assert OllamaLLM().chat([{'role': 'user', 'content': 'x'}])['parsed'] == {'ok': True}


def test_4xx_is_not_retried(monkeypatch):
    calls = []

    def post(*a, **k):
        calls.append(1)
        return _Resp(404, {'error': 'model not found'})
    monkeypatch.setattr(llm.requests, 'post', post)
    with pytest.raises(OllamaError, match='model not found'):
        OllamaLLM().chat([{'role': 'user', 'content': 'x'}])
    assert len(calls) == 1


def test_preflight_ok(monkeypatch):
    monkeypatch.setattr(llm.requests, 'get', lambda *a, **k: _Resp(200, {'models': [{'name': llm.MODEL}]}))
    sent = {}

    def post(url, json=None, timeout=None):
        sent.update(json)
        return _ok_chat()
    monkeypatch.setattr(llm.requests, 'post', post)
    preflight('http://127.0.0.1:11434')
    # Loads the model with the same context size the experiment uses, so memory problems show up here.
    assert sent['options']['num_ctx'] == llm.PARAMS['num_ctx'] and 'format' in sent


def test_preflight_model_missing(monkeypatch):
    monkeypatch.setattr(llm.requests, 'get', lambda *a, **k: _Resp(200, {'models': []}))
    with pytest.raises(OllamaError, match='no está descargado'):
        preflight('http://127.0.0.1:11434')


def test_preflight_server_down(monkeypatch):
    def get(*a, **k):
        raise requests.ConnectionError('refused')
    monkeypatch.setattr(llm.requests, 'get', get)
    with pytest.raises(OllamaError, match='no responde'):
        preflight('http://127.0.0.1:11434')


def test_preflight_chat_error_shows_message(monkeypatch):
    monkeypatch.setattr(llm.time, 'sleep', lambda s: None)
    monkeypatch.setattr(llm.requests, 'get', lambda *a, **k: _Resp(200, {'models': [{'name': llm.MODEL}]}))
    monkeypatch.setattr(llm.requests, 'post', lambda *a, **k: _Resp(500, {'error': 'CUDA error: out of memory'}))
    with pytest.raises(OllamaError, match='out of memory'):
        preflight('http://127.0.0.1:11434')


def test_cli_stops_before_running_when_preflight_fails(monkeypatch, dataset_dir, tmp_path, capsys):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location('run_experiment', Path(__file__).resolve().parents[1] / 'scripts' / 'run_experiment.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def boom(host, model=llm.MODEL):
        raise OllamaError('Ollama HTTP 500: CUDA error: out of memory')
    monkeypatch.setattr(mod, 'preflight', boom)
    ran = []
    monkeypatch.setattr(mod, 'run_experiment', lambda *a, **k: ran.append(1))
    with pytest.raises(SystemExit) as e:
        mod.main(['--data', str(dataset_dir), '--split', 'validation', '--conditions', 'full',
                  '--out', str(tmp_path / 'out'), '--limit', '1'])
    assert e.value.code == 2 and not ran
    assert 'out of memory' in capsys.readouterr().out
