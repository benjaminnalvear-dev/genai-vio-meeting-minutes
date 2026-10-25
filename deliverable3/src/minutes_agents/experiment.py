"""Experiment runner: conditions, resumable per-meeting outputs, summary with provenance."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from minutes_agents.agents.base import RunConfig
from minutes_agents.d2_reference import run_baseline, run_d2_combined
from minutes_agents.evaluate import evaluate_arm
from minutes_agents.graph import run_meeting
from minutes_agents.llm import LLM, MODEL, PARAMS
from minutes_agents.metrics import extended_metrics, paired_comparison
from minutes_agents.prompts import PROMPTS_DIR

CONDITIONS = ['baseline', 'd2', 'full', 'no_react', 'no_auditor', 'no_fewshot', 'no_cot']
CONFIGS_DIR = Path(__file__).resolve().parents[2] / 'configs'
PAIRED_KEYS = ('decisions_f1', 'tasks_f1', 'strict_f1')


def load_config(name: str) -> RunConfig:
    data = json.loads((CONFIGS_DIR / f'{name}.json').read_text(encoding='utf-8'))
    return RunConfig(**data)


def prompt_hashes(prompts_dir: Path = PROMPTS_DIR) -> dict[str, str]:
    return {p.relative_to(prompts_dir).as_posix():
            hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
            for p in sorted(Path(prompts_dir).rglob('*.md'))}


def run_experiment(conditions: list[str], transcripts: dict, gold: dict, llm: LLM,
                   out_dir: Path, trace_dir: Path, *, meta_extra: dict | None = None,
                   log: Callable[[str], None] = print) -> dict:
    unknown = [c for c in conditions if c not in CONDITIONS]
    if unknown:
        raise ValueError(f'Unknown conditions: {unknown}; valid: {CONDITIONS}')
    out_dir, trace_dir = Path(out_dir), Path(trace_dir)
    summary: dict = {}
    per_cond: dict[str, dict] = {}
    for cond in conditions:
        cdir = out_dir / cond
        cdir.mkdir(parents=True, exist_ok=True)
        cfg = load_config(cond) if cond not in ('baseline', 'd2') else None
        outputs = {}
        for mid in sorted(transcripts):
            path = cdir / f'{mid}.json'
            if path.exists():
                outputs[mid] = json.loads(path.read_text(encoding='utf-8'))
                log(f'[{cond}] {mid}  resumed')
                continue
            tr = transcripts[mid]
            if cond == 'baseline':
                res = run_baseline(tr, llm)
            elif cond == 'd2':
                res = run_d2_combined(tr, llm)
            else:
                tdir = trace_dir / cond
                tdir.mkdir(parents=True, exist_ok=True)
                res = run_meeting(tr, llm, cfg, tdir / f'{mid}.jsonl')
            path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
            outputs[mid] = res
            log(f'[{cond}] {mid}  {res.get("seconds", 0):.1f}s  {res.get("calls", 1)} calls')
        is_base = cond == 'baseline'
        summary[cond] = {'primary': evaluate_arm(outputs, transcripts, gold, is_base, cond),
                         'extended': extended_metrics(outputs, transcripts, gold, is_base)}
        per_cond[cond] = summary[cond]['extended']['per_meeting']
    if 'full' in per_cond and 'd2' in per_cond:
        summary['paired_full_vs_d2'] = {k: paired_comparison(per_cond['full'], per_cond['d2'], k)
                                        for k in PAIRED_KEYS}
    meta = {'model': MODEL, 'params': PARAMS, 'ollama_version': None,
            'prompts': prompt_hashes(), 'conditions': list(conditions),
            'meeting_ids': sorted(transcripts),
            'created': datetime.now(timezone.utc).isoformat()}
    meta.update(meta_extra or {})
    summary['meta'] = meta
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding='utf-8')
    return summary
