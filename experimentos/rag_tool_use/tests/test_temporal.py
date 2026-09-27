"""Pruebas del resolvedor temporal. Reunión: jueves 27 de agosto de 2026.

Incluye todas las expresiones de plazo de la transcripción 01 y variantes que no aparecen en ella.
"""

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.temporal import anchor, resolve  # noqa: E402

MEETING = date(2026, 8, 27)

CASES = [
    # (literal, esperado) — transcripción 01
    ("mañana a las cinco", "2026-08-28 17:00"),                         # U004, U026
    ("Lunes 31 a las cuatro", "2026-08-31 16:00"),                      # U008, U019
    ("el lunes en la mañana", "2026-08-31"),                            # U011
    ("mañana al mediodía", "2026-08-28 12:00"),                          # U012
    ("Mañana a las doce", "2026-08-28 12:00"),                          # U013
    ("mañana viernes a las doce", "2026-08-28 12:00"),                  # U014
    ("antes de mañana viernes a las doce", "2026-08-28 12:00"),         # U017 (condición)
    ("el lunes a las seis", "2026-08-31 18:00"),                        # U017
    ("el lunes a primera hora", "2026-08-31"),                          # U017
    ("miércoles 2 a las once y media", "2026-09-02 11:30"),             # U039
    ("miércoles 2 de septiembre a las 10:00", "2026-09-02 10:00"),      # U041
    ("el martes a las nueve", "2026-09-01 09:00"),                      # U042
    ("el martes 1 entre nueve y una", "2026-09-01 13:00"),              # U044
    ("el martes 1 entre nueve y una, y subo el informe antes de la una", "2026-09-01 13:00"),
    ("antes de la una", None),                                          # sin día -> None salvo contexto
    ("el martes antes de las cuatro", "2026-09-01 16:00"),              # U045
    ("viernes 28 a las doce", "2026-08-28 12:00"),                      # U057
    ("Pantallas y etiquetas mañana a mediodía", "2026-08-28 12:00"),    # U064
    ("invitaciones el lunes seis", "2026-08-31"),                       # U065 ("seis" sin "a las")
    ("sin fecha", None),
    # variantes que no están en la transcripción
    ("pasado mañana a las 9", "2026-08-29 09:00"),
    ("hoy a las 16:30", "2026-08-27 16:30"),
    ("el jueves a las tres", "2026-09-03 15:00"),
    ("el viernes a las diez menos cuarto", "2026-08-28 09:45"),
    ("15 de septiembre", "2026-09-15"),
    ("el lunes a las 8 de la tarde", "2026-08-31 20:00"),
    ("el lunes a las 7 de la mañana", "2026-08-31 07:00"),
    ("mañana en la mañana", "2026-08-28"),
    ("el martes a la una y cuarto", "2026-09-01 13:15"),
]


class TestResolver(unittest.TestCase):
    def test_cases(self):
        for literal, expected in CASES:
            with self.subTest(literal=literal):
                self.assertEqual(resolve(literal, MEETING).value, expected)

    def test_day_from_utterance(self):
        # U066: el literal no trae día, la intervención citada sí.
        r = resolve("antes de la una", MEETING, "Regresión e informe el martes antes de la una.")
        self.assertEqual(r.value, "2026-09-01 13:00")

    def test_anchor_to_utterance(self):
        # El modelo parafrasea mal el literal; manda el texto de la intervención citada.
        u013 = "Esas tres sí. El resto, no prometo. Mañana a las doce te dejo esas pantallas y las etiquetas definitivas de los botones."
        self.assertEqual(anchor("lunes a las doce", u013, MEETING).value, "2026-08-28 12:00")
        u067 = "Y yo: Sergio mañana antes de las cinco, invitación el martes antes de las cuatro si QA aprueba, más el enlace remoto. Soporte queda pendiente."
        self.assertEqual(anchor("lunes antes de las cinco", u067, MEETING).value, "2026-08-28 17:00")
        self.assertEqual(anchor("martes antes de las cuatro", u067, MEETING).value, "2026-09-01 16:00")
        u044 = "Ya. Yo hago la regresión el martes 1 entre nueve y una, y subo el informe antes de la una."
        self.assertEqual(anchor("antes de la una", u044, MEETING).value, "2026-09-01 13:00")
        u017 = "Un día para reproducir y corregir; no quiero decir horas. Si Andrés la envía antes de mañana viernes a las doce, lo dejo listo el lunes a las seis. Si no, el lunes a primera hora les digo que no llego."
        self.assertEqual(anchor("el lunes a las seis", u017, MEETING).value, "2026-08-31 18:00")

    def test_alert_without_time(self):
        r = resolve("el lunes a primera hora", MEETING)
        self.assertTrue(r.alerts)


if __name__ == "__main__":
    unittest.main()
