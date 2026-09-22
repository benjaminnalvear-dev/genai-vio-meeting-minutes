"""Evaluador automático: compara salidas (baseline o pipeline) contra el gold.

Aplica exactamente el mismo criterio a cualquier salida, que es lo que exige la
rúbrica del entregable 2 ("the same correctness criterion to the baseline and to
the solution").

Acepta:
  - registros JSON de baseline.py / run_model_test.ps1 (campo "response"/"response_raw")
  - salidas .md con un bloque ```json (como 01_salida_ministral_8k.md)
  - JSON directo con el esquema del prompt directo (decisions / action_items /
    pending_issues) o con el esquema del entregable 1 (decisions / tasks con
    statement, description, condition, evidence_id)

Uso:
    python scripts/evaluate.py --gold pruebas/01_gold.json SALIDA [SALIDA ...]
    python scripts/evaluate.py --gold pruebas/01_gold.json resultados/baseline/*.json \\
        resultados/pipeline/*.json --report resultados/comparacion_01.md
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from common import load_transcript, norm_loose, norm_quote, parse_json_response

STATES = ["final", "superseded", "rejected", "pending"]
NULL_LIKE = {"", "null", "none", "n/a", "na", "-", "sin fecha", "sin responsable", "no definido",
             "no asignado", "sin asignar", "pendiente", "tbd", "sin condicion", "sin condiciones",
             "ninguna", "ninguno", "no aplica", "desconocido"}


# ============================================================ carga de salidas
def load_output(path: Path) -> dict:
    """Devuelve {"data": dict|None, "valid": bool, "meta": {...}}."""
    text = path.read_text(encoding="utf-8")
    meta = {"file": path.name, "model": None, "seconds": None, "tokens": None, "done_reason": None}

    if path.suffix.lower() == ".md":
        m = re.search(r"```json\s*(.*?)```", text, re.S)
        data, valid = parse_json_response(m.group(1)) if m else (None, False)
        mm = re.search(r"Modelo:\s*`([^`]+)`", text)
        meta["model"] = mm.group(1) if mm else None
        mm = re.search(r"Duraci[oó]n total:\s*([\d.]+)\s*s", text)
        meta["seconds"] = float(mm.group(1)) if mm else None
        mm = re.search(r"Tokens generados:\s*([\d,.]+)", text)
        meta["tokens"] = int(re.sub(r"\D", "", mm.group(1))) if mm else None
        return {"data": data, "valid": valid, "meta": meta}

    obj, ok = parse_json_response(text)
    if not ok:
        return {"data": None, "valid": False, "meta": meta}
    if isinstance(obj, dict) and ("response_raw" in obj or "response_json_valid" in obj):
        meta["model"] = obj.get("model")
        meta["system"] = obj.get("system")
        meta["done_reason"] = obj.get("done_reason")
        meta["tokens"] = obj.get("eval_count")
        if obj.get("total_duration_ns"):
            meta["seconds"] = obj["total_duration_ns"] / 1e9
        elif obj.get("wall_seconds"):
            meta["seconds"] = obj["wall_seconds"]
        data = obj.get("response")
        valid = bool(obj.get("response_json_valid")) and isinstance(data, dict)
        if not valid and obj.get("response_raw"):
            data, valid = parse_json_response(obj["response_raw"])
        return {"data": data if valid else None, "valid": valid, "meta": meta}
    return {"data": obj, "valid": isinstance(obj, dict), "meta": meta}


# ============================================================ normalización de ítems
def clean_null(v):
    if v is None:
        return None
    if isinstance(v, (list, dict)):
        v = json.dumps(v, ensure_ascii=False)
    s = str(v).strip()
    return None if norm_loose(s).strip(" .") in NULL_LIKE else s


def extract_evidence(item: dict) -> list[tuple[str | None, str | None]]:
    out = []
    ev = item.get("evidence")
    if isinstance(ev, dict):
        ev = [ev]
    if isinstance(ev, str):
        ev = [{"utterance_id": ev}]
    for e in ev or []:
        if isinstance(e, dict):
            uid = e.get("utterance_id") or e.get("id") or e.get("evidence_id")
            q = e.get("exact_quote") or e.get("quote") or e.get("text")
            out.append((str(uid).strip().upper() if uid else None, q))
        elif isinstance(e, str):
            out.append((e.strip().upper() if re.fullmatch(r"\s*U\d+\s*", e) else None,
                        None if re.fullmatch(r"\s*U\d+\s*", e) else e))
    eid = item.get("evidence_id")
    if eid:
        ids = eid if isinstance(eid, list) else re.findall(r"U\d+", str(eid))
        q = item.get("evidence_quote") or item.get("exact_quote")
        for i in ids:
            out.append((str(i).upper(), q if len(ids) == 1 else None))
    return out


def normalize(data: dict) -> tuple[list[dict], list[dict]]:
    """Convierte cualquiera de los dos esquemas a una forma interna común."""
    pool, tasks = [], []
    for d in data.get("decisions", []) or []:
        if not isinstance(d, dict):
            continue
        text = " ".join(str(d.get(k) or "") for k in ("topic", "outcome", "statement", "condition"))
        pool.append({"text": text.strip(), "state": norm_loose(d.get("state")) or None,
                     "evidence": extract_evidence(d), "src": "decision"})
    for p in data.get("pending_issues", []) or []:
        if not isinstance(p, dict):
            continue
        pool.append({"text": str(p.get("issue") or p.get("topic") or ""), "state": "pending",
                     "owner": clean_null(p.get("owner")),
                     "evidence": extract_evidence(p), "src": "pending_issue"})
    for t in (data.get("action_items") or data.get("tasks") or []):
        if not isinstance(t, dict):
            continue
        tasks.append({
            "text": str(t.get("task") or t.get("description") or ""),
            "assignee": clean_null(t.get("assignee")),
            "deadline": clean_null(t.get("deadline")),
            "condition": clean_null(t.get("conditions") if "conditions" in t else t.get("condition")),
            "evidence": extract_evidence(t),
        })
    return pool, tasks


# ============================================================ emparejamiento
def keyword_match(match: dict, text: str):
    t = norm_loose(text)
    if any(norm_loose(x) in t for x in match.get("none_of", [])):
        return None
    hits = 0
    for group in match["all_of"]:
        if not any(norm_loose(term) in t for term in group):
            return None
        hits += 1
    return hits


def align(gold_items, pred_items, use_state: bool):
    """Emparejamiento uno a uno, greedy por puntaje. Devuelve {gold_idx: pred_idx}."""
    cands = []
    for gi, g in enumerate(gold_items):
        gev = set(g["evidence"])
        for pi, p in enumerate(pred_items):
            hits = keyword_match(g["match"], p["text"])
            if hits is None:
                continue
            ids = {u for u, _ in p["evidence"] if u}
            score = hits + 0.5 * len(ids & gev)
            if use_state and p.get("state") in g["states"]:
                score += 1.5
            cands.append((score, gi, pi))
    cands.sort(key=lambda x: -x[0])
    used_g, used_p, pairs = set(), set(), {}
    for _, gi, pi in cands:
        if gi not in used_g and pi not in used_p:
            pairs[gi] = pi
            used_g.add(gi)
            used_p.add(pi)
    return pairs


# ============================================================ comparación de campos
def parse_deadline(s):
    if s is None:
        return None
    m = re.search(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{1,2}):(\d{2}))?", s)
    if not m:
        return "NO_PARSEABLE: " + s
    d, h, mi = m.groups()
    return f"{d} {int(h):02d}:{mi}" if h else d


def assignee_ok(gold: str | None, pred: str | None) -> bool:
    if gold is None:
        return pred is None
    return pred is not None and norm_loose(gold).split()[0] in re.split(r"[\s,;/]+", norm_loose(pred))


def condition_ok(gold, pred) -> bool:
    if gold == "*":
        return True
    if gold is None:
        return pred is None
    return pred is not None and re.search(gold, norm_loose(pred)) is not None


def prf(tp, n_pred, n_gold):
    p = tp / n_pred if n_pred else 0.0
    r = tp / n_gold if n_gold else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


# ============================================================ evaluación
def evaluate(gold: dict, utterances: dict, output: dict) -> dict:
    G_pool, G_tasks = gold["records"], gold["tasks"]
    res = {"file": output["meta"]["file"], "meta": output["meta"], "json_valid": output["valid"]}
    if not output["valid"]:
        res.update({"note": "JSON inválido: se evalúa como salida vacía"})
        pool, tasks = [], []
    else:
        pool, tasks = normalize(output["data"])

    pool_pairs = align(G_pool, pool, use_state=True)
    task_pairs = align(G_tasks, tasks, use_state=False)

    # --- detección
    p, r, f = prf(len(pool_pairs), len(pool), len(G_pool))
    res["records"] = {"pred": len(pool), "gold": len(G_pool), "matched": len(pool_pairs), "P": p, "R": r, "F1": f}
    p, r, f = prf(len(task_pairs), len(tasks), len(G_tasks))
    res["tasks"] = {"pred": len(tasks), "gold": len(G_tasks), "matched": len(task_pairs), "P": p, "R": r, "F1": f}

    # --- estados: macro-F1 sobre final/superseded/rejected/pending
    y_true, y_pred = [], []
    matched_p = set(pool_pairs.values())
    for gi, g in enumerate(G_pool):
        canon = g["states"][0]
        if gi in pool_pairs:
            ps = pool[pool_pairs[gi]]["state"]
            y_true.append(canon)
            y_pred.append(canon if ps in g["states"] else (ps or "?"))
        else:
            y_true.append(canon)
            y_pred.append("<omitido>")
    for pi, pitem in enumerate(pool):
        if pi not in matched_p:
            y_true.append("<no_existe>")
            y_pred.append(pitem["state"] or "?")
    f1s = {}
    for s in STATES:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == s and b == s)
        fp = sum(1 for a, b in zip(y_true, y_pred) if b == s and a != s)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == s and b != s)
        if tp + fp + fn == 0:
            continue
        f1s[s] = 2 * tp / (2 * tp + fp + fn)
    res["states"] = {"per_state_F1": f1s, "macro_F1": sum(f1s.values()) / len(f1s) if f1s else 0.0,
                     "correct_on_matched": sum(1 for gi, pi in pool_pairs.items()
                                               if pool[pi]["state"] in G_pool[gi]["states"])}

    # --- campos de tareas (sobre las 7 tareas del gold; tarea omitida = incorrecta)
    acc = Counter()
    detail_tasks = []
    for gi, g in enumerate(G_tasks):
        row = {"gold": g["id"], "label": g["label"], "pred": None}
        if gi in task_pairs:
            t = tasks[task_pairs[gi]]
            dl = parse_deadline(t["deadline"])
            ok_a = assignee_ok(g["assignee"], t["assignee"])
            ok_d = dl in g["deadline"]
            ok_c = condition_ok(g["condition"], t["condition"])
            acc["assignee"] += ok_a
            acc["deadline"] += ok_d
            acc["condition"] += ok_c
            row.update({"pred": t["text"][:90], "assignee": (t["assignee"], ok_a), "deadline": (dl, ok_d),
                        "condition": ((t["condition"] or "")[:60] or None, ok_c)})
        detail_tasks.append(row)
    n = len(G_tasks)
    res["fields"] = {k: acc[k] / n for k in ("assignee", "deadline", "condition")}
    res["fields_counts"] = {k: f"{acc[k]}/{n}" for k in ("assignee", "deadline", "condition")}

    # --- evidencia
    support_sets = {}
    for gi, pi in pool_pairs.items():
        support_sets[("pool", pi)] = set(G_pool[gi]["evidence"])
    for gi, pi in task_pairs.items():
        support_sets[("task", pi)] = set(G_tasks[gi]["evidence"])
    n_cit = n_verbatim = n_correct = n_quoted = 0
    bad_quotes = []
    for kind, items in (("pool", pool), ("task", tasks)):
        for pi, it in enumerate(items):
            for uid, q in it["evidence"]:
                n_cit += 1
                utt = utterances.get(uid)
                verb = None
                if q is not None:
                    n_quoted += 1
                    verb = utt is not None and norm_quote(q) in norm_quote(utt)
                    n_verbatim += verb
                    if not verb:
                        bad_quotes.append({"id": uid, "quote": str(q)[:100]})
                supports = uid in support_sets.get((kind, pi), set())
                if supports and (verb is None or verb):
                    n_correct += 1
    res["evidence"] = {
        "citations": n_cit,
        "precision": n_correct / n_cit if n_cit else 0.0,
        "verbatim_rate": n_verbatim / n_quoted if n_quoted else 0.0,
        "non_verbatim": bad_quotes,
    }

    # --- afirmaciones sin respaldo
    claims = unsupported = 0
    matched_t = set(task_pairs.values())
    gold_of_task = {pi: G_tasks[gi] for gi, pi in task_pairs.items()}
    gold_of_pool = {pi: G_pool[gi] for gi, pi in pool_pairs.items()}
    for pi, it in enumerate(pool):
        claims += 1
        unsupported += pi not in matched_p
        if it.get("owner"):
            claims += 1
            g = gold_of_pool.get(pi)
            unsupported += not (g and g.get("owner") and assignee_ok(g["owner"], it["owner"]))
    for pi, t in enumerate(tasks):
        claims += 1
        unsupported += pi not in matched_t
        g = gold_of_task.get(pi)
        for field in ("assignee", "deadline", "condition"):
            if t[field] is None:
                continue
            claims += 1
            if g is None:
                unsupported += 1
            elif field == "deadline" and g["deadline"] == [None]:
                unsupported += 1
            elif field == "condition" and g["condition"] is None:
                unsupported += 1
    res["unsupported_rate"] = unsupported / claims if claims else 0.0
    res["unsupported_counts"] = f"{unsupported}/{claims}"

    # --- errores especialmente penalizados (01_gold_referencia.md)
    forbidden = [norm_loose(x) for x in gold.get("forbidden_assignees", [])]
    gid = {g["id"]: i for i, g in enumerate(G_pool)}
    tid = {g["id"]: i for i, g in enumerate(G_tasks)}

    def pool_state(code):
        i = gid.get(code)
        return pool[pool_pairs[i]]["state"] if i in pool_pairs else None

    def task_cond_missing(code):
        i = tid.get(code)
        if i not in task_pairs:
            return "tarea omitida"
        return not condition_ok(G_tasks[i]["condition"], tasks[task_pairs[i]]["condition"])

    neg = re.compile(r"\b(no|sin|fuera|descart|rechaz|exclu|elimin|queda fuera)")
    res["penalized"] = {
        "asigna_a_no_participante": sum(1 for who in [t["assignee"] for t in tasks] + [i.get("owner") for i in pool]
                                        if who and any(f in norm_loose(who) for f in forbidden)),
        "lunes_31_como_final": pool_state("D2") == "final",
        "omite_condicion_credencial": task_cond_missing("T2"),
        "omite_condicion_QA": task_cond_missing("T4"),
        "soporte_como_tarea": any(keyword_match(G_pool[gid["P2"]]["match"], t["text"]) is not None for t in tasks),
        "herramienta_rechazada_aprobada": any(
            it["state"] == "final" and re.search(r"whatsapp|mailfast", norm_loose(it["text"]))
            and not neg.search(norm_loose(it["text"])) for it in pool),
        "inventa_retencion": any(
            it["state"] == "final" and "retencion" in norm_loose(it["text"])
            and re.search(r"30|treinta|seis meses|6 meses", norm_loose(it["text"])) for it in pool),
        "citas_no_textuales": len(bad_quotes),
    }

    # --- detalle legible
    res["detail_records"] = [
        {"gold": g["id"], "label": g["label"], "expected": "/".join(g["states"]),
         "pred": pool[pool_pairs[i]]["text"][:90] if i in pool_pairs else None,
         "pred_state": pool[pool_pairs[i]]["state"] if i in pool_pairs else None}
        for i, g in enumerate(G_pool)]
    res["detail_tasks"] = detail_tasks
    res["unmatched_pred"] = [it["text"][:90] for i, it in enumerate(pool) if i not in matched_p] + \
                            [t["text"][:90] for i, t in enumerate(tasks) if i not in matched_t]
    return res


# ============================================================ reporte
def fmt(x, pct=True):
    if isinstance(x, bool):
        return "sí" if x else "no"
    if isinstance(x, float):
        return f"{x:.2f}"
    return str(x) if x is not None else "-"


def summary_table(results: list[dict]) -> str:
    rows = [
        ("JSON válido", lambda r: fmt(r["json_valid"])),
        ("Decisiones+pendientes F1", lambda r: f'{r["records"]["F1"]:.2f} ({r["records"]["matched"]}/{r["records"]["gold"]}, pred {r["records"]["pred"]})'),
        ("Tareas F1", lambda r: f'{r["tasks"]["F1"]:.2f} ({r["tasks"]["matched"]}/{r["tasks"]["gold"]}, pred {r["tasks"]["pred"]})'),
        ("Macro-F1 estados", lambda r: f'{r["states"]["macro_F1"]:.2f}'),
        ("Responsable correcto", lambda r: r["fields_counts"]["assignee"]),
        ("Plazo correcto", lambda r: r["fields_counts"]["deadline"]),
        ("Condición correcta", lambda r: r["fields_counts"]["condition"]),
        ("Precisión de evidencia", lambda r: f'{r["evidence"]["precision"]:.2f} ({r["evidence"]["citations"]} citas)'),
        ("Citas textuales exactas", lambda r: f'{r["evidence"]["verbatim_rate"]:.2f}'),
        ("Afirmaciones sin respaldo", lambda r: f'{r["unsupported_rate"]:.2f} ({r["unsupported_counts"]})'),
        ("Tiempo (s)", lambda r: f'{r["meta"]["seconds"]:.0f}' if r["meta"].get("seconds") else "-"),
    ]
    head = "| Métrica | " + " | ".join(r["file"] for r in results) + " |"
    sep = "|---|" + "---|" * len(results)
    lines = [head, sep] + ["| " + name + " | " + " | ".join(f(r) for r in results) + " |" for name, f in rows]
    lines += ["", "**Errores especialmente penalizados**", "", head, sep]
    for k in results[0]["penalized"]:
        lines.append(f"| {k} | " + " | ".join(fmt(r["penalized"][k]) for r in results) + " |")
    return "\n".join(lines)


def detail_md(r: dict) -> str:
    out = [f"### {r['file']}", ""]
    if not r["json_valid"]:
        out += ["JSON inválido: evaluado como salida vacía.", ""]
    out += ["| Gold | Esperado | Ítem emparejado | Estado |", "|---|---|---|---|"]
    for d in r["detail_records"]:
        ok = "" if d["pred_state"] is None else (" ✓" if d["pred_state"] in d["expected"].split("/") else " ✗")
        out.append(f'| {d["gold"]} {d["label"]} | {d["expected"]} | {d["pred"] or "(omitido)"} | {(d["pred_state"] or "-") + ok} |')
    out += ["", "| Tarea gold | Ítem emparejado | Responsable | Plazo | Condición |", "|---|---|---|---|---|"]
    for t in r["detail_tasks"]:
        if t["pred"] is None:
            out.append(f'| {t["gold"]} {t["label"]} | (omitida) | - | - | - |')
        else:
            c = lambda v: f'{v[0]} {"✓" if v[1] else "✗"}'
            out.append(f'| {t["gold"]} {t["label"]} | {t["pred"]} | {c(t["assignee"])} | {c(t["deadline"])} | {c(t["condition"])} |')
    if r["unmatched_pred"]:
        out += ["", "Ítems predichos sin correspondencia en el gold:", ""] + [f"- {u}" for u in r["unmatched_pred"]]
    if r["evidence"]["non_verbatim"]:
        out += ["", "Citas que no aparecen textualmente en la intervención citada:", ""] + \
               [f'- {q["id"]}: "{q["quote"]}"' for q in r["evidence"]["non_verbatim"]]
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gold", required=True)
    ap.add_argument("outputs", nargs="+")
    ap.add_argument("--report", help="ruta .md para guardar tabla + detalle (además se guarda un .json)")
    args = ap.parse_args()

    gold_path = Path(args.gold)
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    tr_path = (gold_path.parent / gold["transcript"])
    utterances = {u["id"]: u["text"] for u in load_transcript(tr_path)["utterances"]}

    results = [evaluate(gold, utterances, load_output(Path(o))) for o in args.outputs]
    table = summary_table(results)
    print(table)

    if args.report:
        rp = Path(args.report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        body = f"# Evaluación contra {gold_path.name}\n\n{table}\n\n## Detalle por salida\n\n" + \
               "\n".join(detail_md(r) for r in results)
        rp.write_text(body, encoding="utf-8")
        rp.with_suffix(".json").write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str),
                                           encoding="utf-8")
        print(f"\nReporte: {rp}  (+ {rp.with_suffix('.json').name})")


if __name__ == "__main__":
    main()
