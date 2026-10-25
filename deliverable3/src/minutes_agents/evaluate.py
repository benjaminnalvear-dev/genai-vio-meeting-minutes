"""Evaluador del D2 (celda 9), parametrizado en lugar de usar globales del notebook."""
import datetime as dt
import json
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher

from jsonschema import Draft202012Validator

from minutes_agents.schemas import make_schema


def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '').lower())
    s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+',' ',s).strip()

def recover_baseline(raw):
    # Recuperación SOLO para evaluar contenido: raw JSON/schema siguen reportados aparte.
    cleaned=re.sub(r'^\s*```(?:json)?\s*|\s*```\s*$','',raw.strip(),flags=re.I)
    try: obj=json.loads(cleaned)
    except json.JSONDecodeError: return None
    if not isinstance(obj,dict): return None
    return {'decisions':obj.get('decisions',obj.get('decisiones',[])),
            'tasks':obj.get('tasks',obj.get('tareas',[]))}

def comparable_date(value):
    if value is None: return None
    if not isinstance(value,str):return value
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',value): return dt.date.fromisoformat(value).isoformat()
        return dt.datetime.fromisoformat(value).isoformat(timespec='minutes')
    except ValueError: return value

def content_score(a,b,kind):
    field='statement' if kind=='decisions' else 'description'
    # La cláusula que anuncia un reemplazo no representa la decisión principal.
    main=re.split(r'\b(?:reemplaz\w*|sustituy\w*)\b',str(a.get(field,'')),maxsplit=1,flags=re.I)[0]
    x,y=norm(main),norm(b.get(field))
    seq=SequenceMatcher(None,x,y).ratio()
    sx,sy=set(x.split()),set(y.split())
    bow=2*len(sx&sy)/(len(sx)+len(sy)) if sx or sy else 0
    gold_coverage=len(sx&sy)/len(sy) if sy else 0
    main=max(seq,bow,gold_coverage)
    topic=SequenceMatcher(None,norm(a.get('topic')),norm(b.get('topic'))).ratio() if kind=='decisions' else 0
    evid=int(a.get('evidence_id')==b.get('evidence_id'))
    return (0.70*main+0.15*topic+0.15*evid) if kind=='decisions' else (0.80*main+0.20*evid)

def match_items(pred,gold,kind):
    candidates=[]
    for i,p in enumerate(pred):
        if not isinstance(p,dict):continue
        for j,g in enumerate(gold):
            score=content_score(p,g,kind)
            if score>=0.55: candidates.append((score,i,j))
    used_p,used_g=set(),set(); pairs=[]
    for score,i,j in sorted(candidates,reverse=True):
        if i not in used_p and j not in used_g:
            used_p.add(i);used_g.add(j);pairs.append((pred[i],gold[j],score))
    return pairs

def evaluate_arm(outputs, transcripts, gold, is_baseline, arm):
    totals=Counter()
    per=[]
    for mid in sorted(outputs):
        out=outputs[mid]; obj=out.get('parsed')
        tr=transcripts[mid]; g=gold[mid]
        totals['meetings']+=1
        totals['seconds']+=out['seconds']
        totals['json_valid']+=int(isinstance(obj,dict))
        schema=make_schema(tr)
        totals['schema_valid']+=int(isinstance(obj,dict) and Draft202012Validator(schema).is_valid(obj))
        p=(recover_baseline(out['raw']) if is_baseline else obj)
        p=p if isinstance(p,dict) else {}
        totals['content_recovered']+=int(bool(p))
        for kind in ('decisions','tasks'):
            predicted=p.get(kind,[])
            predicted=predicted if isinstance(predicted,list) else []
            expected=g[kind]
            pairs=match_items(predicted,expected,kind)
            totals[kind+'_pred']+=len(predicted)
            totals[kind+'_gold']+=len(expected)
            totals[kind+'_tp']+=len(pairs)
            valid_ids={u['id'] for u in tr['utterances']}
            totals['cites']+=sum(isinstance(x,dict) for x in predicted)
            totals['cites_existing']+=sum(isinstance(x,dict) and x.get('evidence_id') in valid_ids for x in predicted)
            for x,y,score in pairs:
                totals['matched']+=1
                totals['state_right']+=int(x.get('state')==y.get('state'))
                totals['evidence_right']+=int(x.get('evidence_id')==y.get('evidence_id'))
                if kind=='tasks':
                    totals['tasks_matched']+=1
                    totals['assignee_right']+=int(x.get('assignee')==y.get('assignee'))
                    totals['deadline_right']+=int(comparable_date(x.get('deadline'))==comparable_date(y.get('deadline')))
        per.append({'meeting_id':mid,'seconds':out['seconds'],
                    'decisions_pred':len(p.get('decisions',[])) if isinstance(p.get('decisions',[]),list) else 0,
                    'tasks_pred':len(p.get('tasks',[])) if isinstance(p.get('tasks',[]),list) else 0})
    result={'arm':arm,'meetings':totals['meetings'],'seconds_total':round(totals['seconds'],1),
            'json_valid':f"{totals['json_valid']}/{totals['meetings']}",
            'schema_valid':f"{totals['schema_valid']}/{totals['meetings']}",
            'content_recovered':f"{totals['content_recovered']}/{totals['meetings']}",
            'state_accuracy_matched':round(totals['state_right']/totals['matched'],3) if totals['matched'] else None,
            'assignee_accuracy_matched':round(totals['assignee_right']/totals['tasks_matched'],3) if totals['tasks_matched'] else None,
            'deadline_accuracy_matched':round(totals['deadline_right']/totals['tasks_matched'],3) if totals['tasks_matched'] else None,
            'evidence_exact_matched':round(totals['evidence_right']/totals['matched'],3) if totals['matched'] else None,
            'evidence_id_exists':f"{totals['cites_existing']}/{totals['cites']}",
            'per_meeting':per,
            'note':'Emparejamiento aproximado automático; revisar errores manualmente.'}
    for kind in ('decisions','tasks'):
        n=totals[kind+'_tp']; pred=totals[kind+'_pred']; expected=totals[kind+'_gold']
        prec=n/pred if pred else (1.0 if not expected else 0.0)
        recall=n/expected if expected else 1.0
        f1=2*prec*recall/(prec+recall) if prec+recall else 0.0
        result[kind]={'matched':n,'predicted':pred,'gold':expected,
                      'precision':round(prec,3),'recall':round(recall,3),'f1':round(f1,3)}
    return result
