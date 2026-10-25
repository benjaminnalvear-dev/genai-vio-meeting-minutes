"""Test doubles."""
from __future__ import annotations

import json

from minutes_agents.llm import parse_result


class FakeLLM:
    """Scripted LLM: each item is a dict (model's JSON) or a raw string."""

    def __init__(self, script: list):
        self.script = list(script)
        self.calls: list[tuple] = []

    def chat(self, messages: list[dict], schema: dict | None = None) -> dict:
        self.calls.append((messages, schema))
        if not self.script:
            raise AssertionError('FakeLLM script exhausted: no further calls expected')
        item = self.script.pop(0)
        raw = item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
        return parse_result(raw, schema)


# --- Scripted step outputs valid against the real step schemas for RunConfig('full') (M01) ---
def _decision(statement='Se adopta el plan acordado'):
    return {'id': 'd01', 'topic': 'plan', 'statement': statement, 'state': 'final',
            'condition': None, 'supersedes': None, 'evidence_id': 'u05'}


def _task(description='Enviar el informe', state='pending'):
    return {'id': 't01', 'description': description, 'assignee': None, 'deadline': None,
            'condition': None, 'state': state, 'evidence_id': 'u08'}


dec_finish = {'thought': 'revisé el tema', 'action': 'finish', 'tool_calls': [],
              'decisions': [_decision()], 'topic_plan': [{'topic': 'plan', 'evidence_ids': ['u05']}]}
dec_revised = {'thought': 'corrijo', 'action': 'finish', 'tool_calls': [],
               'decisions': [_decision('Se adopta el plan acordado (revisado)')],
               'topic_plan': [{'topic': 'plan', 'evidence_ids': ['u05']}]}
task_finish = {'thought': 'listo', 'action': 'finish', 'tool_calls': [], 'tasks': [_task()]}
task_revised = {'thought': 'corrijo', 'action': 'finish', 'tool_calls': [],
                'tasks': [_task('Enviar el informe final', 'final')]}


def audit_route(route, flag=None):
    flags = [flag] if isinstance(flag, str) else list(flag or [])
    verdicts = [{'item_id': f, 'ok': False, 'problem': 'wrong_state', 'detail': 'revisar'} for f in flags]
    return {'thought': 'auditoría', 'action': 'finish', 'tool_calls': [],
            'verdicts': verdicts, 'route': route}
