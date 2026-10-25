import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location('make_figures', ROOT / 'scripts' / 'make_figures.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cond(f1d, f1t):
    return {
        'primary': {'decisions': {'f1': f1d}, 'tasks': {'f1': f1t}},
        'extended': {
            'strict_f1': {'decisions': f1d - 0.1, 'tasks': f1t - 0.1},
            'per_trap': {
                'D: explícita': {'gold': 10, 'found': 8, 'state_ok': 7, 'deadline_ok': 0, 'assignee_ok': 0},
                'D: con condición': {'gold': 4, 'found': 1, 'state_ok': 1, 'deadline_ok': 0, 'assignee_ok': 0},
                'T: relativa': {'gold': 6, 'found': 3, 'state_ok': 3, 'deadline_ok': 2, 'assignee_ok': 3},
            },
        },
    }


def _write(tmp_path, conds):
    s = {c: _cond(0.6 + 0.1 * i, 0.5 + 0.1 * i) for i, c in enumerate(conds)}
    s['paired_full_vs_d2'] = {}
    s['meta'] = {'conditions': conds}
    p = tmp_path / 'summary.json'
    p.write_text(json.dumps(s), encoding='utf-8')
    return p


def test_make_figures_creates_files(tmp_path):
    out = _load().make_figures(_write(tmp_path, ['d2', 'full']), tmp_path / 'figs')
    names = {p.name for p in out}
    assert names == {'f1_by_condition.pdf', 'f1_by_condition.png',
                     'trap_heatmap.pdf', 'trap_heatmap.png'}
    assert all(p.exists() and p.stat().st_size > 0 for p in out)


def test_missing_conditions_skipped(tmp_path):
    out = _load().make_figures(_write(tmp_path, ['full', 'no_cot']), tmp_path / 'figs')
    assert len(out) == 4


def test_present_conditions_order_and_ignores_meta():
    mf = _load()
    s = {'meta': {}, 'paired_full_vs_d2': {}, 'no_cot': {}, 'd2': {}, 'full': {}}
    assert mf.present_conditions(s) == ['d2', 'full', 'no_cot']


def test_ordered_categories_decisions_first():
    mf = _load()
    s = {'d2': {'extended': {'per_trap': {'T: a': {}, 'D: z': {}, 'D: b': {}}}},
         'full': {'extended': {'per_trap': {'T: 0': {}}}}}
    assert mf.ordered_categories(s) == ['D: b', 'D: z', 'T: 0', 'T: a']


def test_heatmap_nan_paths(tmp_path):
    p = _write(tmp_path, ['d2', 'full'])
    s = json.loads(p.read_text(encoding='utf-8'))
    del s['full']['extended']['per_trap']['T: relativa']          # missing in one condition
    s['d2']['extended']['per_trap']['T: vacía'] = {'gold': 0, 'found': 0}  # zero gold
    s['full']['extended']['per_trap']['D: explícita'] = {'gold': 10}       # no 'found'
    p.write_text(json.dumps(s), encoding='utf-8')
    mf = _load()
    conds, cats, vals = mf.heatmap_matrix(s)
    assert conds == ['d2', 'full']
    assert cats == ['D: con condición', 'D: explícita', 'T: relativa', 'T: vacía']
    d2, full = vals
    assert d2[0] == 0.25 and d2[1] == 0.8 and d2[2] == 0.5
    assert math.isnan(d2[3])                                   # gold == 0
    assert full[0] == 0.25
    assert math.isnan(full[1])                                 # missing 'found'
    assert math.isnan(full[2]) and math.isnan(full[3])         # category absent
    assert len(mf.make_figures(p, tmp_path / 'figs')) == 4


def test_incomplete_condition_skipped_in_bars(tmp_path, capsys):
    p = _write(tmp_path, ['d2', 'full', 'no_cot'])
    s = json.loads(p.read_text(encoding='utf-8'))
    del s['full']['primary']
    s['no_cot']['primary']['tasks']['f1'] = None
    mf = _load()
    assert mf.bar_conditions(s) == ['d2']
    err = capsys.readouterr().err
    assert "'full'" in err and "'no_cot'" in err and 'warning' in err
    p.write_text(json.dumps(s), encoding='utf-8')
    out = mf.make_figures(p, tmp_path / 'figs')
    assert {x.name for x in out} == {'f1_by_condition.pdf', 'f1_by_condition.png',
                                     'trap_heatmap.pdf', 'trap_heatmap.png'}


def test_no_conditions_no_error(tmp_path):
    p = tmp_path / 'summary.json'
    p.write_text(json.dumps({'meta': {}}), encoding='utf-8')
    assert _load().make_figures(p, tmp_path / 'figs') == []


def test_cli_main_writes_files(tmp_path):
    p = _write(tmp_path, ['d2', 'full'])
    _load().main(['--summary', str(p), '--out', str(tmp_path / 'cli')])
    assert (tmp_path / 'cli' / 'f1_by_condition.pdf').stat().st_size > 0
    assert (tmp_path / 'cli' / 'trap_heatmap.png').stat().st_size > 0


def test_every_condition_has_a_label():
    from minutes_agents.experiment import CONDITIONS
    mf = _load()
    assert set(CONDITIONS) <= set(mf.LABELS) and mf.LABELS['no_guards'] == '− Barandas'
