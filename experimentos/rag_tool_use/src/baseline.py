"""Baseline del D1: prompt directo canónico + transcripción, en una sola llamada.

Reproduce scripts/run_model_test.ps1: mismo texto de entrada, /api/generate, format=json,
num_ctx 8192, temperatura 0, seed 42, num_predict 3000.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import ollama_client

PROMPT_PATH = "pruebas/01_prompt_directo_ministral.md"
TRANSCRIPT_PATH = "pruebas/01_transcripcion_reunion_simulada.md"
SEPARATOR = "\n\n--- TRANSCRIPCION A ANALIZAR ---\n\n"
D1_PROMPT_EVAL_COUNT = 4196  # registrado en pruebas/01_salida_ministral_8k.md


def build_input(repo_root: Path, crlf: bool = False, transcript_path: Path | None = None,
                transcript_text: str | None = None) -> str:
    """Texto exacto que recibió el modelo en el D1 (o el mismo prompt con otra transcripción).

    El repo guarda LF. En Windows con core.autocrlf los archivos quedan con CRLF y el separador
    del script PowerShell usa LF; `crlf=True` reproduce esa variante.
    """
    prompt = (repo_root / PROMPT_PATH).read_text(encoding="utf-8-sig")
    transcript = transcript_text if transcript_text is not None else \
        Path(transcript_path or repo_root / TRANSCRIPT_PATH).read_text(encoding="utf-8-sig")
    if crlf:
        prompt = prompt.replace("\n", "\r\n")
        transcript = transcript.replace("\n", "\r\n")
    return prompt + SEPARATOR + transcript


def probe_input_variant(repo_root: Path) -> dict:
    """Mide prompt_eval_count de las dos variantes (1 token de salida) y elige la que coincide con el D1."""
    counts = {}
    for crlf in (False, True):
        rec = ollama_client.generate(build_input(repo_root, crlf), num_predict=1, keep_alive=0)
        counts["crlf" if crlf else "lf"] = rec["prompt_eval_count"]
    chosen = next((k for k, v in counts.items() if v == D1_PROMPT_EVAL_COUNT), "lf")
    return {"prompt_eval_count_por_variante": counts, "esperado_d1": D1_PROMPT_EVAL_COUNT,
            "variante_elegida": chosen, "coincide_con_d1": counts[chosen] == D1_PROMPT_EVAL_COUNT}


def run(repo_root: Path, crlf: bool = False, transcript_path: Path | None = None,
        transcript_text: str | None = None) -> dict:
    text = build_input(repo_root, crlf, transcript_path, transcript_text)
    num_ctx = ollama_client.DEFAULT_OPTIONS["num_ctx"]
    approx = int(len(text) / 2.5)
    if approx + 3000 > num_ctx:
        print(f"ADVERTENCIA: la entrada del baseline (~{approx} tokens) más la salida (3000) no cabe en "
              f"num_ctx={num_ctx}; Ollama recortará el principio, como en la corrida de 4K del D1.")
    record = ollama_client.generate(text, num_predict=3000)
    try:
        acta = json.loads(record["response_raw"])
        valid = True
    except json.JSONDecodeError:
        acta, valid = None, False
    record.update({"condicion": "baseline", "variante_entrada": "crlf" if crlf else "lf",
                   "response_json_valid": valid, "acta": acta, "n_llamadas": 1})
    return record
