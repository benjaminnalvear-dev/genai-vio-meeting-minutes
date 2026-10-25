"""Run ablation experiment. Usage (from deliverable3/):
python scripts/run_experiment.py --data <dir|Fine Tuning.zip> --split test --conditions full,d2 --out results/test
"""
import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import requests  # noqa: E402

from minutes_agents.data import extract_dataset, load_split  # noqa: E402
from minutes_agents.experiment import CONDITIONS, run_experiment  # noqa: E402
from minutes_agents.llm import MODEL, CachedLLM, OllamaError, OllamaLLM, preflight  # noqa: E402


def ollama_version(host: str):
    try:
        return requests.get(f'{host.rstrip("/")}/api/version', timeout=10).json().get('version')
    except Exception:
        return None


def model_digest(host: str, model: str = MODEL):
    try:
        tags = requests.get(f'{host.rstrip("/")}/api/tags', timeout=10).json().get('models', [])
        return next((m.get('digest') for m in tags if model in (m.get('name'), m.get('model'))), None)
    except Exception:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', type=Path, required=True, help='dir with train/validation/test, or Fine Tuning.zip')
    ap.add_argument('--split', choices=['validation', 'test'], default='test')
    ap.add_argument('--conditions', default=','.join(CONDITIONS), help='comma list of: ' + ','.join(CONDITIONS))
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--traces', type=Path, default=Path('traces'))
    ap.add_argument('--host', default='http://127.0.0.1:11434')
    ap.add_argument('--cache', type=Path, default=Path('.cache/llm'))
    ap.add_argument('--demo', action='store_true', help='first meeting only')
    ap.add_argument('--limit', type=int, default=None, help='first N meetings (smoke runs)')
    a = ap.parse_args(argv)
    conds = [c.strip() for c in a.conditions.split(',') if c.strip()]
    bad = [c for c in conds if c not in CONDITIONS]
    if bad:
        ap.error(f'unknown conditions {bad}; valid: {CONDITIONS}')
    with tempfile.TemporaryDirectory() as tmp:
        root = extract_dataset(a.data, Path(tmp)) if a.data.suffix.lower() == '.zip' else a.data
        transcripts, gold = load_split(root, a.split)
    ids = sorted(transcripts)
    n = 1 if a.demo else a.limit
    if n is not None:
        ids = ids[:n]
    transcripts, gold = {m: transcripts[m] for m in ids}, {m: gold[m] for m in ids}
    print('Verificando Ollama (servidor, modelo y una llamada de prueba)...', flush=True)
    try:
        preflight(a.host)
    except OllamaError as exc:
        print('!' * 70)
        print(f'!!! OLLAMA NO ESTÁ LISTO: {exc}')
        print('!!! No se ejecutó ninguna reunión. Revisa /content/ollama_serve.log, reinicia la celda 2 y repite.')
        print('!' * 70, flush=True)
        sys.exit(2)
    print('Ollama OK.', flush=True)
    llm = CachedLLM(OllamaLLM(host=a.host), a.cache)
    summary = run_experiment(conds, transcripts, gold, llm, a.out, a.traces,
                             meta_extra={'ollama_version': ollama_version(a.host),
                                         'model_digest': model_digest(a.host), 'split': a.split,
                                         'demo': a.demo, 'limit': a.limit})
    for c in conds:
        if c not in summary:
            print(f'{c}: NO RESULTS (every meeting failed)')
            continue
        p = summary[c]['primary']
        print(f"{c}: decisions F1 {p['decisions']['f1']}  tasks F1 {p['tasks']['f1']}")
    failed = summary['meta'].get('failed') or []
    if failed:
        print()
        print(f'!!! {len(failed)} FAILED MEETING(S) - rerun the same command to retry them:')
        for f in failed:
            print(f"!!!   [{f['condition']}] {f['meeting_id']}: {f['error']}")
    return summary


if __name__ == '__main__':
    main()
