"""Pruebas sin modelo de lo que permite usar el pipeline con cualquier reunión."""

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import ollama_client, pipeline  # noqa: E402
from src.retrieval import BM25, tokenize_stem  # noqa: E402
from src.transcript import Meeting, Utterance, load_meeting, to_canonical  # noqa: E402

SIMPLE = """Fecha: 2026-10-05
Tema: feria del colegio
Participantes: Ana Díaz (coordinadora), Luis Mora (logística)
Ausentes: Marta

Ana: ¿Hacemos la feria el sábado?
Luis: El sábado no hay salón.
seguimos viendo otra fecha.
[10:02] Ana: Entonces el domingo 11.
Pedro: Yo llevo las mesas.
"""


def write(text: str) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    f.write(text)
    f.close()
    return Path(f.name)


class TestLoader(unittest.TestCase):
    def test_simple_format(self):
        m = load_meeting(write(SIMPLE))
        self.assertEqual(m.date, date(2026, 10, 5))
        self.assertEqual([u.id for u in m.utterances], ["U001", "U002", "U003", "U004"])
        self.assertEqual(m.utterances[1].text, "El sábado no hay salón. seguimos viendo otra fecha.")  # continuación
        self.assertEqual(m.utterances[2].time, "10:02")
        self.assertEqual(m.absent_mentioned, ["Marta"])
        self.assertIn("Pedro", m.first_names())                     # habla, así que está presente
        self.assertTrue(any("Pedro" in w for w in m.warnings))

    def test_missing_date(self):
        text = SIMPLE.replace("Fecha: 2026-10-05\n", "")
        with self.assertRaises(ValueError):
            load_meeting(write(text))
        self.assertEqual(load_meeting(write(text), fecha="2026-10-05").date, date(2026, 10, 5))

    def test_repeated_first_names(self):
        m = load_meeting(write(SIMPLE), presentes="Ana Díaz, Ana Rojas, Luis Mora")
        labels = m.first_names()
        self.assertIn("Ana Díaz", labels)
        self.assertIn("Ana Rojas", labels)
        self.assertIn("Luis", labels)

    def test_canonical_roundtrip(self):
        m = load_meeting(write(SIMPLE))
        again = load_meeting(write(to_canonical(m)))
        self.assertEqual([(u.id, u.speaker, u.text) for u in m.utterances],
                         [(u.id, u.speaker, u.text) for u in again.utterances])
        self.assertEqual(m.date, again.date)

    def test_transcript_01_unchanged(self):
        m = load_meeting(Path(__file__).resolve().parents[3] / "pruebas" / "01_transcripcion_reunion_simulada.md")
        self.assertEqual(len(m.utterances), 69)
        self.assertEqual(list(m.first_names()), ["Camila", "Diego", "Fernanda", "Martín"])
        self.assertEqual(m.absent_mentioned, ["Paula", "Sergio", "Andrés"])
        self.assertEqual(m.warnings, [])


class TestAutoMode(unittest.TestCase):
    def setUp(self):
        self.utts = [Utterance(f"U{i:03d}", "", "Ana", f"Intervención número {i} sobre el proveedor {i % 7} y la sala {i % 5}.")
                     for i in range(1, 41)]
        self.meeting = Meeting(date(2026, 10, 5), "prueba", {"Ana Díaz": "coordinadora"}, [], self.utts)
        texts = [u.text for u in self.utts]
        self.bm, self.bms = BM25(texts), BM25(texts, tokenizer=tokenize_stem)

    def registry_with(self, n_items: int) -> pipeline.Registry:
        reg = pipeline.Registry(self.meeting)
        for k in range(n_items):
            uid = self.utts[k % 30].id
            reg.apply({"herramienta": "crear_decision", "id": f"D{k + 1}", "tema": f"proveedor {k % 7}",
                       "contenido": "contratar el proveedor con condiciones largas " * 3, "estado": "propuesta",
                       "reemplaza": [], "utterance_id": uid}, {uid})
        return reg

    def message_tokens(self, reg, shown, retrieved, new, prev):
        user = pipeline.build_user_message(self.meeting, reg, "decisiones", new, prev, retrieved, shown=shown)
        return pipeline.estimate_tokens(pipeline.DECISION_PROMPT) + pipeline.estimate_tokens(user)

    def test_short_meeting_uses_no_rag(self):
        reg = self.registry_with(5)
        new, prev = self.utts[32:40], self.utts[29:32]
        shown, retrieved, mode, _ = pipeline.plan_context(self.meeting, reg, "decisiones", 32, new, prev, "auto",
                                                          self.bm, self.bms, 1500)
        self.assertEqual(mode, "sin_rag")
        self.assertEqual(len(shown), 5)
        self.assertEqual(retrieved, [])

    def test_long_meeting_switches_to_rag_and_fits(self):
        reg = self.registry_with(300)   # registro enorme: no cabe en 8192 tokens
        new, prev = self.utts[32:40], self.utts[29:32]
        shown, retrieved, mode, notes = pipeline.plan_context(self.meeting, reg, "decisiones", 32, new, prev, "auto",
                                                              self.bm, self.bms, 1500)
        self.assertEqual(mode, "rag")
        self.assertLess(len(shown), 300)
        self.assertTrue(notes)
        limit = ollama_client.DEFAULT_OPTIONS["num_ctx"] - 1500
        self.assertLessEqual(self.message_tokens(reg, shown, retrieved, new, prev), limit)

    def test_other_modes_are_trimmed_to_fit(self):
        reg = self.registry_with(300)
        new, prev = self.utts[32:40], self.utts[29:32]
        shown, retrieved, mode, notes = pipeline.plan_context(self.meeting, reg, "decisiones", 32, new, prev,
                                                              "todo_el_pasado", self.bm, self.bms, 1500)
        limit = ollama_client.DEFAULT_OPTIONS["num_ctx"] - 1500
        self.assertLessEqual(self.message_tokens(reg, shown, retrieved, new, prev), limit)
        self.assertTrue(any("recorte" in n for n in notes))


if __name__ == "__main__":
    unittest.main()
