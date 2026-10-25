"""Result figures for the paper: F1 by condition and trap-category heatmap.

CLI: python scripts/make_figures.py --summary <summary.json> --out <dir>
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from minutes_agents.experiment import CONDITIONS  # noqa: E402

LABELS = {'baseline': 'Prompt directo', 'd2': 'D2', 'full': 'Agentes', 'no_react': '− ReAct',
          'no_auditor': '− Auditor', 'no_fewshot': '− Few-shot', 'no_cot': '− CoT',
          'no_guards': '− Barandas'}
REFERENCE = ('baseline', 'd2')
C_DEC, C_TASK = '#2a6fb0', '#d9822b'   # colorblind-safe blue / orange
INK = '#222222'
FS = 7.5
COL_W = 3.4


def _style():
    plt.rcParams.update({'font.size': FS, 'axes.labelsize': FS, 'xtick.labelsize': FS,
                         'ytick.labelsize': FS, 'font.family': 'DejaVu Sans',
                         'axes.edgecolor': '#888888', 'pdf.fonttype': 42})


def _save(fig, out_dir: Path, stem: str) -> list[Path]:
    paths = []
    for ext in ('pdf', 'png'):
        p = out_dir / f'{stem}.{ext}'
        fig.savefig(p, dpi=200, bbox_inches='tight', pad_inches=0.03)
        paths.append(p)
    plt.close(fig)
    return paths


def _has_f1(cond) -> bool:
    try:
        vals = (cond['primary']['decisions']['f1'], cond['primary']['tasks']['f1'],
                cond['extended']['strict_f1']['decisions'], cond['extended']['strict_f1']['tasks'])
    except (KeyError, TypeError):
        return False
    return all(isinstance(v, (int, float)) for v in vals)


def bar_conditions(summary) -> list[str]:
    """Conditions with all four F1 values; others are skipped with a stderr warning."""
    out = []
    for c in present_conditions(summary):
        if _has_f1(summary[c]):
            out.append(c)
        else:
            print(f'warning: condition {c!r} lacks F1 keys; skipped in bar chart', file=sys.stderr)
    return out


def present_conditions(summary) -> list[str]:
    """Conditions found in the summary, in CONDITIONS order (ignores paired/meta keys)."""
    return [c for c in CONDITIONS if isinstance(summary.get(c), dict)]


def ordered_categories(summary, conds=None) -> list[str]:
    """per_trap categories across conditions: decision ('D') first, then tasks, alphabetical."""
    conds = present_conditions(summary) if conds is None else conds
    cats = set()
    for k in conds:
        cats |= set(((summary[k].get('extended') or {}).get('per_trap')) or {})
    return sorted(cats, key=lambda c: (not c.startswith('D'), c))


def _f1_figure(summary, conds):
    series = [
        ('F1 decisiones', C_DEC, None, lambda s: s['primary']['decisions']['f1']),
        ('F1 estricto decisiones', C_DEC, '////', lambda s: s['extended']['strict_f1']['decisions']),
        ('F1 tareas', C_TASK, None, lambda s: s['primary']['tasks']['f1']),
        ('F1 estricto tareas', C_TASK, '////', lambda s: s['extended']['strict_f1']['tasks']),
    ]
    h = 0.19
    gap_ref = 0.35  # extra spacing between reference and agent groups
    ys, y, prev_ref = [], 0.0, None
    for c in conds:
        is_ref = c in REFERENCE
        if prev_ref is True and not is_ref:
            y += gap_ref
        ys.append(y)
        y += 1.0
        prev_ref = is_ref
    fig, ax = plt.subplots(figsize=(COL_W - 0.2, 0.62 * len(conds) + 0.7))
    for i, (name, color, hatch, get) in enumerate(series):
        vals = [get(summary[c]) for c in conds]
        pos = [yy + (i - 1.5) * h for yy in ys]
        ax.barh(pos, vals, height=h * 0.92, color=('white' if hatch else color),
                edgecolor=color, hatch=hatch, linewidth=0.6)
        for p, v in zip(pos, vals):
            ax.text(v + 0.012, p, f'{v:.2f}', va='center', ha='left', fontsize=FS - 0.5, color=INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([LABELS.get(c, c) for c in conds], color=INK)
    ax.set_xlim(0, 1.12)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel('F1')
    ax.xaxis.grid(True, color='#e3e3e3', linewidth=0.5)
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=2)
    ax.set_ylim(ys[-1] + 0.6, -0.6)
    # divider between reference and agent conditions
    refs = [yy for yy, c in zip(ys, conds) if c in REFERENCE]
    agents = [yy for yy, c in zip(ys, conds) if c not in REFERENCE]
    if refs and agents:
        ax.axhline((max(refs) + min(agents)) / 2, color='#555555', linewidth=0.7,
                   linestyle=(0, (4, 3)))
    handles = [Patch(facecolor=('white' if hs else col), edgecolor=col, hatch=hs, linewidth=0.6,
                     label=n) for n, col, hs, _ in series]
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.45, -0.12), ncol=2,
              frameon=False, fontsize=FS, handlelength=1.4, columnspacing=1.0, handletextpad=0.5)
    return fig


def _trap(summary, k, c):
    return (((summary[k].get('extended') or {}).get('per_trap')) or {}).get(c)


def heatmap_matrix(summary, conds=None):
    """(conds, cats, values): found/gold per condition x category; NaN if missing or gold == 0."""
    conds = present_conditions(summary) if conds is None else conds
    cats = ordered_categories(summary, conds)
    nan = float('nan')
    values = []
    for k in conds:
        row = []
        for c in cats:
            t = _trap(summary, k, c) or {}
            g, f = t.get('gold'), t.get('found')
            row.append(f / g if g and f is not None else nan)
        values.append(row)
    return conds, cats, values


def _heatmap_figure(summary, conds):
    conds, cats, mat = heatmap_matrix(summary, conds)
    if not cats or not conds:
        return None
    gold = {c: max((_trap(summary, k, c) or {}).get('gold') or 0 for k in conds) for c in cats}
    fig, ax = plt.subplots(figsize=(COL_W - 0.6, 0.34 * len(conds) + 1.5))
    im = ax.imshow(mat, cmap='Blues', vmin=0, vmax=1, aspect='auto')
    for i, row in enumerate(mat):
        for j, v in enumerate(row):
            if v == v:
                ax.text(j, i, f'{100 * v:.0f}', ha='center', va='center', fontsize=FS,
                        color='white' if v > 0.6 else INK)
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels([f'{c} (n={gold[c]})' for c in cats], rotation=40, ha='left',
                       rotation_mode='anchor', color=INK)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(conds)))
    ax.set_yticklabels([LABELS.get(c, c) for c in conds], color=INK)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([x - 0.5 for x in range(1, len(cats))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(conds))], minor=True)
    ax.grid(which='minor', color='white', linewidth=1.2)
    ax.tick_params(which='minor', length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label('% encontrados', fontsize=FS)
    cb.ax.tick_params(labelsize=FS, length=2)
    cb.set_ticks([0, 0.5, 1])
    cb.set_ticklabels(['0', '50', '100'])
    cb.outline.set_visible(False)
    return fig


def make_figures(summary_path: Path, out_dir: Path) -> list[Path]:
    summary = json.loads(Path(summary_path).read_text(encoding='utf-8'))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    conds = present_conditions(summary)
    bar_conds = bar_conditions(summary)
    _style()
    paths = []
    if bar_conds:
        paths += _save(_f1_figure(summary, bar_conds), out_dir, 'f1_by_condition')
    fig = _heatmap_figure(summary, conds)
    if fig is not None:
        paths += _save(fig, out_dir, 'trap_heatmap')
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--summary', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    a = ap.parse_args(argv)
    for p in make_figures(a.summary, a.out):
        print(p)


if __name__ == '__main__':
    main()
