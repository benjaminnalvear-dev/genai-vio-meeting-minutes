"""Baseline: prompt directo (entregable 1), versión Python de run_model_test.ps1.

Envía el prompt directo + la transcripción completa en una sola llamada, con los
mismos parámetros del entregable 1, y guarda un registro JSON con el mismo formato
que producía el script de PowerShell.

Uso:
    python scripts/baseline.py
    python scripts/baseline.py --transcript pruebas/02_transcripcion.md
    python scripts/baseline.py --model ministral-vio --out resultados/baseline
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from common import DEFAULT_MODEL, DEFAULT_OPTIONS, REPO_ROOT, generate, ollama_version, parse_json_response

SEPARATOR = "\n\n--- TRANSCRIPCION A ANALIZAR ---\n\n"  # idéntico al .ps1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--prompt", default=str(REPO_ROOT / "pruebas" / "01_prompt_directo_ministral.md"))
    ap.add_argument("--transcript", default=str(REPO_ROOT / "pruebas" / "01_transcripcion_reunion_simulada.md"))
    ap.add_argument("--out", default=str(REPO_ROOT / "resultados" / "baseline"))
    ap.add_argument("--ctx", type=int, default=DEFAULT_OPTIONS["num_ctx"])
    ap.add_argument("--num-predict", type=int, default=DEFAULT_OPTIONS["num_predict"])
    ap.add_argument("--seed", type=int, default=DEFAULT_OPTIONS["seed"])
    ap.add_argument("--think", action="store_true")
    args = ap.parse_args()

    prompt_text = Path(args.prompt).read_text(encoding="utf-8")
    transcript_text = Path(args.transcript).read_text(encoding="utf-8")
    model_input = prompt_text + SEPARATOR + transcript_text

    options = {"num_ctx": args.ctx, "temperature": 0, "seed": args.seed, "num_predict": args.num_predict}
    print(f"Modelo: {args.model} | transcripción: {Path(args.transcript).name} | opciones: {options}")
    t0 = time.time()
    result = generate(model_input, model=args.model, options=options, think=args.think)
    wall = time.time() - t0

    parsed, valid = parse_json_response(result.get("response", ""))
    record = {
        "system": "baseline",
        "model": args.model,
        "ollama_version": ollama_version(),
        "transcript": Path(args.transcript).name,
        "prompt": Path(args.prompt).name,
        "context_size": args.ctx,
        "temperature": 0,
        "seed": args.seed,
        "output_limit": args.num_predict,
        "thinking_enabled": args.think,
        "created_at": datetime.now().astimezone().isoformat(),
        "wall_seconds": round(wall, 2),
        "load_duration_ns": result.get("load_duration"),
        "total_duration_ns": result.get("total_duration"),
        "prompt_eval_duration_ns": result.get("prompt_eval_duration"),
        "prompt_eval_count": result.get("prompt_eval_count"),
        "eval_duration_ns": result.get("eval_duration"),
        "eval_count": result.get("eval_count"),
        "done_reason": result.get("done_reason"),
        "response_json_valid": valid,
        "response_raw": result.get("response"),
        "response": parsed,
        "thinking": result.get("thinking"),
    }

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.transcript).stem.split("_")[0]
    safe_model = "".join(c if c.isalnum() or c in "._-" else "_" for c in args.model)
    out_path = out_dir / f"{stem}_baseline_{safe_model}_{datetime.now():%Y%m%d-%H%M%S}.json"
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    tps = (result.get("eval_count") or 0) / max((result.get("eval_duration") or 1) / 1e9, 1e-9)
    print(f"JSON válido: {valid} | fin: {result.get('done_reason')} | "
          f"{result.get('eval_count')} tokens en {wall:.1f} s ({tps:.2f} tok/s)")
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()
