"""El corrector automático debe reproducir la auditoría manual del D1 (pruebas/01_auditoria_ministral.md)."""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))

from src.score import load_acta, load_gold, score  # noqa: E402
from src.transcript import load_meeting  # noqa: E402


class TestScoreD1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        meeting = load_meeting(REPO / "pruebas" / "01_transcripcion_reunion_simulada.md")
        acta, valid, raw = load_acta(REPO / "pruebas" / "01_salida_ministral_8k.md")
        cls.m = score(acta, valid, load_gold(HERE / "gold" / "01_gold.json"), meeting, "D1", raw).metrics

    def test_matches_manual_audit(self):
        m = self.m
        self.assertTrue(m["json_valido"])                          # "JSON sintácticamente válido: Sí"
        self.assertEqual(m["superseded_recuperados"], 0)            # "0 de 2 esperados"
        self.assertEqual(m["tareas"]["tp"], 6)                      # "6 frente a 7"
        self.assertEqual(m["tareas_por_gold"]["T5"], "omitida")     # enlace de la demo
        self.assertEqual(m["tareas_plazo_exacto"], "5/6")           # regresión 01:00
        self.assertEqual(m["personas_ausentes_asignadas"], 1)       # Paula
        self.assertEqual(m["errores_esquema"], 2)                   # "null" como texto y state "pending"
        self.assertEqual(m["decisiones"]["tp"], 3)
        for gid in ("D5", "D7", "D8", "D9"):                        # WhatsApp, demo, U055, bloqueadores
            self.assertEqual(m["decisiones_por_gold"][gid], "omitida")
        self.assertEqual(m["evidencias"]["tipo1_id_incorrecto"], 0)
        self.assertEqual(m["evidencias"]["no_exactas_byte_a_byte"], 3)


if __name__ == "__main__":
    unittest.main()
