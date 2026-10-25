"""Package deliverable3/ as a zip to upload to Colab (the repo is not pushed yet).

Usage (from deliverable3/): python scripts/package_for_colab.py [--out dist/deliverable3_colab.zip]
"""
import argparse
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {'.venv', '.cache', 'dist', 'results', 'traces', '__pycache__', '.pytest_cache'}
ARC_ROOT = 'deliverable3'


def git_head() -> str:
    try:
        r = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True,
                           text=True, check=True)
        return r.stdout.strip() or 'unknown'
    except Exception:
        return 'unknown'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=ROOT / 'dist' / 'deliverable3_colab.zip')
    a = ap.parse_args(argv)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    commit = git_head()
    n = 0
    with zipfile.ZipFile(a.out, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob('*')):
            rel = p.relative_to(ROOT)
            if not p.is_file() or EXCLUDE_DIRS & set(rel.parts) or p.suffix == '.pyc':
                continue
            z.write(p, f'{ARC_ROOT}/{rel.as_posix()}')
            n += 1
        z.writestr(f'{ARC_ROOT}/COMMIT.txt', commit + '\n')
    print(f'commit {commit}; {n + 1} files; {a.out} ({a.out.stat().st_size / 1e6:.2f} MB)')


if __name__ == '__main__':
    main()
