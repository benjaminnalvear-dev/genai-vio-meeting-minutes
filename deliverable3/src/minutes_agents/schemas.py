"""Esquema JSON de las minutas (copiado del D2, celda 4)."""

STATES = ['final', 'superseded', 'rejected', 'pending']

def nullable_string(): return {'type': ['string', 'null']}

def make_schema(tr):
    evidence_ids = [u['id'] for u in tr['utterances']]
    decision = {
      'type': 'object', 'additionalProperties': False,
      'required': ['id','topic','statement','state','condition','supersedes','evidence_id'],
      'properties': {
        'id': {'type':'string'}, 'topic': {'type':'string'}, 'statement': {'type':'string'},
        'state': {'type':'string','enum':STATES}, 'condition': nullable_string(),
        'supersedes': nullable_string(), 'evidence_id': {'type':'string','enum':evidence_ids}
      }
    }
    task = {
      'type': 'object', 'additionalProperties': False,
      'required': ['id','description','assignee','deadline','condition','state','evidence_id'],
      'properties': {
        'id': {'type':'string'}, 'description': {'type':'string'},
        'assignee': nullable_string(),
        'deadline': nullable_string(), 'condition': nullable_string(),
        'state': {'type':'string','enum':STATES},
        'evidence_id': {'type':'string','enum':evidence_ids}
      }
    }
    return {'type':'object','additionalProperties':False,'required':['decisions','tasks'],
            'properties': {'decisions':{'type':'array','items':decision},
                           'tasks':{'type':'array','items':task}}}
