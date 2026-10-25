"""Barandas determinísticas del Auditor (G0–G7).

El Auditor propone veredictos; antes de que lleguen a un especialista, este módulo verifica cada
afirmación verificable con las mismas herramientas determinísticas (tools.py). Los veredictos que la
transcripción no sostiene se descartan con un motivo, y el grafo los registra en la traza.
Funciones puras: no llaman al LLM ni modifican sus entradas.
"""
from __future__ import annotations

import re

from minutes_agents.evaluate import norm
from minutes_agents.finalize import NEW_ID
from minutes_agents.tools import (check_participant, find_revision_cues, find_uncovered_commitments,
                                  resolve_deadline)

TURN_ID = re.compile(r'\bu\d+\b')
REJECTED = re.compile(r'\b(descart\w*|rechaz\w*)\b')
PENDING = re.compile(r'\bpendiente\b')


def _text(tr: dict, evidence_id) -> str | None:
    return next((u['text'] for u in tr['utterances'] if u['id'] == evidence_id), None)


def _speaker(tr: dict, evidence_id) -> str | None:
    return next((u['speaker'] for u in tr['utterances'] if u['id'] == evidence_id), None)


def _g1(tr, decisions, tasks, v) -> tuple[str | None, str | None]:
    """missing_item → (motivo de descarte | None, kind_hint)."""
    if v.get('item_id') != NEW_ID:
        return 'missing_item sobre un ítem existente', None
    uncovered = {u['id'] for u in find_uncovered_commitments(tr, list(decisions) + list(tasks))}
    uncited_cues = ({c['id'] for c in find_revision_cues(tr)}
                    - {d.get('evidence_id') for d in decisions if isinstance(d, dict)})
    cited = set(TURN_ID.findall(str(v.get('detail') or '')))
    if not cited & (uncovered | uncited_cues):
        return ('detail no cita un turno con compromiso sin cubrir ni una señal de cambio sin '
                'decisión'), None
    return None, ('tasks' if cited & uncovered else 'decisions')


def _g3(tr, decisions, d) -> str | None:
    state, text = d.get('state'), norm(_text(tr, d.get('evidence_id')) or '')
    if state == 'superseded':
        cues = {c['id'] for c in find_revision_cues(tr)}
        if any(isinstance(o, dict) and o.get('supersedes') == d.get('id') and o.get('evidence_id') in cues
               for o in decisions):
            return 'superseded respaldado: una decisión posterior la reemplaza con señal de cambio'
    elif state == 'rejected' and REJECTED.search(text):
        return 'rejected respaldado: el turno citado descarta/rechaza'
    elif state == 'pending' and PENDING.search(text):
        return 'pending respaldado: el turno citado dice "pendiente"'
    return None


def _g5(tr, t) -> str | None:
    assignee = t.get('assignee')
    if not isinstance(assignee, str) or not check_participant(tr, assignee)['is_participant']:
        return None
    ev = t.get('evidence_id')
    if assignee == _speaker(tr, ev) or norm(assignee) in norm(_text(tr, ev) or ''):
        return 'el responsable es participante y habla o es nombrado en el turno citado'
    return None


def filter_verdicts(tr: dict, decisions: list[dict], tasks: list[dict],
                    verdicts: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separa los veredictos con ok == False en (aceptados, descartados).

    Los veredictos ok == True se ignoran (no aparecen en ninguna lista). Cada descartado es
    {'verdict': v, 'guard': 'G0'..'G6', 'reason': str}. Un NEW aceptado recibe 'kind_hint'."""
    decs = {d['id']: d for d in decisions if isinstance(d, dict) and 'id' in d}
    tsks = {t['id']: t for t in tasks if isinstance(t, dict) and 'id' in t}
    accepted, dropped = [], []

    def drop(v, guard, reason):
        dropped.append({'verdict': v, 'guard': guard, 'reason': reason})

    for v in verdicts:
        if not isinstance(v, dict) or v.get('ok') is not False:
            continue
        item_id, problem = v.get('item_id'), v.get('problem')
        if item_id != NEW_ID and item_id not in decs and item_id not in tsks:
            drop(v, 'G0', 'unknown item')
            continue
        reason, guard = None, None
        if problem == 'missing_item':
            reason, hint = _g1(tr, decisions, tasks, v)
            guard = 'G1'
            if reason is None:
                accepted.append(dict(v, kind_hint=hint))
                continue
        elif problem == 'wrong_deadline' and item_id in tsks:
            t = tsks[item_id]
            sug = resolve_deadline(tr, t.get('evidence_id'))['suggested']
            if t.get('deadline') is not None and sug is not None and sug[:10] == str(t['deadline'])[:10]:
                guard, reason = 'G2', f'el día coincide con resolve_deadline ({sug})'
        elif problem == 'wrong_state' and item_id in decs:
            guard, reason = 'G3', _g3(tr, decisions, decs[item_id])
        elif problem == 'wrong_state' and item_id in tsks:
            guard, reason = 'G4', 'una tarea confirmada es final por regla del proyecto'
        elif problem == 'wrong_assignee' and item_id in tsks:
            guard, reason = 'G5', _g5(tr, tsks[item_id])
        elif problem == 'merged_items' and item_id in decs:
            d = decs[item_id]
            if d.get('supersedes') is not None or any(
                    o.get('supersedes') == item_id for o in decs.values()):
                guard, reason = 'G6', 'la decisión es parte de una cadena de reemplazo, no una fusión'
        if reason is not None:
            drop(v, guard, reason)
        else:
            accepted.append(v)
    return accepted, dropped


def route_from(accepted: list[dict]) -> str:
    """Ruta recalculada a partir de los veredictos aceptados."""
    kinds = set()
    for v in accepted:
        item_id = str(v.get('item_id', ''))
        if item_id == NEW_ID:
            if v.get('kind_hint') in ('decisions', 'tasks'):
                kinds.add(v['kind_hint'])
        elif item_id.startswith('d'):
            kinds.add('decisions')
        elif item_id.startswith('t'):
            kinds.add('tasks')
    if kinds == {'decisions', 'tasks'}:
        return 'both'
    return kinds.pop() if kinds else 'finish'


def dedupe_new(current: list[dict], merged: list[dict]) -> tuple[list[dict], list[dict]]:
    """G7: descarta los ítems agregados por merge cuyo evidence_id ya cita un ítem preexistente."""
    current_ids = {c.get('id') for c in current if isinstance(c, dict)}
    old_evidence = {m.get('evidence_id') for m in merged
                    if isinstance(m, dict) and m.get('id') in current_ids}
    kept, dropped = [], []
    for m in merged:
        if isinstance(m, dict) and m.get('id') not in current_ids and m.get('evidence_id') in old_evidence:
            dropped.append(m)
        else:
            kept.append(m)
    return kept, dropped
