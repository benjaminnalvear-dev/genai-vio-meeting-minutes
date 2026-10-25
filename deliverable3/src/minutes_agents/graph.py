"""Grafo LangGraph: decisions -> tasks -> auditor <-> especialistas -> finalize."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import TypedDict

from jsonschema import Draft202012Validator
from langgraph.graph import END, START, StateGraph

from minutes_agents.agents import auditor as auditor_mod
from minutes_agents.agents import decisions as decisions_mod
from minutes_agents.agents import tasks as tasks_mod
from minutes_agents.agents.base import RunConfig, run_react, user_message
from minutes_agents.finalize import NEW_ID, finalize, merge
from minutes_agents.llm import LLM
from minutes_agents.schemas import make_schema
from minutes_agents.tracing import Tracer


class MeetingState(TypedDict):
    transcript: dict
    decisions: list[dict]
    tasks: list[dict]
    verdicts: list[dict]
    route: str | None
    audit_round: int  # revisiones ya hechas
    flagged: list[str]
    trace_events: list[dict]
    calls: int
    mechanical_actions: list[str]


def route_after_audit(state: MeetingState, cfg: RunConfig) -> str:
    """'finalize' si el Auditor termina (o su salida no es válida); si no, el primer especialista.
    El incremento de `audit_round` lo hace el nodo del Auditor (una arista condicional no escribe estado)."""
    route = state.get('route')
    if route in ('decisions', 'both'):
        return 'revise_decisions'
    if route == 'tasks':
        return 'revise_tasks'
    return 'finalize'


def route_after_revision(state: MeetingState, cfg: RunConfig, *, just_revised: str = 'tasks') -> str:
    if just_revised == 'decisions' and state.get('route') == 'both':
        return 'revise_tasks'
    return 'finalize' if state['audit_round'] >= cfg.auditor_rounds else 'auditor'


def _items(state: MeetingState) -> list[dict]:
    return list(state['decisions']) + list(state['tasks'])


def _mine(state: MeetingState, kind: str) -> tuple[list[dict], list[dict], set[str]]:
    """Veredictos marcados (ok == False) que le tocan al especialista, sus ítems y sus ids."""
    prefix = 'd' if kind == 'decisions' else 't'
    current = state[kind]
    ids = {i.get('id') for i in current if isinstance(i, dict)}
    gets_new = state.get('route') in (kind, 'both')
    verdicts = [v for v in state['verdicts'] if v.get('ok') is False and (
        (str(v.get('item_id', '')).startswith(prefix) and v.get('item_id') in ids)
        or (v.get('item_id') == NEW_ID and gets_new))]
    flagged = {v['item_id'] for v in verdicts if v['item_id'] in ids}
    items = [i for i in current if isinstance(i, dict) and i.get('id') in flagged]
    return verdicts, items, flagged


def build_graph(llm: LLM, tracer: Tracer, cfg: RunConfig):
    dec, tsk, aud = decisions_mod.build(cfg), tasks_mod.build(cfg), auditor_mod.build(cfg)

    def decisions_node(state: MeetingState):
        tr = state['transcript']
        r = run_react(dec, tr, user_message(tr), llm, tracer, cfg, {'items': _items(state)})
        return {'decisions': r['output']['decisions'], 'calls': state['calls'] + r['calls']}

    def tasks_node(state: MeetingState):
        tr = state['transcript']
        r = run_react(tsk, tr, user_message(tr), llm, tracer, cfg, {'items': _items(state)})
        return {'tasks': r['output']['tasks'], 'calls': state['calls'] + r['calls']}

    def auditor_node(state: MeetingState):
        tr = state['transcript']
        msg = user_message(tr, items={'decisions': state['decisions'], 'tasks': state['tasks']})
        r = run_react(aud, tr, msg, llm, tracer, cfg, {'items': _items(state)})
        verdicts, route = r['output']['verdicts'] or [], r['output']['route']
        if not verdicts and route is None:
            route = 'finish'  # salida inválida: se corta el lazo
        flagged = [v['item_id'] for v in verdicts if v.get('ok') is False]
        revising = route in ('decisions', 'tasks', 'both')
        nxt = route_after_audit({'route': route}, cfg)
        tracer.log('router', state['audit_round'], route=route, flagged=flagged, next=nxt)
        return {'verdicts': verdicts, 'route': route, 'flagged': flagged,
                'audit_round': state['audit_round'] + (1 if revising else 0),
                'calls': state['calls'] + r['calls']}

    def _revise(kind: str, spec, state: MeetingState):
        tr = state['transcript']
        verdicts, items, flagged = _mine(state, kind)
        r = run_react(spec, tr, user_message(tr, feedback=verdicts, items=items), llm, tracer, cfg,
                      {'items': _items(state)})
        merged = merge(state[kind], r['output'][kind], flagged, prefix=kind[0])
        return {kind: merged, 'calls': state['calls'] + r['calls']}

    def revise_decisions(state: MeetingState):
        return _revise('decisions', dec, state)

    def revise_tasks(state: MeetingState):
        return _revise('tasks', tsk, state)

    def finalize_node(state: MeetingState):
        out = finalize(state['transcript'], state['decisions'], state['tasks'])
        tracer.log('finalize', 0, mechanical_actions=out['mechanical_actions'],
                   decisions=len(out['decisions']), tasks=len(out['tasks']),
                   audit_rounds=state['audit_round'])
        return {'decisions': out['decisions'], 'tasks': out['tasks'],
                'mechanical_actions': out['mechanical_actions'], 'trace_events': list(tracer.events)}

    g = StateGraph(MeetingState)
    for name, fn in [('decisions', decisions_node), ('tasks', tasks_node),
                     ('revise_decisions', revise_decisions), ('revise_tasks', revise_tasks),
                     ('finalize', finalize_node)]:
        g.add_node(name, fn)
    g.add_edge(START, 'decisions')
    g.add_edge('decisions', 'tasks')
    if cfg.auditor_rounds > 0:
        g.add_node('auditor', auditor_node)
        g.add_edge('tasks', 'auditor')
        g.add_conditional_edges('auditor', lambda s: route_after_audit(s, cfg),
                                ['revise_decisions', 'revise_tasks', 'finalize'])
        g.add_conditional_edges('revise_decisions',
                                lambda s: route_after_revision(s, cfg, just_revised='decisions'),
                                ['revise_tasks', 'auditor', 'finalize'])
        g.add_conditional_edges('revise_tasks',
                                lambda s: route_after_revision(s, cfg, just_revised='tasks'),
                                ['auditor', 'finalize'])
    else:
        g.add_edge('tasks', 'finalize')
    g.add_edge('finalize', END)
    return g.compile()


def run_meeting(tr: dict, llm: LLM, cfg: RunConfig, trace_path: Path | None) -> dict:
    if trace_path is not None and Path(trace_path).exists():
        Path(trace_path).unlink()  # una traza por ejecución
    tracer = Tracer(trace_path)
    graph = build_graph(llm, tracer, cfg)
    state: MeetingState = {'transcript': tr, 'decisions': [], 'tasks': [], 'verdicts': [], 'route': None,
                           'audit_round': 0, 'flagged': [], 'trace_events': [], 'calls': 0,
                           'mechanical_actions': []}
    t0 = time.perf_counter()
    final = graph.invoke(state)
    seconds = time.perf_counter() - t0
    parsed = {'decisions': final['decisions'], 'tasks': final['tasks']}
    return {'parsed': parsed, 'raw': json.dumps(parsed, ensure_ascii=False), 'seconds': seconds,
            'calls': final['calls'],
            'eval_count': sum(e.get('tokens') or 0 for e in tracer.events),
            'schema_valid': Draft202012Validator(make_schema(tr)).is_valid(parsed),
            'trace_path': str(trace_path) if trace_path is not None else None}
