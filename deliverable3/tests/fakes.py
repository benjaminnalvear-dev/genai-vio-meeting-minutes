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
