"""Agente Tareas (ataca F2 y F3): quién, qué, para cuándo y con qué condición."""
from __future__ import annotations

from minutes_agents.agents.base import AgentSpec, RunConfig
from minutes_agents.prompts import load_prompt
from minutes_agents.schemas import task_item_schema
from minutes_agents.tools import check_participant, resolve_deadline

TOOLS = ['resolve_deadline', 'check_participant', 'inspect_evidence']


def output(tr: dict, ctx: dict, cfg: RunConfig) -> dict[str, dict]:
    return {'tasks': {'type': 'array', 'items': task_item_schema(tr)}}


def _participants(tr: dict) -> list[str]:
    return list(tr.get('participants') or sorted({u['speaker'] for u in tr['utterances']}))


def precompute(tr: dict, ctx: dict) -> list[dict]:
    reports = []
    for u in tr['utterances']:
        r = resolve_deadline(tr, u['id'])
        if r.get('suggested') is not None:
            reports.append({'tool': 'resolve_deadline', 'result': r})
    reports += [{'tool': 'check_participant', 'result': check_participant(tr, p)} for p in _participants(tr)]
    return reports


def build(cfg: RunConfig) -> AgentSpec:
    return AgentSpec(name='tasks', prompt=load_prompt('tasks.v2'),
                     fewshot=load_prompt('fewshot/tasks.TR01'), tools=list(TOOLS),
                     output=output, precompute=precompute)
