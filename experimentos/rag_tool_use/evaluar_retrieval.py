"""Mide la calidad del retrieval SIN llamar al modelo.

Para cada bloque de 8 intervenciones, las intervenciones anteriores "relevantes" son las que respaldan
(según gold/01_gold.json) un ítem que también aparece en el bloque. Se cuenta cuántas de esas trae
cada variante del buscador. Uso: python evaluar_retrieval.py
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from src import pipeline  # noqa: E402
from src.retrieval import BM25, tokenize_stem  # noqa: E402
from src.transcript import load_meeting  # noqa: E402

PREV = pipeline.PREVIOUS_CONTEXT
K = pipeline.RETRIEVED_CONTEXT


def main():
    meeting = load_meeting(HERE.parent.parent / "pruebas" / "01_transcripcion_reunion_simulada.md")
    U = meeting.utterances
    ids = [u.id for u in U]
    gold = json.loads((HERE / "gold" / "01_gold.json").read_text(encoding="utf-8"))
    items = gold["decisiones"] + gold["tareas"] + gold["pendientes"]
    bm = BM25([u.text for u in U])
    bm_stem = BM25([u.text for u in U], tokenizer=tokenize_stem)

    def relevant(s, e):
        block, allowed, rel = set(ids[s:e]), set(ids[: max(0, s - PREV)]), set()
        for it in items:
            support = set(it["respaldo"]) | set(it.get("respaldo_extra", []))
            if support & block:
                rel |= support & allowed
        return rel

    # Buscar sobre el registro: reconstruye, sin modelo, el registro que tenía S2 en la T4 al llegar a cada bloque.
    rec = json.loads((HERE / "resultados" / "tesla-t4" / "pipeline_tool_bloques.json").read_text(encoding="utf-8"))
    calls = [c for c in rec["llamadas_herramientas"] if c.get("_aplicada_a")]

    def over_registry(s, e):
        reg = pipeline.Registry(meeting)
        for c in calls:
            if ids.index(c["utterance_id"]) < s:
                cc = {k: v for k, v in c.items() if not k.startswith("_") and k != "pasada"}
                reg.apply(cc, {cc["utterance_id"]})
        its = list(reg.items.values())
        if not its:
            return set()
        bm_reg = BM25([f"{i.tema} {i.contenido} {i.responsable or ''}" for i in its], tokenizer=tokenize_stem)
        allowed, out = set(ids[: max(0, s - PREV)]), []
        for u in U[s:e]:
            for t in bm_reg.top(u.text, 1, None):
                out += [uid for uid, _ in its[t].evidence if uid in allowed and uid not in out]
        return set(out[:K])

    def via_pipeline(mode):
        return lambda s, e: {u.id for u in pipeline.retrieve(meeting, mode, s, U[s:e], bm, bm_stem)}

    variants = {
        "S3  · una consulta por bloque (actual)": via_pipeline("bloque"),
        "S3b · una consulta por intervención + stemmer": via_pipeline("por_intervencion"),
        "      sobre el registro + stemmer (explorado)": over_registry,
        "Control · todo el pasado (techo)": via_pipeline("todo_el_pasado"),
    }
    blocks = [(s, min(s + 8, len(U))) for s in range(0, len(U), 8) if s > PREV]
    print(f"{'variante':48s} relevantes traídas   precisión   intervenciones agregadas")
    for name, f in variants.items():
        hit = rel_total = ret_total = 0
        for s, e in blocks:
            rel, got = relevant(s, e), f(s, e)
            hit, rel_total, ret_total = hit + len(got & rel), rel_total + len(rel), ret_total + len(got)
        print(f"{name:48s} {hit:2d}/{rel_total} ({hit / rel_total:.0%})        {hit / max(ret_total, 1):.0%}        {ret_total}")


if __name__ == "__main__":
    main()
