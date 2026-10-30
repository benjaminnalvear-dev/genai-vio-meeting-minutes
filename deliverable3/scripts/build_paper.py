"""Build the one-page technical document and refuse anything that is not exactly one page.

Usage (from deliverable3/): python scripts/build_paper.py [--tectonic <path to tectonic>]
Needs latexmk (MiKTeX / TeX Live) or Tectonic (single binary, https://tectonic-typesetting.github.io).
Regenerates the English
figures from runs/test/results/summary.json, compiles paper/D3.tex and copies the PDF to
the repository root as Deliverable_3.pdf.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper'
TARGET = ROOT.parent / 'Deliverable_3.pdf'


def page_count(log_text: str) -> int | None:
    m = re.search(r'Output written on \S+ \((\d+) pages?', log_text)
    return int(m[1]) if m else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--tectonic', default=None, help='use this Tectonic binary instead of latexmk')
    a = ap.parse_args(argv)
    subprocess.run([sys.executable, str(ROOT / 'scripts' / 'make_figures.py'), '--summary',
                    str(ROOT / 'runs' / 'test' / 'results' / 'summary.json'), '--out',
                    str(PAPER / 'figures'), '--lang', 'en', '--overview',
                    '--heatmap-conds', 'baseline,d2,full,no_fewshot'], check=True, stdout=subprocess.DEVNULL)
    cmd = ([a.tectonic, '--keep-logs', 'D3.tex'] if a.tectonic
           else ['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error', 'D3.tex'])
    r = subprocess.run(cmd,
                       cwd=PAPER, capture_output=True, text=True, encoding='utf-8', errors='replace')
    log = (PAPER / 'D3.log').read_text(encoding='utf-8', errors='replace') if (PAPER / 'D3.log').exists() else ''
    if r.returncode != 0:
        print((r.stdout + r.stderr)[-3000:], file=sys.stderr)
        print('LaTeX failed; see paper/D3.log', file=sys.stderr)
        return 1
    pages = page_count(log)
    if pages != 1:
        print(f'ERROR: the PDF has {pages} pages; the deliverable must be exactly 1 page.', file=sys.stderr)
        return 2
    overfull = len(re.findall(r'^Overfull \\hbox', log, flags=re.M))
    shutil.copyfile(PAPER / 'D3.pdf', TARGET)
    print(f'OK: 1 page -> {TARGET}' + (f' ({overfull} overfull hbox warnings)' if overfull else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
