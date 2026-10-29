"""Esquemas JSON.

`make_schema` es el esquema del acta de D2, copiado sin cambios. Los esquemas de acción son nuevos en D3:
cada paso de un agente devuelve {"action": "tool", ...} o {"action": "finish", ...} y el grafo enruta según eso.
"""

# ---- Copiado de D2 (sin cambios) ----
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


# ---- Nuevo en D3: salidas y acciones de los agentes ----
def _obj(props, required=None):
    return {'type': 'object', 'additionalProperties': False,
            'required': list(required or props), 'properties': props}


def ids_de(tr):
    return [u['id'] for u in tr['utterances']]


def salida_rastreador(tr):
    tema = _obj({'id': {'type': 'string'}, 'nombre': {'type': 'string'},
                 'utterance_ids': {'type': 'array', 'items': {'type': 'string', 'enum': ids_de(tr)}},
                 'tipo': {'type': 'string', 'enum': ['decision', 'tarea', 'ambos']},
                 'tiene_revision': {'type': 'boolean'}})
    return _obj({'topics': {'type': 'array', 'items': tema}})


def salida_decisiones(tr):
    return _obj({'decisions': make_schema(tr)['properties']['decisions']})


def salida_tareas(tr):
    return _obj({'tasks': make_schema(tr)['properties']['tasks']})


def salida_auditor(item_ids):
    veredicto = _obj({'id': {'type': 'string', 'enum': item_ids},
                      'veredicto': {'type': 'string', 'enum': ['ok', 'revisar']},
                      'motivo': {'type': 'string'}})
    return _obj({'veredictos': {'type': 'array', 'items': veredicto}})


def args_herramienta(nombre, tr):
    if nombre in ('inspect_evidence', 'resolve_deadline'):
        return _obj({'evidence_id': {'type': 'string', 'enum': ids_de(tr)}})
    if nombre == 'check_participante':
        return _obj({'nombre': {'type': 'string'}})
    if nombre == 'revision_cues':
        return _obj({})
    raise KeyError(nombre)


def accion(salida, herramientas, tr):
    """Esquema de un paso: llamar una de `herramientas` o terminar con `salida`.

    Con `herramientas` vacío (presupuesto agotado o condición sin_tools) solo queda `finish`.
    `motivo` va antes de `tool` para que el modelo explique por qué la llama.
    """
    finish = _obj({'action': {'type': 'string', 'enum': ['finish']}, 'output': salida})
    if not herramientas:
        return finish
    tools = [_obj({'action': {'type': 'string', 'enum': ['tool']}, 'motivo': {'type': 'string'},
                   'tool': {'type': 'string', 'enum': [h]}, 'args': args_herramienta(h, tr)})
             for h in herramientas]
    return {'anyOf': tools + [finish]}
