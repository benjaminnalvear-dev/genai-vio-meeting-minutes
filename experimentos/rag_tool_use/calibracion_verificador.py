"""Calibración del verificador sí/no con pares de OTRA reunión (no la transcripción evaluada).

Uso: python calibracion_verificador.py   (requiere Ollama con ministral-3:3b)
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.pipeline import Item, verify  # noqa: E402
from src.transcript import Meeting, Utterance  # noqa: E402

UTTS = [
    Utterance("U001", "10:00:00", "Luis", "Yo reservo el salón mañana a las tres, si Marta me manda el presupuesto."),
    Utterance("U002", "10:00:10", "Ana", "Perfecto, a tu nombre. Y yo imprimo los afiches el lunes."),
    Utterance("U003", "10:00:20", "Ana", "Entonces Sabores descartado. Vamos con Delicias."),
    Utterance("U004", "10:00:30", "Ana", "Eso lo dejamos pendiente hasta tener la lista de invitados."),
    Utterance("U005", "10:00:40", "Luis", "¿Contratamos el catering de Sabores?"),
    Utterance("U006", "10:00:50", "Luis", "Cobran el doble que el año pasado."),
    Utterance("U007", "10:01:00", "Marta", "El proyector de la sala está roto."),
    Utterance("U008", "10:01:10", "Ana", "Confirmo: Delicias."),
]
MEETING = Meeting(date(2026, 3, 5), "feria", {"Ana Díaz": "coordinadora", "Luis Mora": "logística"}, ["Marta"], UTTS)


def task(who, what):
    return Item("T1", "tarea", contenido=what, responsable=who)


def decision(state, topic, what, replaced=False):
    return Item("D1", "decision", tema=topic, contenido=what, estado=state, reemplazada_por="D2" if replaced else None)


# (ítem, intervención, ¿debería respaldarlo?)
PAIRS = [
    (task("Luis", "reservar el salón"), "U001", True),
    (task("Ana", "imprimir los afiches"), "U002", True),
    (decision("final", "catering", "contratar Delicias"), "U003", True),
    (decision("pendiente", "menú vegano", "definir si habrá menú vegano"), "U004", True),
    (decision("propuesta", "catering", "contratar Sabores", replaced=True), "U005", True),
    (decision("final", "catering", "contratar Delicias"), "U008", True),
    (decision("final", "catering", "contratar Sabores"), "U005", False),
    (task("Luis", "reservar el salón"), "U006", False),
    (decision("final", "fecha", "hacer la feria el domingo"), "U002", False),
    (task("Marta", "arreglar el proyector"), "U007", False),
    (task("Ana", "reservar el salón"), "U001", False),
    (decision("rechazada", "catering", "contratar Delicias"), "U003", False),
]


def main():
    calls = []
    hits = {"tp": 0, "fn": 0, "tn": 0, "fp": 0}
    for item, uid, expected in PAIRS:
        got = verify(item, uid, MEETING, calls)
        key = ("tp" if got else "fn") if expected else ("fp" if got else "tn")
        hits[key] += 1
        print(f"{'OK ' if got == expected else 'MAL'} esperado={expected!s:5} obtenido={got!s:5} {uid} {item.line() if item.evidence else item.contenido}")
    total = len(PAIRS)
    print(f"\nAciertos {hits['tp'] + hits['tn']}/{total} | verdaderos positivos {hits['tp']}, falsos negativos {hits['fn']}, "
          f"verdaderos negativos {hits['tn']}, falsos positivos {hits['fp']}")


if __name__ == "__main__":
    main()
