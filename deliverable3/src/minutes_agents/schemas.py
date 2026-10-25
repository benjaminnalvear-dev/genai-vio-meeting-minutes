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


def decision_item_schema(tr):
    return make_schema(tr)['properties']['decisions']['items']


def task_item_schema(tr):
    return make_schema(tr)['properties']['tasks']['items']


PROBLEMS = ['evidence_not_supporting', 'wrong_state', 'wrong_deadline',
            'wrong_assignee', 'merged_items', 'missing_item']


def verdict_schema(item_ids):
    return {'type': 'object', 'additionalProperties': False,
            'required': ['item_id', 'ok', 'problem', 'detail'],
            'properties': {
                'item_id': {'type': 'string', 'enum': list(item_ids) + ['NEW']},
                'ok': {'type': 'boolean'},
                'problem': {'type': ['string', 'null'], 'enum': PROBLEMS + [None]},
                'detail': {'type': 'string'}}}


def step_schema(tr, tools, output, *, allow_tools, with_thought):
    ids = [u['id'] for u in tr['utterances']]
    call = {'type': 'object', 'additionalProperties': False,
            'required': ['tool', 'evidence_id', 'name'],
            'properties': {
                'tool': {'type': 'string', 'enum': list(tools)},
                'evidence_id': {'type': ['string', 'null'], 'enum': ids + [None]},
                'name': nullable_string()}}
    tool_calls = {'type': 'array', 'items': call}
    if not allow_tools:
        tool_calls['maxItems'] = 0
    props = {}
    if with_thought:
        props['thought'] = {'type': 'string'}
    props['action'] = {'type': 'string',
                       'enum': ['call_tools', 'finish'] if allow_tools else ['finish']}
    props['tool_calls'] = tool_calls
    props.update(output)
    return {'type': 'object', 'additionalProperties': False,
            'required': list(props), 'properties': props}
