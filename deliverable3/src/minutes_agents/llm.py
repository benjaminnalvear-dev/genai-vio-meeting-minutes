"""LLM client: Ollama backend (D2 inference()), on-disk cache, Protocol."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Protocol

import requests
from jsonschema import Draft202012Validator

MODEL = 'ministral-3:3b-instruct-2512-q4_K_M'
PARAMS = {'temperature': 0, 'seed': 42, 'num_ctx': 12288, 'num_predict': 2400}


class LLM(Protocol):
    def chat(self, messages: list[dict], schema: dict | None) -> dict: ...


def parse_result(raw, schema, seconds=0.0, eval_count=0, prompt_eval_count=0, done_reason=None) -> dict:
    """Build the D2 result dict from raw model text."""
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            parsed = None
    except (json.JSONDecodeError, TypeError):
        parsed = None
    return {'raw': raw, 'parsed': parsed, 'seconds': seconds,
            'eval_count': eval_count, 'prompt_eval_count': prompt_eval_count, 'done_reason': done_reason,
            'schema_valid': bool(parsed is not None and schema is not None
                                 and Draft202012Validator(schema).is_valid(parsed))}


class OllamaLLM:
    def __init__(self, host: str = 'http://127.0.0.1:11434', model: str = MODEL, params: dict = PARAMS):
        self.host, self.model, self.params = host.rstrip('/'), model, dict(params)

    def chat(self, messages: list[dict], schema: dict | None = None) -> dict:
        body = {'model': self.model, 'messages': messages, 'stream': False, 'options': self.params}
        if schema is not None:
            body['format'] = schema
        t0 = time.monotonic()
        res = requests.post(f'{self.host}/api/chat', json=body, timeout=900)
        res.raise_for_status()
        out = res.json()
        raw = out['message'].get('content', '')
        return parse_result(raw, schema, round(time.monotonic() - t0, 2),
                            out.get('eval_count'), out.get('prompt_eval_count'), out.get('done_reason'))


class CachedLLM:
    def __init__(self, inner: LLM, cache_dir: Path):
        self.inner, self.cache_dir = inner, Path(cache_dir)
        self.calls_made = 0

    def _key(self, messages, schema) -> str:
        payload = {'messages': messages, 'schema': schema,
                   'model': getattr(self.inner, 'model', None),
                   'params': getattr(self.inner, 'params', None)}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()

    def chat(self, messages: list[dict], schema: dict | None = None) -> dict:
        path = self.cache_dir / f'{self._key(messages, schema)}.json'
        if path.exists():
            try:
                return json.loads(path.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass  # corrupted/truncated cache entry: treat as miss
        result = self.inner.chat(messages, schema)
        self.calls_made += 1
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + '.tmp')
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(tmp, path)
        return result
