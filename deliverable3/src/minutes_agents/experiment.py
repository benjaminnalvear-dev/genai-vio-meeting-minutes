"""Experiment runner: conditions, resumable per-meeting outputs, summary with provenance."""
from __future__ import annotations

import hashlib
import json
import os
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




def _load_result(path: Path) -> dict | None:
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None  # missing or truncated/corrupt: treat as not done
    return obj if isinstance(obj, dict) else None


def _write_atomic(path: Path, obj: dict) -> None:
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding='utf-8')
    os.replace(tmp, path)


def run_experiment(conditions: list[str], transcripts: dict, gold: dict, llm: LLM,
                   out_dir: Path, trace_dir: Path, *, meta_extra: dict | None = None,
                   log: Callable[[str], None] = print) -> dict:
    unknown = [c for c in conditions if c not in CONDITIONS]
    if unknown:
        raise ValueError(f'Unknown conditions: {unknown}; valid: {CONDITIONS}')
    out_dir, trace_dir = Path(out_dir), Path(trace_dir)
    failed: list[dict] = []
    for cond in conditions:
        cdir = out_dir / cond
        cdir.mkdir(parents=True, exist_ok=True)
        cfg = load_config(cond) if cond not in ('baseline', 'd2') else None
        for mid in sorted(transcripts):
            path = cdir / f'{mid}.json'
            if _load_result(path) is not None:
                log(f'[{cond}] {mid}  resumed')
                continue
            tr = transcripts[mid]
            try:
                if cond == 'baseline':
                    res = run_baseline(tr, llm)
                elif cond == 'd2':
                    res = run_d2_combined(tr, llm)
                else:
                    tdir = trace_dir / cond
                    tdir.mkdir(parents=True, exist_ok=True)
                    res = run_meeting(tr, llm, cfg, tdir / f'{mid}.jsonl')
            except Exception as e:  # one bad meeting must not abort the whole run
                failed.append({'condition': cond, 'meeting_id': mid, 'error': f'{type(e).__name__}: {e}'})
                log(f'[{cond}] {mid}  FAILED {type(e).__name__}: {e}')
                continue
            _write_atomic(path, res)
            log(f'[{cond}] {mid}  {res.get("seconds", 0):.1f}s  {res.get("calls", 1)} calls')
    # Summary is rebuilt from every condition directory present, not only those just run.
    summary: dict = {}
    per_cond: dict[str, dict] = {}
    evaluated: dict[str, list[str]] = {}
    for cond in CONDITIONS:
        if not (out_dir / cond).is_dir():
            continue
        outputs = {}
        for mid in sorted(transcripts):
            res = _load_result(out_dir / cond / f'{mid}.json')
            if res is not None:
                outputs[mid] = res
        if not outputs:
            continue
        is_base = cond == 'baseline'
        summary[cond] = {'primary': evaluate_arm(outputs, transcripts, gold, is_base, cond),
                         'extended': extended_metrics(outputs, transcripts, gold, is_base)}
        per_cond[cond] = summary[cond]['extended']['per_meeting']
        evaluated[cond] = sorted(outputs)
    if 'full' in per_cond and 'd2' in per_cond:
        common = [m for m in per_cond['full'] if m in per_cond['d2']]
        a = {m: per_cond['full'][m] for m in common}
        b = {m: per_cond['d2'][m] for m in common}
        summary['paired_full_vs_d2'] = {k: paired_comparison(a, b, k) for k in PAIRED_KEYS}
    meta = {'model': MODEL, 'params': PARAMS, 'ollama_version': None,
            'prompts': prompt_hashes(), 'conditions': [c for c in CONDITIONS if c in evaluated],
            'conditions_run': list(conditions), 'meeting_ids': sorted(transcripts),
            'evaluated_meetings': evaluated, 'failed': failed,
            'created': datetime.now(timezone.utc).isoformat()}
    meta.update(meta_extra or {})
    summary['meta'] = meta
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_atomic(out_dir / 'summary.json', summary)
    return summary
