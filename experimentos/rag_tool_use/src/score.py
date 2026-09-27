"""Corrector automático: compara un acta (esquema del prompt canónico del D1) contra gold/01_gold.json.

El mismo corrector se aplica al baseline y a la solución.

Criterios (declarados en el README):
- Correspondencia ítem predicho -> ítem gold: comparten al menos un ID de respaldo del gold
  (respaldo + respaldo_extra). Desempate: estado compatible, IDs de la pauta original, primer ID citado.
- Decisión correcta = corresponde a un ítem gold y su estado está entre los aceptados.
- Tarea identificada = corresponde a una tarea gold. Responsable y plazo se comparan exactos.
- Cita exacta: se reporta estricta (byte a byte) y normalizada (mayúsculas y espacios).
- Tipo 3 (proxy): el ID citado no está entre los respaldos del ítem gold correspondiente.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from .transcript import Meeting

VALID_DECISION_STATES = {"final", "superseded", "rejected"}
VALID_TASK_STATUS = {"agreed", "conditional", "pending"}
NUMBER_WORDS = {1: "una", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis", 7: "siete",
                8: "ocho", 9: "nueve", 10: "diez", 11: "once", 12: "doce"}


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.casefold()).strip()


def norm_quote(text: str) -> str:
    return fold(text).strip(" .,;:!?¡¿\"'“”«»…")


# ---------------------------------------------------------------- carga

def _closers(prefix: str) -> str | None:
    """Cierres necesarios para que `prefix` sea JSON; None si termina dentro de un string."""
    stack, in_str, esc = [], False, False
    for ch in prefix:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack:
            stack.pop()
    return None if in_str else "".join(reversed(stack))


def repair_truncated(raw: str) -> dict | None:
    """Recorta un JSON cortado por límite de tokens hasta el último objeto completo y lo cierra.

    Solo para analizar contenido: el acta sigue contando como JSON inválido.
    """
    for pos in range(len(raw) - 1, 0, -1):
        if raw[pos] != "}":
            continue
        prefix = raw[: pos + 1]
        closers = _closers(prefix)
        if closers is None:
            continue
        try:
            return json.loads(prefix + closers)
        except json.JSONDecodeError:
            continue
    return None


def load_acta(path: str | Path) -> tuple[dict | None, bool, str]:
    """Devuelve (acta, json_valido, texto_crudo). Acepta .md con bloque ```json o registro .json."""
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        m = re.search(r"```json\n(.*?)```", raw, re.S)
        raw = m.group(1) if m else raw
    else:
        record = json.loads(raw)
        if "acta" in record:
            acta = record["acta"]
            return acta, acta is not None, record.get("response_raw", "")
        raw = record.get("response_raw", "")
    try:
        return json.loads(raw), True, raw
    except json.JSONDecodeError:
        return None, False, raw


# ---------------------------------------------------------------- correspondencia

def cited_ids(item: dict) -> list[str]:
    ids = [e.get("utterance_id") for e in item.get("evidence") or [] if isinstance(e, dict)]
    return [i for i in ids if isinstance(i, str)]


def first_name(value) -> str:
    if not isinstance(value, str):
        return ""
    return fold(value).split(" ")[0] if value.strip() else ""


@dataclass
class Match:
    pred_index: int
    gold: dict
    overlap: list[str]


def match_items(preds: list[dict], golds: list[dict], state_ok=None, extra_ok=None) -> list[Match]:
    candidates = []
    for pi, pred in enumerate(preds):
        ids = cited_ids(pred)
        for g in golds:
            support = set(g["respaldo"]) | set(g.get("respaldo_extra", []))
            overlap = [i for i in ids if i in support]
            if not overlap:
                continue
            key = (
                1 if state_ok is None or state_ok(pred, g) else 0,
                1 if extra_ok is None or extra_ok(pred, g) else 0,
                len([i for i in ids if i in g["respaldo"]]),
                len(overlap),
                1 if ids and ids[0] in support else 0,
            )
            candidates.append((key, pi, g, overlap))
    candidates.sort(key=lambda c: c[0], reverse=True)
    used_pred, used_gold, matches = set(), set(), []
    for _, pi, g, overlap in candidates:
        if pi in used_pred or g["id"] in used_gold:
            continue
        used_pred.add(pi)
        used_gold.add(g["id"])
        matches.append(Match(pi, g, overlap))
    return sorted(matches, key=lambda m: m.pred_index)


def mentions_datetime(text: str, value: str) -> bool:
    """¿El texto menciona el día y la hora de `value` (YYYY-MM-DD HH:MM)?"""
    t = fold(text)
    day_s, time_s = value.split(" ")
    y, mo, d = (int(x) for x in day_s.split("-"))
    h, mi = (int(x) for x in time_s.split(":"))
    day_ok = day_s in t or re.search(rf"\b{d}\b", t) is not None
    h12 = h - 12 if h > 12 else h
    patterns = [rf"\b0?{h}:{mi:02d}\b", rf"\b0?{h12}(:{mi:02d})?\s*(pm|p\.m\.)" if h >= 12 else rf"\b0?{h}(:{mi:02d})?\s*(am|a\.m\.)"]
    if mi == 0:
        patterns.append(rf"\blas {NUMBER_WORDS.get(h12, '@@')}\b")
    time_ok = any(re.search(p, t) for p in patterns)
    return day_ok and time_ok


# ---------------------------------------------------------------- corrector

@dataclass
class Report:
    metrics: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def md(self) -> str:
        return "\n".join(self.lines)


def prf(tp: int, n_pred: int, n_gold: int) -> dict:
    p = tp / n_pred if n_pred else 0.0
    r = tp / n_gold if n_gold else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "pred": n_pred, "gold": n_gold, "precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3)}


def score(acta: dict | None, json_valid: bool, gold: dict, meeting: Meeting, name: str = "", raw: str = "") -> Report:
    rep = Report()
    m = rep.metrics
    m["json_valido"] = json_valid
    m["json_reparado"] = False
    if acta is None and raw:
        acta = repair_truncated(raw)
        m["json_reparado"] = acta is not None
    if acta is None:
        rep.lines.append(f"### {name}\n\nJSON inválido: no se puede puntuar.")
        return rep

    utt = {u.id: u.text for u in meeting.utterances}
    schema_errors: list[str] = []
    decisions = acta.get("decisions") or []
    tasks = acta.get("action_items") or []
    pendings = acta.get("pending_issues") or []

    # ----- decisiones
    gold_dec = gold["decisiones"]
    required = [g for g in gold_dec if not g.get("opcional")]
    for d in decisions:
        if d.get("state") not in VALID_DECISION_STATES:
            schema_errors.append(f"decisión con state={d.get('state')!r}")

    def dec_state_ok(pred, g):
        return pred.get("state") in g["estados_aceptados"]

    def dec_value_ok(pred, g):
        return "valor" not in g or mentions_datetime(str(pred.get("outcome", "")), g["valor"])

    dec_matches = match_items(decisions, gold_dec, dec_state_ok, dec_value_ok)
    dec_rows, dec_tp, optional_matched = [], 0, 0
    matched_gold = {mt.gold["id"]: mt for mt in dec_matches}
    for mt in dec_matches:
        pred = decisions[mt.pred_index]
        ok_state = dec_state_ok(pred, mt.gold)
        ok_value = dec_value_ok(pred, mt.gold)
        if mt.gold.get("opcional"):
            # Un ítem opcional solo absorbe predicciones con estado aceptado; si no, cuenta como falso positivo.
            optional_matched += 1 if ok_state else 0
        elif ok_state and ok_value:
            dec_tp += 1
        dec_rows.append((mt.pred_index, pred, mt.gold, ok_state, ok_value, mt.overlap))
    n_pred_dec = len(decisions) - optional_matched
    m["decisiones"] = prf(dec_tp, n_pred_dec, len(required))
    # Estados obsoletos = decisiones del gold (no opcionales) que solo aceptan quedar reemplazadas o rechazadas.
    sup_ids = [g["id"] for g in required if "final" not in g["estados_aceptados"] and "superseded" in g["estados_aceptados"]]
    m["superseded_esperados"] = len(sup_ids)
    m["superseded_recuperados"] = sum(
        1 for gid in sup_ids
        if gid in matched_gold
        and dec_state_ok(decisions[matched_gold[gid].pred_index], matched_gold[gid].gold)
        and dec_value_ok(decisions[matched_gold[gid].pred_index], matched_gold[gid].gold)
    )
    m["decisiones_por_gold"] = {
        g["id"]: ("ok" if g["id"] in matched_gold and dec_state_ok(decisions[matched_gold[g["id"]].pred_index], g)
                  and dec_value_ok(decisions[matched_gold[g["id"]].pred_index], g)
                  else "estado/valor incorrecto" if g["id"] in matched_gold else "omitida")
        for g in gold_dec
    }

    # ----- tareas
    gold_tasks = gold["tareas"]

    def task_person_ok(pred, g):
        return first_name(pred.get("assignee")) == fold(g["responsable"])

    for t in tasks:
        dl = t.get("deadline")
        if isinstance(dl, str) and fold(dl) in {"null", "none", ""}:
            schema_errors.append(f"deadline como texto {dl!r} en '{str(t.get('task'))[:40]}'")
        if t.get("status") not in VALID_TASK_STATUS:
            schema_errors.append(f"tarea con status={t.get('status')!r}")
    task_matches = match_items(tasks, gold_tasks, task_person_ok)
    t_rows = []
    assignee_ok = deadline_ok = cond_required_ok = cond_spurious = 0
    n_cond_required = 0
    for mt in task_matches:
        pred, g = tasks[mt.pred_index], mt.gold
        a_ok = task_person_ok(pred, g)
        dl = pred.get("deadline")
        dl = None if isinstance(dl, str) and fold(dl) in {"null", "none", ""} else dl
        accepted = g.get("plazos_aceptados", [g["plazo"]])
        d_ok = (dl.strip() if isinstance(dl, str) else dl) in accepted
        has_cond = bool(pred.get("conditions")) and fold(str(pred.get("conditions"))) not in {"null", "none"}
        assignee_ok += a_ok
        deadline_ok += d_ok
        if g["requiere_condicion"]:
            n_cond_required += 1
            cond_required_ok += has_cond
        elif has_cond:
            cond_spurious += 1
        t_rows.append((mt.pred_index, pred, g, a_ok, d_ok, has_cond, mt.overlap))
    m["tareas"] = prf(len(task_matches), len(tasks), len(gold_tasks))
    m["tareas_responsable_exacto"] = f"{assignee_ok}/{len(task_matches)}"
    m["tareas_plazo_exacto"] = f"{deadline_ok}/{len(task_matches)}"
    m["tareas_condicion_requerida_presente"] = f"{cond_required_ok}/{n_cond_required}"
    m["tareas_condicion_no_esperada"] = cond_spurious
    task_gold_matched = {mt.gold["id"] for mt in task_matches}
    m["tareas_por_gold"] = {g["id"]: ("identificada" if g["id"] in task_gold_matched else "omitida") for g in gold_tasks}

    # ----- pendientes
    pend_matches = match_items(pendings, gold["pendientes"])
    m["pendientes"] = prf(len(pend_matches), len(pendings), len(gold["pendientes"]))

    # ----- personas ausentes asignadas
    absent = [fold(a) for a in gold["personas_ausentes"]]
    absent_hits = []
    for t in tasks:
        if any(a in fold(str(t.get("assignee") or "")) for a in absent):
            absent_hits.append(f"tarea '{str(t.get('task'))[:50]}' -> {t.get('assignee')}")
    for p in pendings:
        if any(a in fold(str(p.get("owner") or "")) for a in absent):
            absent_hits.append(f"pendiente '{str(p.get('issue'))[:50]}' -> {p.get('owner')}")
    m["personas_ausentes_asignadas"] = len(absent_hits)

    # ----- evidencias
    item_gold: dict[tuple[str, int], dict] = {}
    for mt in dec_matches:
        item_gold[("decisions", mt.pred_index)] = mt.gold
    for mt in task_matches:
        item_gold[("action_items", mt.pred_index)] = mt.gold
    for mt in pend_matches:
        item_gold[("pending_issues", mt.pred_index)] = mt.gold

    ev_total = t1 = t2 = strict_fail = t3 = unmatched_ev = 0
    ev_flags: list[str] = []
    for section, items in (("decisions", decisions), ("action_items", tasks), ("pending_issues", pendings)):
        for idx, item in enumerate(items):
            g = item_gold.get((section, idx))
            for ev in item.get("evidence") or []:
                if not isinstance(ev, dict):
                    continue
                ev_total += 1
                uid, quote = ev.get("utterance_id"), str(ev.get("exact_quote") or "")
                text = utt.get(uid)
                if text is None:
                    t1 += 1
                    ev_flags.append(f"tipo 1: {uid} no existe")
                    continue
                strict = quote in text
                normalized = norm_quote(quote) in fold(text)
                if not strict:
                    strict_fail += 1
                if not normalized:
                    elsewhere = [k for k, v in utt.items() if k != uid and norm_quote(quote) in fold(v)]
                    if elsewhere:
                        t1 += 1
                        ev_flags.append(f"tipo 1: cita de {elsewhere[0]} atribuida a {uid}")
                    else:
                        t2 += 1
                        ev_flags.append(f"tipo 2: {uid} cita no textual: {quote[:60]!r}")
                if g is None:
                    unmatched_ev += 1
                    continue
                support = set(g["respaldo"]) | set(g.get("respaldo_extra", []))
                if uid not in support:
                    t3 += 1
                    field_name = ev.get("field", "")
                    ev_flags.append(f"tipo 3 (proxy): {uid} citado para {g['id']}{' / ' + field_name if field_name else ''}")
    m["evidencias"] = {
        "total": ev_total,
        "tipo1_id_incorrecto": t1,
        "tipo2_no_textual": t2,
        "no_exactas_byte_a_byte": strict_fail,
        "tipo3_proxy_fuera_de_respaldo": t3,
        "de_items_sin_correspondencia": unmatched_ev,
    }
    m["errores_esquema"] = len(schema_errors)

    # ----- informe legible
    L = rep.lines
    L.append(f"### {name}".rstrip())
    L.append("")
    L.append("| Métrica | Valor |")
    L.append("|---|---|")
    d, t, p, e = m["decisiones"], m["tareas"], m["pendientes"], m["evidencias"]
    L.append(f"| JSON válido | {'sí' if json_valid else 'no (cortado; contenido puntuado sobre versión reparada)' if m['json_reparado'] else 'no'} |")
    L.append(f"| Errores de esquema | {m['errores_esquema']} |")
    L.append(f"| Decisiones correctas (de {d['gold']}) | {d['tp']}/{d['gold']} — precisión {d['precision']}, F1 {d['f1']} |")
    L.append(f"| Estados obsoletos (superseded) | {m['superseded_recuperados']}/{m['superseded_esperados']} |")
    L.append(f"| Tareas identificadas (de {t['gold']}) | {t['tp']}/{t['gold']} — precisión {t['precision']}, F1 {t['f1']} |")
    L.append(f"| Responsable exacto | {m['tareas_responsable_exacto']} |")
    L.append(f"| Plazo exacto | {m['tareas_plazo_exacto']} |")
    L.append(f"| Condición obligatoria presente | {m['tareas_condicion_requerida_presente']} |")
    L.append(f"| Pendientes identificados (de {p['gold']}) | {p['tp']}/{p['gold']} — precisión {p['precision']} |")
    L.append(f"| Personas ausentes asignadas | {m['personas_ausentes_asignadas']} |")
    L.append(f"| Citas: total | {e['total']} |")
    L.append(f"| Citas tipo 1 (ID incorrecto) | {e['tipo1_id_incorrecto']} |")
    L.append(f"| Citas tipo 2 (no textual) | {e['tipo2_no_textual']} (byte a byte: {e['no_exactas_byte_a_byte']}) |")
    L.append(f"| Citas tipo 3 (proxy: fuera del respaldo) | {e['tipo3_proxy_fuera_de_respaldo']} |")
    L.append("")
    L.append("Decisiones por ítem gold: " + ", ".join(f"{k} {v}" for k, v in m["decisiones_por_gold"].items()))
    L.append("")
    L.append("Tareas por ítem gold: " + ", ".join(f"{k} {v}" for k, v in m["tareas_por_gold"].items()))
    L.append("")
    L.append("<details><summary>Correspondencias y observaciones</summary>")
    L.append("")
    for pi, pred, g, ok_s, ok_v, ov in dec_rows:
        L.append(f"- decisión[{pi}] '{str(pred.get('topic'))[:45]}' state={pred.get('state')} → {g['id']} (IDs {','.join(ov)})"
                 f"{'' if ok_s else ' ESTADO INCORRECTO'}{'' if ok_v else ' FECHA/HORA INCORRECTA'}")
    for pi, pred, g, a_ok, d_ok, has_cond, ov in t_rows:
        gold_deadline = g["plazo"]
        flags = ("" if a_ok else " RESPONSABLE INCORRECTO") + ("" if d_ok else f" PLAZO INCORRECTO (gold {gold_deadline})")
        L.append(f"- tarea[{pi}] {pred.get('assignee')} / {pred.get('deadline')} → {g['id']} (IDs {','.join(ov)}){flags}")
    for h in absent_hits:
        L.append(f"- persona ausente asignada: {h}")
    for s in schema_errors:
        L.append(f"- esquema: {s}")
    for f_ in ev_flags:
        L.append(f"- {f_}")
    L.append("")
    L.append("</details>")
    return rep


def load_gold(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
