"""Agente Decisiones (ataca F1): sigue la historia de cada tema hasta su estado."""
from __future__ import annotations

from minutes_agents.agents.base import AgentSpec, RunConfig
from minutes_agents.prompts import load_prompt
from minutes_agents.schemas import decision_item_schema
from minutes_agents.tools import find_revision_cues, inspect_evidence

TOOLS = ['find_revision_cues', 'inspect_evidence']

TOPIC_PLAN = {'type': 'array', 'items': {
    'type': 'object', 'additionalProperties': False, 'required': ['topic', 'evidence_ids'],
    'properties': {'topic': {'type': 'string'},
                   'evidence_ids': {'type': 'array', 'items': {'type': 'string'}}}}}


def output(tr: dict, ctx: dict, cfg: RunConfig) -> dict[str, dict]:
    # Orden de propiedades = orden de generación (la gramática de llama.cpp lo respeta):
    # con CoT, el plan por tema se genera ANTES de las decisiones.
    out = {'topic_plan': TOPIC_PLAN} if cfg.cot else {}
    out['decisions'] = {'type': 'array', 'items': decision_item_schema(tr)}
    return out


def precompute(tr: dict, ctx: dict) -> list[dict]:
    cues = find_revision_cues(tr)
    return ([{'tool': 'find_revision_cues', 'result': cues}]
            + [{'tool': 'inspect_evidence', 'result': inspect_evidence(tr, c['id'])} for c in cues])


def build(cfg: RunConfig) -> AgentSpec:
    return AgentSpec(name='decisions', prompt=load_prompt('decisions.v2'),
                     fewshot=load_prompt('fewshot/decisions.TR01.v2'), tools=list(TOOLS),
                     output=output, precompute=precompute)
