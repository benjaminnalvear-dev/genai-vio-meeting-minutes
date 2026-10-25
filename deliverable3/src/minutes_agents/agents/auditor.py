"""Agente Auditor (ataca F4): verifica cada ítem contra su cita, busca omisiones y elige la ruta."""
from __future__ import annotations

from minutes_agents.agents.base import AgentSpec, RunConfig
from minutes_agents.prompts import load_prompt
from minutes_agents.schemas import verdict_schema
from minutes_agents.tools import find_revision_cues, find_uncovered_commitments, inspect_evidence

TOOLS = ['inspect_evidence', 'find_uncovered_commitments', 'find_revision_cues']
ROUTES = ['decisions', 'tasks', 'both', 'finish']


def _items(ctx: dict) -> list[dict]:
    return [i for i in (ctx or {}).get('items', []) if isinstance(i, dict)]


def output(tr: dict, ctx: dict, cfg: RunConfig) -> dict[str, dict]:
    ids = list(dict.fromkeys(i['id'] for i in _items(ctx) if isinstance(i.get('id'), str)))
    return {'verdicts': {'type': 'array', 'items': verdict_schema(ids)},
            'route': {'type': 'string', 'enum': list(ROUTES)}}


def precompute(tr: dict, ctx: dict) -> list[dict]:
    items = _items(ctx)
    return ([{'tool': 'find_uncovered_commitments', 'result': find_uncovered_commitments(tr, items)},
             {'tool': 'find_revision_cues', 'result': find_revision_cues(tr)}]
            + [{'tool': 'inspect_evidence', 'item_id': i.get('id'),
                'result': inspect_evidence(tr, i.get('evidence_id'))} for i in items])


def build(cfg: RunConfig) -> AgentSpec:
    return AgentSpec(name='auditor', prompt=load_prompt('auditor.v1'), fewshot=None,
                     tools=list(TOOLS), output=output, precompute=precompute)
