"""Finalizador determinístico (no es un agente): fusiona, renumera y aplica chequeos mecánicos."""
from __future__ import annotations

import copy
import datetime as dt
import json
import re

NEW_ID = 'NEW'


def merge(current: list[dict], revised: list[dict], flagged_ids: set[str]) -> list[dict]:
    """Reemplaza los ítems marcados por su versión revisada (si existe), conserva el resto
    y agrega al final los ítems revisados con id nuevo o 'NEW'. Una revisión no pierde ítems."""
    by_id: dict[str, list[dict]] = {}
    for r in revised:
        if isinstance(r, dict):
            by_id.setdefault(r.get('id'), []).append(r)
    current_ids = {c.get('id') for c in current if isinstance(c, dict)}
    out = []
    for c in current:
        cid = c.get('id') if isinstance(c, dict) else None
        if cid in flagged_ids and cid in by_id:
            out.extend(by_id[cid])
        else:
            out.append(c)
    out += [r for r in revised if isinstance(r, dict)
            and (r.get('id') == NEW_ID or r.get('id') not in current_ids)]
    return out


def _ordered(tr: dict, items: list) -> list:
    pos = {u['id']: k for k, u in enumerate(tr['utterances'])}
    end = len(pos)
    key = lambda it: pos.get(it.get('evidence_id'), end) if isinstance(it, dict) else end
    return sorted(items, key=key)  # sorted es estable: los empates conservan el orden de entrada


def _renumber(items: list, prefix: str) -> tuple[list, dict]:
    id_map: dict = {}
    for n, it in enumerate(items, 1):
        if not isinstance(it, dict):
            continue
        new = f'{prefix}{n:02d}'
        old = it.get('id')
        if isinstance(old, str):
            id_map.setdefault(old, new)
        it['id'] = new
    return items, id_map


# Copiado sin cambios del D2 (notebook, celda 6).
def apply_safe_checks(tr, result):
    # Solo invariantes mecánicas: no se borran errores semánticos para maquillar la evaluación.
    obj=result.get('parsed')
    if not isinstance(obj,dict): return result
    cleaned=json.loads(json.dumps(obj))
    ids={u['id'] for u in tr['utterances']}
    actions=[]
    for kind in ('decisions','tasks'):
        valid=[]
        for item in cleaned.get(kind,[]):
            if not isinstance(item,dict) or item.get('evidence_id') not in ids:
                actions.append('descartado: evidence_id inexistente'); continue
            if kind=='tasks' and item.get('deadline') is not None:
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?)?',str(item['deadline'])):
                    item['deadline']=None; actions.append('fecha no ISO a null')
                else:
                    try:
                        if 'T' in item['deadline']:
                            item['deadline']=dt.datetime.fromisoformat(item['deadline']).isoformat(timespec='minutes')
                        else: item['deadline']=dt.date.fromisoformat(item['deadline']).isoformat()
                    except ValueError:
                        item['deadline']=None; actions.append('fecha imposible a null')
            valid.append(item)
        cleaned[kind]=valid
    result['parsed']=cleaned
    result['mechanical_actions']=actions
    return result


def finalize(tr: dict, decisions: list[dict], tasks: list[dict]) -> dict:
    """Ordena por aparición de evidence_id, renumera d01../t01.., remapea supersedes y
    aplica apply_safe_checks. Los ítems con evidencia inexistente quedan al final (y se descartan)."""
    ds, d_map = _renumber(_ordered(tr, copy.deepcopy(list(decisions))), 'd')
    ts, _ = _renumber(_ordered(tr, copy.deepcopy(list(tasks))), 't')
    actions = []
    for d in ds:
        if isinstance(d, dict) and d.get('supersedes') is not None:
            d['supersedes'] = d_map.get(d['supersedes'])
            if d['supersedes'] is None:
                actions.append('supersedes sin resolver a null')
    result = apply_safe_checks(tr, {'parsed': {'decisions': ds, 'tasks': ts}})
    out = result['parsed']
    actions += result.get('mechanical_actions', [])
    kept = {d['id'] for d in out['decisions']}
    for d in out['decisions']:
        if d.get('supersedes') is not None and d['supersedes'] not in kept:
            d['supersedes'] = None
            actions.append('supersedes colgante a null')
    return {'decisions': out['decisions'], 'tasks': out['tasks'], 'mechanical_actions': actions}
