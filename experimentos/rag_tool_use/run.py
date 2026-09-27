"""Punto de entrada del experimento D2 (retrieval + tool use con Ministral 3 3B).

Uso (desde experimentos/rag_tool_use/):
  python run.py baseline                 # prompt directo del D1, una llamada
  python run.py pipeline --config tool_bloques   # solución propuesta S2 (ver src/pipeline.py: CONFIGS)
  python run.py todo                     # baseline + todas las configuraciones + comparación
  python run.py score resultados/<hw>/baseline.json
  python run.py compare resultados/<hw>
  python run.py tabla-d1 resultados/<hw>  # tabla con los criterios del D1 (usa adjudicacion_tareas.json)
  python run.py score ../../pruebas/01_salida_ministral_8k.md   # salida del D1
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))

from src import baseline, ollama_client  # noqa: E402
from src.score import load_acta, load_gold, score  # noqa: E402
from src.transcript import load_meeting  # noqa: E402

GOLD = HERE / "gold" / "01_gold.json"
TRANSCRIPT = REPO / baseline.TRANSCRIPT_PATH


def hardware_tag(env: dict) -> str:
    raw = env.get("gpu") or env.get("cpu") or platform.machine()
    return re.sub(r"[^a-z0-9]+", "-", raw.split(",")[0].lower()).strip("-")


def save(record: dict, out_dir: Path, name: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def score_file(path: Path, name: str | None = None):
    acta, valid, raw = load_acta(path)
    rep = score(acta, valid, load_gold(GOLD), load_meeting(TRANSCRIPT), name or path.stem, raw)
    return rep


def cmd_baseline(args) -> Path:
    env = ollama_client.environment()
    probe = baseline.probe_input_variant(REPO)
    print("Entrada:", probe)
    started = time.time()
    record = baseline.run(REPO, crlf=probe["variante_elegida"] == "crlf")
    record.update({"entorno": env, "chequeo_entrada": probe, "wall_total_s": round(time.time() - started, 2)})
    out = save(record, Path(args.out or HERE / "resultados" / hardware_tag(env)), "baseline")
    print(f"Guardado: {out}  ({record['eval_count']} tokens, {record['wall_total_s']} s, {record['tok_per_s']} tok/s)")
    print(score_file(out, "baseline").md())
    return out


def cmd_pipeline(args) -> Path:
    from src import pipeline
    env = ollama_client.environment()
    record = pipeline.run(load_meeting(TRANSCRIPT), args.config)
    record["entorno"] = env
    out = save(record, Path(args.out or HERE / "resultados" / hardware_tag(env)), f"pipeline_{args.config}")
    print(f"Guardado: {out}  ({record['n_llamadas']} llamadas, {record['eval_count']} tokens, {record['wall_total_s']} s)")
    print(score_file(out, f"pipeline_{args.config}").md())
    return out


def acta_markdown(acta: dict, meeting) -> str:
    """Versión legible del acta (el JSON es el entregable; esto es para leerla)."""
    L = [f"# Acta — {meeting.topic or 'reunión'} ({meeting.date.isoformat()})", ""]
    ev = lambda it: ", ".join(dict.fromkeys(e["utterance_id"] for e in it.get("evidence", [])))
    decs = acta.get("decisions", [])
    for title, state in (("Decisiones finales", "final"), ("Reemplazadas (superseded)", "superseded"), ("Rechazadas", "rejected")):
        rows = [d for d in decs if d.get("state") == state]
        if rows:
            L += [f"## {title}", ""] + [f"- {d.get('topic')}: {d.get('outcome')} ({ev(d)})" for d in rows] + [""]
    tasks = acta.get("action_items", [])
    if tasks:
        L += ["## Tareas", "", "| Responsable | Tarea | Plazo | Condición | Evidencia |", "|---|---|---|---|---|"]
        L += [f"| {t.get('assignee') or '—'} | {t.get('task')} | {t.get('deadline') or '—'} | {t.get('conditions') or '—'} | {ev(t)} |" for t in tasks]
        L.append("")
    if acta.get("pending_issues"):
        L += ["## Pendientes", ""] + [f"- {p.get('issue')} ({ev(p)})" for p in acta["pending_issues"]] + [""]
    if acta.get("review_alerts"):
        L += ["## Alertas de revisión", ""] + [f"- {a.get('alert')} — {a.get('reason', '')}" for a in acta["review_alerts"]] + [""]
    return "\n".join(L)


def cmd_acta(args):
    """Acta de cualquier transcripción (por defecto con el modo auto)."""
    from src import pipeline
    from src.transcript import to_canonical
    path = Path(args.transcripcion)
    meeting = load_meeting(path, fecha=args.fecha, presentes=args.presentes, ausentes=args.ausentes, tema=args.tema)
    for w in meeting.warnings:
        print("AVISO:", w)
    print(f"{len(meeting.utterances)} intervenciones · {meeting.date} · presentes: {', '.join(meeting.first_names())}"
          f" · ausentes: {', '.join(meeting.absent_mentioned) or 'ninguno'}")
    env = ollama_client.environment()
    if args.config == "baseline":
        is_01 = path.resolve() == TRANSCRIPT.resolve()
        record = baseline.run(REPO, transcript_path=path if is_01 else None,
                              transcript_text=None if is_01 else to_canonical(meeting))
    else:
        record = pipeline.run(meeting, args.config)
    record.update({"entorno": env, "transcripcion": str(path)})
    out_dir = Path(args.out or HERE / "resultados" / hardware_tag(env) / "actas")
    name = f"{path.stem}_{args.config}"
    out = save(record, out_dir, name)
    acta, valid, raw = load_acta(out)
    if acta is not None:
        md = acta_markdown(acta, meeting)
        (out_dir / f"{name}.md").write_text(md + "\n", encoding="utf-8")
        print(md)
    print(f"Guardado: {out} (y {name}.md) · modos: {record.get('modos_usados', ['baseline'])} · "
          f"{record.get('n_llamadas', 1)} llamadas · {record.get('wall_total_s', record.get('wall_s'))} s")
    for line in record.get("registro_log", []):
        if "ADVERTENCIA" in line or "reunión larga" in line or "recorte" in line:
            print("  ", line)
    if args.gold:
        print(score(acta, valid, load_gold(args.gold), meeting, name, raw).md())


def cmd_score(args):
    for p in args.files:
        print(score_file(Path(p)).md())
        print()


def compare(folder: Path) -> str:
    from src import pipeline
    order = ["baseline"] + [f"pipeline_{c}" for c in pipeline.EVAL_CONFIGS]
    files = {p.stem: p for p in folder.glob("*.json")}
    names = [n for n in order if n in files]
    gold, meeting = load_gold(GOLD), load_meeting(TRANSCRIPT)
    rows = {}
    for n in names:
        rec = json.loads(files[n].read_text(encoding="utf-8"))
        acta, valid, raw = load_acta(files[n])
        m = score(acta, valid, gold, meeting, n, raw).metrics
        rows[n] = (m, rec)

    def g(n, f):
        m, rec = rows[n]
        return f(m, rec)

    metrics = [
        ("JSON válido", lambda m, r: "sí" if m["json_valido"] else "no (cortado)" if m.get("json_reparado") else "no"),
        ("Errores de esquema", lambda m, r: m.get("errores_esquema", "-")),
        ("Decisiones correctas", lambda m, r: f"{m['decisiones']['tp']}/{m['decisiones']['gold']}" if "decisiones" in m else "-"),
        ("Precisión decisiones", lambda m, r: m["decisiones"]["precision"] if "decisiones" in m else "-"),
        ("Estados obsoletos", lambda m, r: f"{m['superseded_recuperados']}/{m['superseded_esperados']}" if "superseded_recuperados" in m else "-"),
        ("Tareas identificadas", lambda m, r: f"{m['tareas']['tp']}/{m['tareas']['gold']}" if "tareas" in m else "-"),
        ("Precisión tareas", lambda m, r: m["tareas"]["precision"] if "tareas" in m else "-"),
        ("Responsable exacto", lambda m, r: m.get("tareas_responsable_exacto", "-")),
        ("Plazo exacto", lambda m, r: m.get("tareas_plazo_exacto", "-")),
        ("Condición obligatoria", lambda m, r: m.get("tareas_condicion_requerida_presente", "-")),
        ("Pendientes", lambda m, r: f"{m['pendientes']['tp']}/{m['pendientes']['gold']}" if "pendientes" in m else "-"),
        ("Personas ausentes asignadas", lambda m, r: m.get("personas_ausentes_asignadas", "-")),
        ("Citas no textuales (tipo 1+2)", lambda m, r: (m["evidencias"]["tipo1_id_incorrecto"] + m["evidencias"]["tipo2_no_textual"]) if "evidencias" in m else "-"),
        ("Citas byte a byte no exactas", lambda m, r: m["evidencias"]["no_exactas_byte_a_byte"] if "evidencias" in m else "-"),
        ("Citas tipo 3 (proxy)", lambda m, r: m["evidencias"]["tipo3_proxy_fuera_de_respaldo"] if "evidencias" in m else "-"),
        ("Llamadas al modelo", lambda m, r: r.get("n_llamadas", 1)),
        ("Tokens generados", lambda m, r: r.get("eval_count")),
        ("Tokens de entrada", lambda m, r: r.get("prompt_eval_count")),
        ("Tiempo total (s)", lambda m, r: r.get("wall_total_s", r.get("wall_s"))),
    ]
    lines = ["| Métrica | " + " | ".join(pipeline.LABELS.get(n, n) for n in names) + " |", "|---|" + "---|" * len(names)]
    for label, f in metrics:
        lines.append(f"| {label} | " + " | ".join(str(g(n, f)) for n in names) + " |")
    env = rows[names[0]][1].get("entorno", {}) if names else {}
    lines.append("")
    lines.append(f"Hardware: {env.get('gpu') or env.get('cpu')} · Ollama {env.get('ollama_version')} · "
                 f"modelo {env.get('model')} ({env.get('model_digest_short')})")
    return "\n".join(lines)


D1_OUTPUT = REPO / "pruebas" / "01_salida_ministral_8k.md"
D1_TIME = "22m06s (i5-9300H + GTX 1050)"
OMITTED_IN_D1 = ("D7", "D8", "D9")   # demo remota, credencial + QA, bloqueadores (auditoría D1, error 3)


def _deadline(value):
    if isinstance(value, str) and value.strip().lower() in {"null", "none", ""}:
        return None
    return value.strip() if isinstance(value, str) else value


def _is_12h_shift(pred, gold) -> bool:
    try:
        (pd, pt), (gd, gt) = pred.split(" "), gold.split(" ")
        (ph, pm), (gh, gm) = map(int, pt.split(":")), map(int, gt.split(":"))
    except (AttributeError, ValueError):
        return False
    return pd == gd and pm == gm and abs(ph - gh) == 12


def tabla_d1(folder: Path) -> str:
    """Tabla con las filas de la tabla de Ministral del D1, más la salida original del D1 como referencia."""
    from src import pipeline
    from src.score import repair_truncated
    gold, meeting = load_gold(GOLD), load_meeting(TRANSCRIPT)
    adj_path = folder / "adjudicacion_tareas.json"
    adj = json.loads(adj_path.read_text(encoding="utf-8"))["condiciones"] if adj_path.exists() else {}
    runs = [("d1_original", "D1 original", D1_OUTPUT, None)]
    for stem, label in pipeline.LABELS.items():
        if (folder / f"{stem}.json").exists():
            runs.append((stem, label, folder / f"{stem}.json", json.loads((folder / f"{stem}.json").read_text(encoding="utf-8"))))
    gold_tasks = {t["id"]: t for t in gold["tareas"]}
    cols = []
    for key, label, path, rec in runs:
        acta, valid, raw = load_acta(path)
        m = score(acta, valid, gold, meeting, key, raw).metrics
        acta = acta or repair_truncated(raw)
        tasks = acta["action_items"]
        a = adj.get(key)
        if a:
            recovered = {g: i for g, i in a["recuperadas"].items() if i is not None}
            mixed, split, extra = len(a["mezcladas"]), len(a["partidas"]), len(a["extra"])
        else:  # sin revisión manual: emparejamiento automático por IDs (puede equivocarse con duplicados)
            from src.score import first_name, fold, match_items
            recovered = {mt.gold["id"]: mt.pred_index for mt in match_items(
                tasks, gold["tareas"], lambda p, g: first_name(p.get("assignee")) == fold(g["responsable"]))}
            mixed = split = extra = None
        t3 = "tarea omitida"
        ampm = other = 0
        for gid, idx in recovered.items():
            if idx is None:
                continue
            pred = _deadline(tasks[idx].get("deadline"))
            g = gold_tasks[gid]
            ok = pred in g.get("plazos_aceptados", [g["plazo"]])
            if gid == "T3":
                t3 = f"{'✓' if ok else '✗'} {pred.split(' ')[-1] if pred else 'sin plazo'}"
            if not ok:
                if pred and g["plazo"] and _is_12h_shift(pred, g["plazo"]):
                    ampm += 1
                else:
                    other += 1
        d = m["decisiones_por_gold"]
        e = m["evidencias"]
        bad_ev = e["tipo1_id_incorrecto"] + e["tipo2_no_textual"] + e["tipo3_proxy_fuera_de_respaldo"]
        final_date = {"ok": "fecha final correcta", "omitida": "fecha final omitida"}.get(d["D3"], "fecha final incorrecta")
        support = {"ok": "recuperada", "omitida": "omitida"}.get(d["D5"], "estado incorrecto")
        if rec is None:
            time_cell = D1_TIME
        else:
            env = rec.get("entorno", {})
            hw = (env.get("gpu") or env.get("cpu") or "").split(",")[0]
            time_cell = f"{rec.get('wall_total_s', rec.get('wall_s')):.0f} s ({hw}; {rec.get('eval_count')} tokens)"
        cols.append((label, {
            "Salida final": f"JSON {'válido' if m['json_valido'] else 'inválido'}; {m['errores_esquema']} errores de esquema",
            "Historial apertura": f"{m['superseded_recuperados']}/2 estados obsoletos; {final_date}",
            "Decisiones clave: soporte solo por correo (U030)": support,
            "Decisiones clave: demo remota, credencial + QA, bloqueadores (omitidas en el D1)": f"{sum(d[k] == 'ok' for k in OMITTED_IN_D1)}/3",
            "Tareas": (f"Escribió {len(tasks)}; recuperó {len(recovered)}/7; mezcló {mixed}" if mixed is not None
                       else f"Escribió {len(tasks)}; recuperó {len(recovered)}/7 (automático)"),
            "Tareas partidas o duplicadas": "-" if split is None else str(split),
            "Tareas extra (no están en el gold)": "-" if extra is None else str(extra),
            "Plazos: regresión de Martín (13:00)": t3,
            "Plazos: errores de 12 h (am/pm)": str(ampm),
            "Plazos: otros plazos incorrectos": str(other),
            "Enlaces de evidencia incorrectos (automático)": f"{bad_ev}/{e['total']}",
            "Personas ausentes asignadas": str(m["personas_ausentes_asignadas"]),
            "Tiempo": time_cell,
        }))
    rows = list(cols[0][1])
    out = ["| Criterio del D1 | " + " | ".join(c[0] for c in cols) + " |", "|---|" + "---|" * len(cols)]
    for r in rows:
        out.append(f"| {r} | " + " | ".join(c[1][r] for c in cols) + " |")
    return "\n".join(out)


def cmd_tabla_d1(args):
    folder = Path(args.folder)
    table = tabla_d1(folder)
    (folder / "tabla_d1.md").write_text(table + "\n", encoding="utf-8")
    print(table)


def cmd_compare(args):
    folder = Path(args.folder)
    table = compare(folder)
    (folder / "comparacion.md").write_text(table + "\n", encoding="utf-8")
    print(table)


def cmd_todo(args):
    from src import pipeline
    out = cmd_baseline(args)
    for cfg in pipeline.EVAL_CONFIGS:
        args.config = cfg
        cmd_pipeline(args)
    args.folder = str(out.parent)
    cmd_compare(args)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # consolas Windows (cp1252)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("baseline"); b.add_argument("--out"); b.set_defaults(fn=cmd_baseline)
    p = sub.add_parser("pipeline"); p.add_argument("--config", default="tool_bloques", choices=["tool_1pasada", "tool_bloques", "tool_bloques_rag", "tool_bloques_rag_verif", "tool_bloques_rag2", "tool_bloques_pasado"]); p.add_argument("--out"); p.set_defaults(fn=cmd_pipeline)
    s = sub.add_parser("score"); s.add_argument("files", nargs="+"); s.set_defaults(fn=cmd_score)
    c = sub.add_parser("compare"); c.add_argument("folder"); c.set_defaults(fn=cmd_compare)
    t = sub.add_parser("todo"); t.add_argument("--out"); t.set_defaults(fn=cmd_todo)
    d = sub.add_parser("tabla-d1"); d.add_argument("folder"); d.set_defaults(fn=cmd_tabla_d1)
    a = sub.add_parser("acta", help="acta de cualquier transcripción")
    a.add_argument("transcripcion")
    a.add_argument("--config", default="auto", choices=["auto", "baseline", "tool_1pasada", "tool_bloques",
                                                         "tool_bloques_rag", "tool_bloques_rag_verif", "tool_bloques_rag2"])
    a.add_argument("--fecha", help="AAAA-MM-DD si la transcripción no la trae")
    a.add_argument("--presentes", help="'Ana Díaz, Luis Mora' (reemplaza la cabecera)")
    a.add_argument("--ausentes", help="'Marta, Pedro' (personas mencionadas que no están)")
    a.add_argument("--tema")
    a.add_argument("--gold", help="gold JSON con la estructura de gold/01_gold.json, para puntuar")
    a.add_argument("--out")
    a.set_defaults(fn=cmd_acta)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
