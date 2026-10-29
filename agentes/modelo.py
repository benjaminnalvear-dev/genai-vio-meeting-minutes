"""Llamada a Ollama. Es `inference` del notebook de D2 con el host configurable; modelo y parámetros iguales."""
import json
import os
import time

import requests
from jsonschema import Draft202012Validator

MODEL = os.environ.get('AGENTES_MODEL', 'ministral-3:3b-instruct-2512-q4_K_M')
HOST = os.environ.get('OLLAMA_HOST_URL', 'http://127.0.0.1:11434')
PARAMS = {'temperature': 0, 'seed': 42, 'num_ctx': 12288, 'num_predict': 2400}


def inference(messages, schema=None):
    body = {'model':MODEL, 'messages':messages, 'stream':False, 'options':PARAMS}
    if schema is not None: body['format'] = schema
    t0 = time.monotonic()
    res = requests.post(HOST + '/api/chat', json=body, timeout=900)
    res.raise_for_status()
    out = res.json()
    raw = out['message'].get('content','')
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict): parsed = None
    except (json.JSONDecodeError, TypeError): parsed = None
    return {'raw':raw, 'parsed':parsed, 'seconds':round(time.monotonic()-t0,2),
            'eval_count':out.get('eval_count'), 'prompt_eval_count':out.get('prompt_eval_count'),
            'schema_valid':bool(parsed is not None and schema is not None and Draft202012Validator(schema).is_valid(parsed))}
