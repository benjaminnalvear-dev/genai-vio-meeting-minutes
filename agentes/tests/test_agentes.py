"""Pruebas sin Ollama: evaluador, herramientas y enrutamiento del grafo con un modelo falso."""
import io
import json
import unittest
import zipfile
from unittest import mock

from agentes import grafo
from agentes.datos import RAIZ, load_split
from agentes.evaluador import evaluate
from agentes.herramientas import check_participante

TEST_TR, TEST_GOLD = load_split('test')
ZIP_D2 = RAIZ / 'GenAI Constrained+Tool use' / 'minutas_resultados_test.zip'


class EvaluadorReproduceD2(unittest.TestCase):
    def test_tabla_d2(self):
        with zipfile.ZipFile(ZIP_D2) as z:
            def arm(nombre):
                return {mid: json.loads(z.read(f'{mid}_{nombre}.json')) for mid in TEST_TR}
            esperado = {'baseline': (0.477, 0.667), 'structured': (0.559, 0.709), 'combined_v2': (0.667, 0.716)}
            for nombre, (fd, ft) in esperado.items():
                r = evaluate('baseline' if nombre == 'baseline' else nombre, arm(nombre), TEST_TR, TEST_GOLD)
                self.assertEqual((r['decisions']['f1'], r['tasks']['f1']), (fd, ft), nombre)


class Herramientas(unittest.TestCase):
    def test_check_participante(self):
        tr = TEST_TR['M01']
        self.assertTrue(check_participante(tr, 'Speaker 02')['puede_recibir_tarea'])
        paula = check_participante(tr, 'Paula')
        self.assertEqual(paula['estado'], 'ausente')
        self.assertFalse(paula['puede_recibir_tarea'])
        self.assertEqual(check_participante(tr, 'Marketing')['estado'], 'mencionado, no participa')


def modelo_falso(messages, schema=None):
    """Siempre pide una herramienta si puede; el auditor siempre marca el primer ítem."""
    sistema = messages[0]['content']
    tr = TEST_TR['M01']
    if 'anyOf' in schema:
        variante = schema['anyOf'][0]['properties']
        tool = variante['tool']['enum'][0]
        args = {'evidence_id': 'u05'} if 'evidence_id' in variante['args']['properties'] else (
            {'nombre': 'Paula'} if 'nombre' in variante['args']['properties'] else {})
        a = {'action': 'tool', 'motivo': 'prueba', 'tool': tool, 'args': args}
    elif 'RASTREADOR' in sistema:
        a = {'action': 'finish', 'output': {'topics': [
            {'id': 'T1', 'nombre': 'Fecha', 'utterance_ids': ['u05', 'u31'], 'tipo': 'decision', 'tiene_revision': True},
            {'id': 'T2', 'nombre': 'Cámara', 'utterance_ids': ['u36'], 'tipo': 'ambos', 'tiene_revision': False}]}}
    elif 'DECISIONES' in sistema:
        a = {'action': 'finish', 'output': {'decisions': [
            {'id': 'd01', 'topic': 'x', 'statement': 'a', 'state': 'superseded', 'condition': None, 'supersedes': None, 'evidence_id': 'u05'},
            {'id': 'd02', 'topic': 'x', 'statement': 'b', 'state': 'final', 'condition': None, 'supersedes': 'd01', 'evidence_id': 'u31'}]}}
    elif 'TAREAS' in sistema:
        a = {'action': 'finish', 'output': {'tasks': [
            {'id': 't01', 'description': 'c', 'assignee': 'Speaker 02', 'deadline': 'mañana', 'condition': None, 'state': 'final', 'evidence_id': 'u08'}]}}
    else:
        ids = schema['properties']['output']['properties']['veredictos']['items']['properties']['id']['enum']
        a = {'action': 'finish', 'output': {'veredictos': [{'id': ids[0], 'veredicto': 'revisar', 'motivo': 'm'}]}}
    return {'raw': json.dumps(a), 'parsed': a, 'seconds': 0.01, 'eval_count': 1}


@mock.patch.object(grafo, 'inference', modelo_falso)
class Enrutamiento(unittest.TestCase):
    def correr(self, condicion):
        res, traza = grafo.correr(TEST_TR['M01'], condicion)
        return res, traza.eventos

    def test_full(self):
        res, ev = self.correr('full')
        # dos temas con decisiones, IDs renumerados y supersedes reescrito entre temas
        self.assertEqual([d['id'] for d in res['parsed']['decisions']], ['d01', 'd02', 'd03', 'd04'])
        self.assertEqual(res['parsed']['decisions'][3]['supersedes'], 'd03')
        # apply_safe_checks de D2 limpia la fecha no ISO
        self.assertIsNone(res['parsed']['tasks'][0]['deadline'])
        # el auditor siempre marca algo: se corta en MAX_RONDAS
        self.assertEqual(res['rondas'], grafo.MAX_RONDAS)
        self.assertTrue(any(e['accion'] == 'tope_de_rondas' for e in ev))
        # presupuesto de herramientas por invocación de agente
        for agente, tope in grafo.MAX_TOOLS.items():
            usos = [e for e in ev if e['agente'] == agente and e['accion'] == 'tool']
            invocaciones = sum(1 for e in ev if e['agente'] == agente and e['accion'] == 'finish')
            self.assertLessEqual(len(usos), tope * invocaciones, agente)
        handoffs = [e['a'] for e in ev if e['accion'] == 'handoff']
        self.assertIn('decisiones[T1]', handoffs)
        self.assertIn('tareas', handoffs)

    def test_sin_auditor(self):
        _, ev = self.correr('sin_auditor')
        self.assertFalse(any(e['agente'] == 'auditor' for e in ev))

    def test_sin_tools(self):
        _, ev = self.correr('sin_tools')
        self.assertFalse(any(e['accion'] == 'tool' for e in ev))

    def test_sin_rastreador(self):
        res, ev = self.correr('sin_rastreador')
        self.assertEqual(len(res['temas']), 1)
        self.assertFalse(any(e['agente'] == 'rastreador' and e['accion'] == 'finish' for e in ev))

    def test_sin_fewshot_quita_ejemplos(self):
        for nombre in grafo.HERRAMIENTAS:
            con, sin = grafo.cargar_prompt(nombre), grafo.cargar_prompt(nombre, fewshot=False)
            self.assertIn('EJEMPLO', con)
            self.assertNotIn('EJEMPLO', sin)
            self.assertTrue(con.startswith(sin[:200]))


if __name__ == '__main__':
    unittest.main()
