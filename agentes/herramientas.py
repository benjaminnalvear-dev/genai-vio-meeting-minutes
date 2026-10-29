"""Herramientas determinísticas.

Las funciones hasta `apply_safe_checks` están copiadas sin cambios del notebook de D2
(GenAI Constrained+Tool use/Ministral_Minutas_Colab.ipynb). `check_participante` es nueva en D3.
"""
import datetime as dt
import json
import re

# ---- Copiado de D2 (sin cambios) ----
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

def resolve_deadline(tr, evidence_id, draft_value):
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

def tool_bundle(tr, parsed):
    reports=[]
    for kind in ('decisions','tasks'):
        for item in parsed.get(kind,[]) if isinstance(parsed.get(kind),list) else []:
            if not isinstance(item,dict): continue
            report={'kind':kind,'id':item.get('id'),
                    'evidence':inspect_evidence(tr,item.get('evidence_id'))}
            if kind=='tasks':
                report['assignee_named_in_meeting'] = (item.get('assignee') is None or
                    any(str(item.get('assignee')).lower() in u['text'].lower() or
                        item.get('assignee') == u['speaker'] for u in tr['utterances']))
                if item.get('deadline') is not None:
                    report['deadline_check']=resolve_deadline(tr,item.get('evidence_id'),item.get('deadline'))
            reports.append(report)
    return reports

def revision_cues(tr):
    # Evidencia recuperada de la transcripción; nunca de la rúbrica.
    pattern=r'\b(reemplaz\w*|descart\w*|rechaz\w*|pendiente|aprob\w*|qued\w* a cargo)\b'
    return [{'id':u['id'],'speaker':u['speaker'],'text':u['text']}
            for u in tr['utterances'] if re.search(pattern,u['text'].lower())]

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


# ---- Nuevo en D3 ----
ABSENCE = r'\b(?:no (?:participa|está|esta|vino|asiste)|ausente|no asistió|no asistio)\b'


def check_participante(tr, nombre):
    """Dice si un nombre puede recibir una tarea: hablante, participante declarado, ausente o solo mencionado."""
    nombre = str(nombre or '').strip()
    if not nombre:
        return {'nombre': nombre, 'estado': 'vacío', 'puede_recibir_tarea': False}
    low = nombre.lower()
    speakers = sorted({u['speaker'] for u in tr['utterances']})
    if nombre in speakers or nombre in (tr.get('participants') or []):
        return {'nombre': nombre, 'estado': 'participante', 'puede_recibir_tarea': True,
                'hablantes': speakers}
    menciones = [{'id': u['id'], 'speaker': u['speaker'], 'text': u['text']}
                 for u in tr['utterances'] if low in u['text'].lower()]
    ausente = [m for m in menciones if re.search(ABSENCE, m['text'].lower())]
    estado = 'ausente' if ausente else ('mencionado, no participa' if menciones else 'no aparece')
    return {'nombre': nombre, 'estado': estado, 'puede_recibir_tarea': False,
            'menciones': menciones[:4], 'hablantes': speakers}
