"""Benchmark difficulty analysis. Usage: python scripts/benchmark_difficulty.py --data <dir> --out <dir>"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from minutes_agents.data import load_split  # noqa: E402
from minutes_agents.metrics import difficulty_table  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', type=Path, required=True, help='dir containing train/validation/test')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--split', default='test')
    a = ap.parse_args()
    rows = difficulty_table(*load_split(a.data, a.split))
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'difficulty_per_meeting.json').write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    tot = {k: sum(r[k] for r in rows) for k in rows[0]
           if k not in ('meeting', 'cadena_max', 'distancia_media_revision')}
    print('TOTAL', json.dumps(tot, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
