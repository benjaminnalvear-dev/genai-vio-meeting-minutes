"""Finalizador determinístico (no es un agente): fusiona, renumera y aplica chequeos mecánicos."""
from __future__ import annotations

import copy
import datetime as dt
import json
import re

NEW_ID = 'NEW'


_NUM_ID = re.compile(r'([a-z]+)(\d+)')


def _infer_prefix(items: list) -> str:
    for it in items:
        m = _NUM_ID.fullmatch(str(it.get('id'))) if isinstance(it, dict) else None
        if m:
            return m[1]
    return 'n'


def merge(current: list[dict], revised: list[dict], flagged_ids: set[str],
          prefix: str | None = None) -> list[dict]:
    """Fusiona una revisión sin perder ni duplicar ítems.

    - Un ítem actual cuyo id está en `flagged_ids` se reemplaza, en su posición, por las versiones
      revisadas con ese id (si el especialista no devolvió ninguna, se conserva el original).
      Si devolvió varias (ítem dividido), la primera conserva el id y las demás reciben id nuevo.
    - Los ítems no marcados se conservan tal cual, aunque vuelvan en `revised`.
    - 'NEW' nunca es un id reemplazable: es la marca del Auditor para "falta un ítem".
    - Los ítems revisados con id 'NEW' o desconocido se agregan al final con un id provisional
      único: el siguiente número libre con el prefijo de la lista (`prefix`, o inferido de los ids,
      p. ej. 'd' → d07, 't' → t05). Así una ronda posterior puede marcarlos y reemplazarlos.
      Un `supersedes` que apunte al id viejo de un ítem agregado se reescribe al id provisional.
    El Finalizador renumera todo al final, así que estos ids son solo provisionales."""
    flagged = set(flagged_ids) - {NEW_ID}
    current_ids = {c.get('id') for c in current if isinstance(c, dict)}
    prefix = prefix or _infer_prefix(list(current) + list(revised))
    used = [int(m[2]) for i in current if isinstance(i, dict)
            for m in [_NUM_ID.fullmatch(str(i.get('id')))] if m and m[1] == prefix]
    counter = [max(used, default=0)]

    def fresh() -> str:
        counter[0] += 1
        return f'{prefix}{counter[0]:02d}'

    by_id: dict[str, list[dict]] = {}
    appended: list[dict] = []
    renamed: dict[str, str] = {}
    for r in revised:
        if not isinstance(r, dict):
            continue
        rid = r.get('id')
        if rid in flagged and rid in current_ids:
            by_id.setdefault(rid, []).append(dict(r))
        elif rid == NEW_ID or rid not in current_ids:
            item = dict(r, id=fresh())
            if isinstance(rid, str):
                renamed.setdefault(rid, item['id'])
            appended.append(item)
    for rid, versions in by_id.items():
        for extra in versions[1:]:
            extra['id'] = fresh()

    out, replaced = [], set()
    for c in current:
        cid = c.get('id') if isinstance(c, dict) else None
        if cid in by_id:
            if cid not in replaced:
                out.extend(by_id[cid])
                replaced.add(cid)
        else:
            out.append(c)
    created = appended + [v for vs in by_id.values() for v in vs]  # copias: no se muta la entrada
    for it in created:
        if it.get('supersedes') in renamed and it['supersedes'] not in current_ids:
            it['supersedes'] = renamed[it['supersedes']]
    return out + appended


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


def _drop_overlaps(decisions: list, tasks: list) -> tuple[list, list, list[str]]:
    """Regla anti-solapamiento: una decisión y una tarea no citan el mismo turno (en las rúbricas de
    train/validation nunca ocurre). Si chocan:
    - decisión pending → se descarta la tarea (un tema que queda pendiente no es una tarea);
    - en otro caso → se descarta la decisión (el Agente de Decisiones re-registraba tareas como
      decisiones, p. ej. "X prepara la lista")."""
    pending_turns = {d.get('evidence_id') for d in decisions if isinstance(d, dict) and d.get('state') == 'pending'}
    actions = []
    kept_t = []
    for t in tasks:
        if isinstance(t, dict) and t.get('evidence_id') in pending_turns:
            actions.append(f"tarea descartada: cita el turno de una decisión pending ({t.get('evidence_id')})")
        else:
            kept_t.append(t)
    task_turns = {t.get('evidence_id') for t in kept_t if isinstance(t, dict)}
    kept_d = []
    for d in decisions:
        if isinstance(d, dict) and d.get('evidence_id') in task_turns:
            actions.append(f"decisión descartada: cita el mismo turno que una tarea ({d.get('evidence_id')})")
        else:
            kept_d.append(d)
    return kept_d, kept_t, actions


def finalize(tr: dict, decisions: list[dict], tasks: list[dict]) -> dict:
    """Resuelve choques decisión/tarea en un mismo turno (_drop_overlaps), ordena por aparición de
    evidence_id, renumera d01../t01.., remapea supersedes y aplica apply_safe_checks. Los ítems con
    evidencia inexistente quedan al final (y se descartan)."""
    kept_d, kept_t, actions = _drop_overlaps(copy.deepcopy(list(decisions)), copy.deepcopy(list(tasks)))
    ds, d_map = _renumber(_ordered(tr, kept_d), 'd')
    ts, _ = _renumber(_ordered(tr, kept_t), 't')
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
