"""Grafo multi-agente de D3 con LangGraph.

Rastreador → (Send por tema) Decisiones + Tareas → unir → Auditor ⇄ especialistas → finalizar.
Cada agente es un subgrafo ReAct: en cada paso el modelo devuelve una acción restringida por esquema,
{"action": "tool"} o {"action": "finish"}, y una arista condicional decide si se ejecuta la herramienta
o se entrega la salida.
"""
import json
import re
import time
from pathlib import Path
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from . import esquemas as E
from .datos import transcript_text
from .herramientas import (apply_safe_checks, check_participante, inspect_evidence, resolve_deadline,
                           revision_cues, tool_bundle)
from .modelo import inference

PROMPTS = Path(__file__).resolve().parent / 'prompts'
CONDICIONES = ('full', 'sin_fewshot', 'sin_tools', 'sin_auditor', 'sin_rastreador')
HERRAMIENTAS = {'rastreador': ['revision_cues'],
                'decisiones': ['inspect_evidence', 'revision_cues'],
                'tareas': ['resolve_deadline', 'check_participante'],
                'auditor': ['inspect_evidence']}
MAX_TOOLS = {'rastreador': 1, 'decisiones': 3, 'tareas': 3, 'auditor': 3}
MAX_RONDAS = 2


def cargar_prompt(nombre, fewshot=True):
    texto = (PROMPTS / f'{nombre}.md').read_text(encoding='utf-8')
    if not fewshot:
        texto = re.sub(r'<!-- EJEMPLOS:INICIO -->.*?<!-- EJEMPLOS:FIN -->\n?', '', texto, flags=re.S)
    return texto.strip()


def ejecutar_herramienta(tr, nombre, args):
    if nombre == 'inspect_evidence':
        return inspect_evidence(tr, args.get('evidence_id'))
    if nombre == 'resolve_deadline':
        return resolve_deadline(tr, args.get('evidence_id'), None)
    if nombre == 'check_participante':
        return check_participante(tr, args.get('nombre'))
    if nombre == 'revision_cues':
        return revision_cues(tr)
    raise KeyError(nombre)


class Traza:
    """Registro ordenado de todo lo que pasa entre agentes; se guarda como JSONL."""

    def __init__(self, en_vivo=False):
        self.eventos, self.en_vivo = [], en_vivo
        self.llamadas, self.segundos, self.tokens = 0, 0.0, 0

    def modelo(self, r):
        self.llamadas += 1
        self.segundos += r['seconds']
        self.tokens += (r.get('eval_count') or 0)

    def __call__(self, **evento):
        evento = {'paso': len(self.eventos) + 1, **evento}
        self.eventos.append(evento)
        if self.en_vivo:
            print(formatear(evento), flush=True)

    def guardar(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in self.eventos),
                        encoding='utf-8')


def formatear(e):
    quien = e['agente'].upper() + (f"[{e['tema']}]" if e.get('tema') else '')
    accion = e['accion']
    if accion == 'tool':
        res = json.dumps(e.get('resultado'), ensure_ascii=False)
        return (f"{e['paso']:>3} {quien} → {e['tool']}({json.dumps(e['args'], ensure_ascii=False)})"
                f"  · {e.get('motivo', '')}\n      ← {res[:220]}{'…' if len(res) > 220 else ''}")
    if accion == 'handoff':
        return f"{e['paso']:>3} {quien} ⇒ {e['a']}: {json.dumps(e['contenido'], ensure_ascii=False)[:300]}"
    if accion == 'finish':
        return f"{e['paso']:>3} {quien} ✓ entrega: {json.dumps(e['salida'], ensure_ascii=False)[:300]}"
    return f"{e['paso']:>3} {quien} · {accion}: {json.dumps(e.get('detalle'), ensure_ascii=False)[:300]}"


# ---------------------------------------------------------------------------
# Subgrafo ReAct de un agente
# ---------------------------------------------------------------------------
class EstadoAgente(TypedDict):
    mensajes: list
    usadas: int
    pendiente: dict | None
    salida: dict | None
    cache: dict


def correr_agente(nombre, tr, sistema, usuario, salida_schema, herramientas, traza, tema=None, ronda=0):
    """Corre un agente hasta que entrega. Devuelve su `output` (o None si el modelo no produjo JSON)."""

    def decidir(s):
        disponibles = herramientas if s['usadas'] < MAX_TOOLS[nombre] else []
        r = inference(s['mensajes'], E.accion(salida_schema, disponibles, tr))
        traza.modelo(r)
        a = r['parsed']
        if not isinstance(a, dict):
            traza(agente=nombre, tema=tema, ronda=ronda, accion='error',
                  detalle={'raw': r['raw'][-400:], 'ms': int(r['seconds'] * 1000)})
            return {'pendiente': None, 'salida': None}
        mensajes = s['mensajes'] + [{'role': 'assistant', 'content': r['raw']}]
        if a.get('action') == 'tool':
            return {'mensajes': mensajes, 'pendiente': {**a, 'ms': int(r['seconds'] * 1000),
                                                        'tokens': r.get('eval_count')}}
        traza(agente=nombre, tema=tema, ronda=ronda, accion='finish', salida=a['output'],
              ms=int(r['seconds'] * 1000), tokens=r.get('eval_count'))
        return {'mensajes': mensajes, 'pendiente': None, 'salida': a['output']}

    def herramienta(s):
        a = s['pendiente']
        clave = a['tool'] + json.dumps(a['args'], sort_keys=True)
        repetida = clave in s['cache']
        resultado = s['cache'][clave] if repetida else ejecutar_herramienta(tr, a['tool'], a['args'])
        traza(agente=nombre, tema=tema, ronda=ronda, accion='tool', motivo=a.get('motivo'), tool=a['tool'],
              args=a['args'], resultado=resultado, repetida=repetida, ms=a['ms'], tokens=a['tokens'])
        nota = ' (ya la habías consultado)' if repetida else ''
        restantes = MAX_TOOLS[nombre] - s['usadas'] - 1
        msg = (f"RESULTADO DE {a['tool']}{nota}:\n{json.dumps(resultado, ensure_ascii=False)}\n"
               + (f"Te quedan {restantes} llamadas a herramientas. Llama otra o entrega con finish."
                  if restantes > 0 else 'No te quedan herramientas: entrega con finish.'))
        return {'mensajes': s['mensajes'] + [{'role': 'user', 'content': msg}],
                'usadas': s['usadas'] + 1, 'pendiente': None, 'cache': {**s['cache'], clave: resultado}}

    g = StateGraph(EstadoAgente)
    g.add_node('decidir', decidir)
    g.add_node('herramienta', herramienta)
    g.add_edge(START, 'decidir')
    g.add_conditional_edges('decidir', lambda s: 'herramienta' if s['pendiente'] else END,
                            ['herramienta', END])
    g.add_edge('herramienta', 'decidir')
    final = g.compile().invoke({'mensajes': [{'role': 'system', 'content': sistema},
                                             {'role': 'user', 'content': usuario}],
                                'usadas': 0, 'pendiente': None, 'salida': None, 'cache': {}},
                               {'recursion_limit': 4 * MAX_TOOLS[nombre] + 4})
    return final['salida']


# ---------------------------------------------------------------------------
# Grafo principal
# ---------------------------------------------------------------------------
def _fusionar(a, b):
    return {**(a or {}), **(b or {})}


class Estado(TypedDict):
    tr: dict
    condicion: str
    temas: list
    decisiones_por_tema: Annotated[dict, _fusionar]
    tareas: list
    acta: dict
    origen: dict
    feedback: dict
    ronda: int
    resultado: dict
    tema: dict  # solo en los Send a Decisiones


def lineas(tr, ids):
    pos = {u['id']: u for u in tr['utterances']}
    return '\n'.join(f"{i} | {pos[i]['speaker']}: {pos[i]['text']}" for i in ids if i in pos)


def con_feedback(usuario, previa, observaciones):
    if not observaciones:
        return usuario
    return (usuario + '\n\nTU SALIDA ANTERIOR:\n' + json.dumps(previa, ensure_ascii=False)
            + '\n\nOBSERVACIONES DEL AUDITOR (ítems a revisar):\n'
            + json.dumps(observaciones, ensure_ascii=False)
            + '\nCorrige, elimina o mantiene cada ítem observado y devuelve la lista completa.')


def construir(traza):
    def herramientas(nombre, condicion):
        return [] if condicion == 'sin_tools' else HERRAMIENTAS[nombre]

    def rastreador(s):
        tr = s['tr']
        if s['condicion'] == 'sin_rastreador':
            temas = [{'id': 'T1', 'nombre': 'Reunión completa', 'utterance_ids': E.ids_de(tr),
                      'tipo': 'ambos', 'tiene_revision': True}]
            traza(agente='rastreador', accion='omitido', detalle='ablación sin_rastreador: un solo tema')
            return {'temas': temas, 'ronda': 0, 'feedback': {}}
        salida = correr_agente('rastreador', tr, cargar_prompt('rastreador', s['condicion'] != 'sin_fewshot'),
                               transcript_text(tr) + '\n\nTAREA: agrupa las intervenciones en temas.',
                               E.salida_rastreador(tr), herramientas('rastreador', s['condicion']), traza)
        temas = (salida or {}).get('topics') or []
        if not temas:  # sin temas no hay nada que repartir: se trata como una sola unidad
            temas = [{'id': 'T1', 'nombre': 'Reunión completa', 'utterance_ids': E.ids_de(tr),
                      'tipo': 'ambos', 'tiene_revision': True}]
        return {'temas': temas, 'ronda': 0, 'feedback': {}}

    def repartir(s):
        envios = []
        for t in s['temas']:
            if t['tipo'] in ('decision', 'ambos'):
                envios.append(Send('decisiones', {**s, 'tema': t}))
                traza(agente='rastreador', accion='handoff', a=f"decisiones[{t['id']}]",
                      contenido={'tema': t['nombre'], 'utterance_ids': t['utterance_ids'],
                                 'tiene_revision': t['tiene_revision']})
        envios.append(Send('tareas', s))
        traza(agente='rastreador', accion='handoff', a='tareas',
              contenido=[{'id': t['id'], 'nombre': t['nombre'], 'tipo': t['tipo']} for t in s['temas']])
        return envios

    def decisiones(s):
        tr, t = s['tr'], s['tema']
        obs = (s.get('feedback') or {}).get('decisiones', {}).get(t['id'])
        previa = (s.get('decisiones_por_tema') or {}).get(t['id'])
        usuario = (transcript_text(tr) + f"\n\nTEMA ASIGNADO POR EL RASTREADOR: {t['nombre']} ({t['id']})\n"
                   + 'Intervenciones del tema:\n' + lineas(tr, t['utterance_ids'])
                   + ('\nEl rastreador detectó alternativas, cambios o asuntos pendientes en este tema.'
                      if t.get('tiene_revision') else '')
                   + '\nExtrae solo las decisiones de este tema.')
        salida = correr_agente('decisiones', tr, cargar_prompt('decisiones', s['condicion'] != 'sin_fewshot'),
                               con_feedback(usuario, previa, obs), E.salida_decisiones(tr),
                               herramientas('decisiones', s['condicion']), traza, tema=t['id'],
                               ronda=s.get('ronda', 0))
        items = (salida or {}).get('decisions')
        if items is None:  # salida inválida: se conserva la anterior
            items = previa or []
        return {'decisiones_por_tema': {t['id']: items}}

    def tareas(s):
        tr = s['tr']
        obs = (s.get('feedback') or {}).get('tareas')
        mapa = '\n'.join(f"- {t['id']} {t['nombre']} ({t['tipo']}): {', '.join(t['utterance_ids'])}"
                         for t in s['temas'])
        usuario = (transcript_text(tr) + '\n\nMAPA DE TEMAS DEL RASTREADOR:\n' + mapa
                   + '\nExtrae todas las tareas de la reunión.')
        salida = correr_agente('tareas', tr, cargar_prompt('tareas', s['condicion'] != 'sin_fewshot'),
                               con_feedback(usuario, s.get('tareas'), obs), E.salida_tareas(tr),
                               herramientas('tareas', s['condicion']), traza, ronda=s.get('ronda', 0))
        items = (salida or {}).get('tasks')
        return {'tareas': items if items is not None else (s.get('tareas') or [])}

    def unir(s):
        decs, origen = [], {}
        for t in s['temas']:
            locales = s['decisiones_por_tema'].get(t['id'], [])
            mapa = {}
            for d in locales:
                mapa[d.get('id')] = f'd{len(decs) + 1:02d}'
                origen[mapa[d.get('id')]] = ['decisiones', t['id'], d.get('id')]
                decs.append(dict(d, id=mapa[d.get('id')]))
            for d in decs[len(decs) - len(locales):]:
                d['supersedes'] = mapa.get(d.get('supersedes'))
        tasks = []
        for x in s.get('tareas') or []:
            gid = f't{len(tasks) + 1:02d}'
            origen[gid] = ['tareas', None, x.get('id')]
            tasks.append(dict(x, id=gid))
        acta = {'decisions': decs, 'tasks': tasks}
        traza(agente='sistema', accion='unir', detalle={'decisiones': len(decs), 'tareas': len(tasks)})
        return {'acta': acta, 'origen': origen}

    def auditor(s):
        tr, acta = s['tr'], s['acta']
        ids = [x['id'] for x in acta['decisions'] + acta['tasks']]
        ronda = s.get('ronda', 0) + 1
        if not ids:
            return {'ronda': ronda, 'feedback': {}}
        usuario = transcript_text(tr) + '\n\nACTA A AUDITAR:\n' + json.dumps(acta, ensure_ascii=False)
        if s['condicion'] != 'sin_tools':
            informe = [{'id': r['id'], 'cita': (r['evidence'].get('cited') or {}).get('text'),
                        **({'responsable_en_reunion': r['assignee_named_in_meeting']}
                           if 'assignee_named_in_meeting' in r else {}),
                        **({'fecha_herramienta': r['deadline_check'].get('suggested'),
                            'nota_fecha': r['deadline_check'].get('reason')} if 'deadline_check' in r else {})}
                       for r in tool_bundle(tr, acta)]
            usuario += '\n\nINFORME DE HERRAMIENTAS:\n' + json.dumps(informe, ensure_ascii=False)
        usuario += f'\nDa un veredicto para cada uno de estos ítems: {", ".join(ids)}.'
        salida = correr_agente('auditor', tr, cargar_prompt('auditor', s['condicion'] != 'sin_fewshot'),
                               usuario, E.salida_auditor(ids), herramientas('auditor', s['condicion']),
                               traza, ronda=ronda)
        items = {x['id']: x for x in acta['decisions'] + acta['tasks']}
        feedback = {'decisiones': {}, 'tareas': []}
        for v in (salida or {}).get('veredictos') or []:
            if v['veredicto'] != 'revisar' or v['id'] not in s['origen']:
                continue
            agente, tema, local = s['origen'][v['id']]
            obs = {'id': local, 'item': dict(items[v['id']], id=local), 'motivo': v['motivo']}
            if agente == 'decisiones':
                feedback['decisiones'].setdefault(tema, []).append(obs)
            else:
                feedback['tareas'].append(obs)
        if not feedback['decisiones'] and not feedback['tareas']:
            feedback = {}
        return {'ronda': ronda, 'feedback': feedback}

    def tras_auditor(s):
        fb = s.get('feedback') or {}
        if not fb or s['ronda'] >= MAX_RONDAS:
            traza(agente='auditor', accion='aprobar' if not fb else 'tope_de_rondas',
                  detalle={'ronda': s['ronda'], 'pendientes': fb})
            return ['finalizar']
        envios = []
        temas = {t['id']: t for t in s['temas']}
        for tema, obs in fb.get('decisiones', {}).items():
            envios.append(Send('decisiones', {**s, 'tema': temas[tema]}))
            traza(agente='auditor', accion='handoff', a=f'decisiones[{tema}]', contenido=obs)
        if fb.get('tareas'):
            envios.append(Send('tareas', s))
            traza(agente='auditor', accion='handoff', a='tareas', contenido=fb['tareas'])
        return envios

    def finalizar(s):
        res = apply_safe_checks(s['tr'], {'parsed': s['acta']})
        traza(agente='sistema', accion='finalizar',
              detalle={'acciones_mecanicas': res.get('mechanical_actions'), 'rondas': s.get('ronda', 0)})
        return {'resultado': res}

    g = StateGraph(Estado)
    for nombre, fn in (('rastreador', rastreador), ('decisiones', decisiones), ('tareas', tareas),
                       ('unir', unir), ('auditor', auditor), ('finalizar', finalizar)):
        g.add_node(nombre, fn)
    g.add_edge(START, 'rastreador')
    g.add_conditional_edges('rastreador', repartir, ['decisiones', 'tareas'])
    g.add_edge('decisiones', 'unir')
    g.add_edge('tareas', 'unir')
    g.add_conditional_edges('unir', lambda s: 'finalizar' if s['condicion'] == 'sin_auditor' else 'auditor',
                            ['auditor', 'finalizar'])
    g.add_conditional_edges('auditor', tras_auditor, ['decisiones', 'tareas', 'finalizar'])
    g.add_edge('finalizar', END)
    return g.compile()


def correr(tr, condicion='full', en_vivo=False):
    """Corre el sistema sobre una reunión. Devuelve (resultado para el evaluador, traza)."""
    if condicion not in CONDICIONES:
        raise ValueError(f'condición desconocida: {condicion}')
    traza = Traza(en_vivo)
    t0 = time.monotonic()
    final = construir(traza).invoke({'tr': tr, 'condicion': condicion, 'decisiones_por_tema': {}},
                                    {'max_concurrency': 1, 'recursion_limit': 100})
    acta = final['resultado']['parsed']
    resultado = {'raw': json.dumps(final['acta'], ensure_ascii=False), 'parsed': acta,
                 'seconds': round(time.monotonic() - t0, 2), 'segundos_modelo': round(traza.segundos, 2),
                 'llamadas': traza.llamadas, 'tokens_generados': traza.tokens, 'rondas': final.get('ronda', 0),
                 'temas': final['temas'], 'mechanical_actions': final['resultado'].get('mechanical_actions')}
    return resultado, traza
