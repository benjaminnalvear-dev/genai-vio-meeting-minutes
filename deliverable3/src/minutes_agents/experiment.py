"""Experiment runner: conditions, resumable per-meeting outputs, summary with provenance."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import asdict
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
PACKAGE_ROOT = Path(__file__).resolve().parents[2]  # deliverable3/
CONFIGS_DIR = PACKAGE_ROOT / 'configs'
PAIRED_KEYS = ('decisions_f1', 'tasks_f1', 'strict_f1')


def load_config(name: str) -> RunConfig:
    data = json.loads((CONFIGS_DIR / f'{name}.json').read_text(encoding='utf-8'))
    return RunConfig(**data)


def prompt_hashes(prompts_dir: Path = PROMPTS_DIR) -> dict[str, str]:
    return {p.relative_to(prompts_dir).as_posix():
            hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
            for p in sorted(Path(prompts_dir).rglob('*.md'))}


def package_commit(root: Path = PACKAGE_ROOT) -> str | None:
    """Commit del código: COMMIT.txt (zip para Colab) o `git rev-parse --short HEAD`; None si no hay."""
    f = Path(root) / 'COMMIT.txt'
    if f.exists():
        return f.read_text(encoding='utf-8').strip() or None
    try:
        r = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=root, capture_output=True,
                           text=True, check=True, timeout=10)
        return r.stdout.strip() or None
    except Exception:
        return None


def _provenance(cfg: RunConfig | None, hashes: dict[str, str]) -> dict:
    return {'prompt_hashes': hashes, 'run_config': asdict(cfg) if cfg is not None else None}


def _is_current(res: dict, prov: dict) -> bool:
    return all(res.get(k) == v for k, v in prov.items())


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
    hashes = prompt_hashes()
    failed: list[dict] = []
    computed: set[str] = set()
    for cond in conditions:
        cdir = out_dir / cond
        cdir.mkdir(parents=True, exist_ok=True)
        cfg = load_config(cond) if cond not in ('baseline', 'd2') else None
        prov = _provenance(cfg, hashes)
        for mid in sorted(transcripts):
            path = cdir / f'{mid}.json'
            prev = _load_result(path)
            if prev is not None and _is_current(prev, prov):
                log(f'[{cond}] {mid}  resumed')
                continue
            if prev is not None:
                log(f'[{cond}] {mid}  stale result (prompts or config changed): recomputing')
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
            res.update(prov)
            _write_atomic(path, res)
            computed.add(cond)
            log(f'[{cond}] {mid}  {res.get("seconds", 0):.1f}s  {res.get("calls", 1)} calls')
    # Summary is rebuilt from every condition directory present, not only those just run.
    summary: dict = {}
    per_cond: dict[str, dict] = {}
    evaluated: dict[str, list[str]] = {}
    stale: list[dict] = []
    for cond in CONDITIONS:
        if not (out_dir / cond).is_dir():
            continue
        outputs = {}
        for mid in sorted(transcripts):
            res = _load_result(out_dir / cond / f'{mid}.json')
            if res is not None:
                outputs[mid] = res
                cfg = load_config(cond) if cond not in ('baseline', 'd2') else None
                if not _is_current(res, _provenance(cfg, hashes)):
                    stale.append({'condition': cond, 'meeting_id': mid})
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
    extra = dict(meta_extra or {})
    meta = {'model': MODEL, 'params': PARAMS, 'ollama_version': None, 'model_digest': None,
            'package_commit': package_commit(),
            'prompts': hashes, 'conditions': [c for c in CONDITIONS if c in evaluated],
            'conditions_run': list(conditions), 'meeting_ids': sorted(transcripts),
            'evaluated_meetings': evaluated, 'failed': failed, 'stale_results': stale,
            'created': datetime.now(timezone.utc).isoformat()}
    meta.update(extra)
    # Versión de Ollama / digest del modelo con que se calculó cada condición (se acumula entre
    # invocaciones; solo se actualiza para condiciones con al menos una reunión recalculada).
    prev_meta = (_load_result(out_dir / 'summary.json') or {}).get('meta') or {}
    for key in ('ollama_version', 'model_digest'):
        by_cond = {c: v for c, v in (prev_meta.get(f'{key}_by_condition') or {}).items() if c in evaluated}
        for c in computed:
            by_cond[c] = meta.get(key)
        meta[f'{key}_by_condition'] = by_cond
    summary['meta'] = meta
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_atomic(out_dir / 'summary.json', summary)
    return summary
