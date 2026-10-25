"""Herramientas determinísticas que los agentes ReAct pueden invocar.

inspect_evidence, resolve_deadline y find_revision_cues son copia fiel del D2
(celda 6 del notebook) para que las ablaciones sean comparables.
"""
import datetime as dt
import re

from minutes_agents.evaluate import norm

MONTHS = {'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,
          'julio':7,'agosto':8,'septiembre':9,'setiembre':9,'octubre':10,
          'noviembre':11,'diciembre':12}
WEEKDAYS = {'lunes':0,'martes':1,'miércoles':2,'miercoles':2,'jueves':3,
            'viernes':4,'sábado':5,'sabado':5,'domingo':6}
WORD_HOURS = {'una':1,'dos':2,'tres':3,'cuatro':4,'cinco':5,'seis':6,
              'siete':7,'ocho':8,'nueve':9,'diez':10,'once':11,'doce':12}

def inspect_evidence(tr, evidence_id):
    utterances = tr['utterances']
    pos = next((i for i,u in enumerate(utterances) if u['id']==evidence_id),None)
    if pos is None: return {'evidence_id':evidence_id,'exists':False}
    return {'evidence_id':evidence_id, 'exists':True,
            'cited':utterances[pos],
            'nearby':[{'id':u['id'],'speaker':u['speaker'],'text':u['text']}
                      for u in utterances[max(0,pos-1):min(len(utterances),pos+2)]],
            'participants':sorted({u['speaker'] for u in utterances})}

def resolve_deadline(tr, evidence_id, draft_value=None):
    evidence = inspect_evidence(tr,evidence_id)
    if not evidence['exists']:
        return {'evidence_id':evidence_id,'suggested':None,'reason':'ID no existe'}
    base = dt.date.fromisoformat(tr['meeting_date'])
    s = evidence['cited']['text'].lower()
    day = None
    if re.search(r'\bhoy\b',s): day = base
    elif re.search(r'\bpasado mañana\b',s): day = base+dt.timedelta(days=2)
    elif re.search(r'\bmañana\b',s) and not re.search(r'\b(?:de la|por la) mañana\b',s):
        day = base+dt.timedelta(days=1)
    else:
        monthmatch = re.search(r'\b(\d{1,2})\s+de\s+('+'|'.join(MONTHS)+r')\b',s)
        weekdaymatch = re.search(r'\b('+'|'.join(WEEKDAYS)+r')\s+(\d{1,2})\b',s)
        try:
            if monthmatch:
                d, m = int(monthmatch[1]), MONTHS[monthmatch[2]]
                day = dt.date(base.year,m,d)
                if day < base: day = dt.date(base.year+1,m,d)
            elif weekdaymatch:
                d=int(weekdaymatch[2]); day=dt.date(base.year,base.month,d)
                if day < base: day=dt.date(base.year+(base.month==12),(base.month%12)+1,d)
            else:
                wd = next((v for k,v in WEEKDAYS.items() if re.search(r'\b'+k+r'\b',s)),None)
                if wd is not None:
                    delta=(wd-base.weekday())%7
                    day=base+dt.timedelta(days=delta or 7)
        except ValueError:
            day=None
    tm = re.search(r'\b(?:a las|antes de las|a la|antes de la)\s+(\d{1,2})(?::(\d{2}))?\b',s)
    hour = int(tm[1]) if tm else None
    minute = int(tm[2] or 0) if tm else 0
    if hour is None:
        wm = re.search(r'\b(?:a las|antes de las|a la|antes de la)\s+('+'|'.join(WORD_HOURS)+r')\b',s)
        if wm: hour = WORD_HOURS[wm[1]]
    time_ambiguous = hour is not None and hour <= 12 and not re.search(r'\b(?:de la mañana|por la mañana|tarde|noche|mediodía)\b',s)
    if hour is not None and re.search(r'\b(?:tarde|noche)\b',s) and hour <= 11: hour += 12
    if time_ambiguous: hour = None
    if hour is not None and not (0<=hour<24): hour=None
    suggestion = day.isoformat() if day else None
    if suggestion and hour is not None: suggestion += f'T{hour:02d}:{minute:02d}'
    return {'evidence_id':evidence_id,'source_text':evidence['cited']['text'],
            'draft':draft_value, 'suggested':suggestion,
            'reason':('hora ambigua: solo día calculado' if time_ambiguous and suggestion else
                      'fecha explícita calculada' if suggestion else
                      'expresión relativa/ambigua: revisar contexto completo, no forzar fecha')}

def find_revision_cues(tr):
    # Evidencia recuperada de la transcripción; nunca de la rúbrica.
    pattern=r'\b(reemplaz\w*|descart\w*|rechaz\w*|pendiente|aprob\w*|qued\w* a cargo)\b'
    return [{'id':u['id'],'speaker':u['speaker'],'text':u['text']}
            for u in tr['utterances'] if re.search(pattern,u['text'].lower())]


COMMITMENT_PATTERN = r'\b(yo (puedo|me encargo|reviso|preparo|presento|armo|consolido|envio|entrego)|me encargo|me comprometo|queda a cargo|quedamos en|lo envio|voy a)\b'


def check_participant(tr, name):
    participants = sorted({u['speaker'] for u in tr['utterances']})
    n = norm(name)
    return {'name': name,
            'is_participant': name in participants,
            'mentioned_in_text': bool(n) and any(n in norm(u['text']) for u in tr['utterances']),
            'participants': participants}


def find_uncovered_commitments(tr, items):
    us = tr['utterances']
    cited = {i.get('evidence_id') for i in items if isinstance(i, dict)}
    out = []
    for k, u in enumerate(us):
        if not re.search(COMMITMENT_PATTERN, norm(u['text'])):
            continue
        near = {x['id'] for x in us[max(0, k - 1):k + 2]}
        if not (near & cited):
            out.append({'id': u['id'], 'speaker': u['speaker'], 'text': u['text']})
    return out


def _known_id(tr, eid):
    return isinstance(eid, str) and any(u['id'] == eid for u in tr['utterances'])


def _t_inspect(tr, call, ctx):
    eid = call.get('evidence_id')
    if not _known_id(tr, eid):
        return {'tool': 'inspect_evidence', 'error': f'evidence_id ausente o inexistente: {eid!r}'}
    return inspect_evidence(tr, eid)


def _t_deadline(tr, call, ctx):
    eid = call.get('evidence_id')
    if not _known_id(tr, eid):
        return {'tool': 'resolve_deadline', 'error': f'evidence_id ausente o inexistente: {eid!r}'}
    return resolve_deadline(tr, eid, call.get('draft_value'))


def _t_participant(tr, call, ctx):
    name = call.get('name')
    if not isinstance(name, str) or not name.strip():
        return {'tool': 'check_participant', 'error': 'name ausente o vacío'}
    return check_participant(tr, name)


TOOLS = {
    'inspect_evidence': _t_inspect,
    'find_revision_cues': lambda tr, call, ctx: find_revision_cues(tr),
    'resolve_deadline': _t_deadline,
    'check_participant': _t_participant,
    'find_uncovered_commitments': lambda tr, call, ctx: find_uncovered_commitments(tr, (ctx or {}).get('items', [])),
}
