"""Extended metrics (strict F1, per-trap breakdown) and benchmark difficulty analysis."""
import re
from collections import Counter, defaultdict

from minutes_agents.evaluate import comparable_date, match_items, norm, recover_baseline

# Absent third parties, taken from each rubric's evaluation_notes (gold side only).
ABSENT = {'M01': ['paula'], 'M02': ['sofia'], 'M03': ['martin', 'organizador'], 'M04': ['camila'],
          'M05': ['javier'], 'M06': ['paula'], 'M07': ['andres'], 'M08': ['agencia'],
          'M09': ['lucia'], 'M10': ['gerente']}

_WEEKDAY = r'\b(lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b'
_MONTHS = r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)'
REL = 'relativo (hoy/mañana/día)'
NOT_IN_QUOTE = 'plazo no está en la cita'


def _utext(tr, uid):
    return next((u['text'] for u in tr['utterances'] if u['id'] == uid), '')


def _uidx(tr, uid):
    return next((i for i, u in enumerate(tr['utterances']) if u['id'] == uid), None)


def deadline_kind(task, tr):
    """How hard the gold deadline is to resolve from the cited utterance."""
    if task['deadline'] is None:
        return 'sin plazo (null)'
    s = norm(_utext(tr, task['evidence_id']))
    if re.search(r'\b\d{1,2} de ' + _MONTHS + r'\b', s):
        return 'fecha explícita'
    if re.search(r'\b(hoy|manana|pasado manana)\b', s) or re.search(_WEEKDAY, s):
        return REL
    return NOT_IN_QUOTE


def decision_kind(d):
    if d['state'] == 'superseded':
        return 'superseded'
    if d['state'] == 'final':
        return 'final tras reemplazo' if d['supersedes'] else 'final simple'
    return d['state']  # rejected / pending


def difficulty_table(transcripts, gold):
    rows = []
    for m in sorted(transcripts):
        tr, g = transcripts[m], gold[m]
        dec, tasks = g['decisions'], g['tasks']
        by_topic = defaultdict(list)
        for d in dec:
            by_topic[d['topic']].append(d)
        chains = [len(v) for v in by_topic.values() if len(v) > 1]
        dist = [max(i) - min(i) for i in
                ([_uidx(tr, d['evidence_id']) for d in v] for v in by_topic.values() if len(v) > 1)]
        rows.append({
            'meeting': m, 'turnos': len(tr['utterances']),
            'decisiones': len(dec),
            'final': sum(d['state'] == 'final' for d in dec),
            'superseded': sum(d['state'] == 'superseded' for d in dec),
            'rejected': sum(d['state'] == 'rejected' for d in dec),
            'pending': sum(d['state'] == 'pending' for d in dec),
            'temas_revisados': len(chains), 'cadena_max': max(chains, default=1),
            'distancia_media_revision': round(sum(dist) / len(dist), 1) if dist else 0,
            'decisiones_condicionales': sum(d['condition'] is not None for d in dec),
            'tareas': len(tasks),
            'tareas_condicionales': sum(t['condition'] is not None for t in tasks),
            'tareas_no_final': sum(t['state'] != 'final' for t in tasks),
            'tareas_sin_responsable': sum(t['assignee'] is None for t in tasks),
            'plazo_con_hora': sum(bool(t['deadline']) and 'T' in t['deadline'] for t in tasks),
            'plazo_relativo': sum(deadline_kind(t, tr) == REL for t in tasks),
            'plazo_fuera_de_cita': sum(deadline_kind(t, tr) == NOT_IN_QUOTE for t in tasks),
            'terceros_ausentes': len(ABSENT[m]),
            'menciones_ausentes': sum(any(a in norm(u['text']) for a in ABSENT[m])
                                      for u in tr['utterances']),
        })
    return rows


def _f1(tp, pred, gold):
    prec = tp / pred if pred else (1.0 if not gold else 0.0)
    rec = tp / gold if gold else 1.0
    return 2 * prec * rec / (prec + rec) if prec + rec else 0.0


def _deadline_error(pred_dl, gold_dl):
    p, g = comparable_date(pred_dl), comparable_date(gold_dl)
    if p == g:
        return 'ok'
    if g is None:
        return 'inventado'
    if p is None:
        return 'omitido'
    if str(p)[:10] == str(g)[:10]:
        return 'hora mal/falta'
    return 'dia equivocado'


def extended_metrics(outputs, transcripts, gold, is_baseline):
    totals = Counter()
    per_trap = defaultdict(Counter)
    dl_errors = {k: 0 for k in ('ok', 'dia equivocado', 'inventado', 'hora mal/falta', 'omitido')}
    states = Counter()
    non_part = 0
    per_meeting = {}
    for mid in sorted(outputs):
        out, tr, g = outputs[mid], transcripts[mid], gold[mid]
        totals['calls'] += out.get('calls', 0) or 0
        totals['tokens'] += out.get('eval_count', 0) or 0
        p = recover_baseline(out['raw']) if is_baseline else out.get('parsed')
        p = p if isinstance(p, dict) else {}
        f1s = {}
        for kind in ('decisions', 'tasks'):
            pred = p.get(kind, [])
            pred = pred if isinstance(pred, list) else []
            pairs = match_items(pred, g[kind], kind)
            by_gold = {id(gi): x for x, gi, _ in pairs}
            strict_tp = sum(x.get('state') == gi.get('state') for x, gi, _ in pairs)
            f1s[kind] = (_f1(len(pairs), len(pred), len(g[kind])),
                         _f1(strict_tp, len(pred), len(g[kind])))
            totals[kind + '_strict_tp'] += strict_tp
            totals[kind + '_pred'] += len(pred)
            totals[kind + '_gold'] += len(g[kind])
            tag = 'D' if kind == 'decisions' else 'T'
            for gi in g[kind]:
                cats = [f'{tag}: ' + (decision_kind(gi) if kind == 'decisions' else deadline_kind(gi, tr))]
                if gi['condition'] is not None:
                    cats.append(f'{tag}: con condición')
                x = by_gold.get(id(gi))
                for c in cats:
                    b = per_trap[c]
                    b['gold'] += 1
                    if x is not None:
                        b['found'] += 1
                        b['state_ok'] += int(x.get('state') == gi['state'])
                        if kind == 'tasks':
                            b['deadline_ok'] += int(comparable_date(x.get('deadline'))
                                                    == comparable_date(gi['deadline']))
                            b['assignee_ok'] += int(x.get('assignee') == gi['assignee'])
                if kind == 'tasks' and x is not None:
                    dl_errors[_deadline_error(x.get('deadline'), gi['deadline'])] += 1
            if kind == 'tasks':
                parts = set(tr['participants'])
                for x in pred:
                    if not isinstance(x, dict):
                        continue
                    states[x.get('state')] += 1
                    a = x.get('assignee')
                    if a is not None and a not in parts:
                        non_part += 1
        per_meeting[mid] = {'decisions_f1': f1s['decisions'][0], 'tasks_f1': f1s['tasks'][0],
                            'strict_f1': (f1s['decisions'][1] + f1s['tasks'][1]) / 2}
    return {
        'strict_f1': {k: round(_f1(totals[k + '_strict_tp'], totals[k + '_pred'], totals[k + '_gold']), 3)
                      for k in ('decisions', 'tasks')},
        'per_trap': {c: {k: v[k] for k in ('gold', 'found', 'state_ok', 'deadline_ok', 'assignee_ok')}
                     for c, v in sorted(per_trap.items())},
        'deadline_errors': dl_errors,
        'task_states_predicted': dict(states),
        'non_participant_assignees': non_part,
        'per_meeting': per_meeting,
        'calls_total': totals['calls'],
        'tokens_total': totals['tokens'],
    }


def paired_comparison(per_meeting_a, per_meeting_b, key):
    res = {'wins': 0, 'ties': 0, 'losses': 0}
    for mid in per_meeting_a:
        d = per_meeting_a[mid][key] - per_meeting_b[mid][key]
        res['ties' if abs(d) < 1e-9 else 'wins' if d > 0 else 'losses'] += 1
    return res
