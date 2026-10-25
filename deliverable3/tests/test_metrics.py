import json

from minutes_agents.data import load_split
from minutes_agents.metrics import difficulty_table, extended_metrics, paired_comparison


def test_difficulty_totals(dataset_dir):
    rows = difficulty_table(*load_split(dataset_dir, 'test'))
    tot = lambda k: sum(r[k] for r in rows)
    assert (tot('turnos'), tot('decisiones'), tot('tareas')) == (347, 56, 53)
    assert (tot('superseded'), tot('rejected'), tot('pending'), tot('final')) == (11, 11, 8, 26)
    assert (tot('plazo_relativo'), tot('terceros_ausentes'), tot('menciones_ausentes')) == (29, 11, 24)


def test_extended_metrics_d2_combined(dataset_dir, d2_results_dir):
    tr, gold = load_split(dataset_dir, 'test')
    outs = {m: json.loads((d2_results_dir / f'{m}_combined_v2.json').read_text('utf-8')) for m in sorted(tr)}
    em = extended_metrics(outs, tr, gold, is_baseline=False)
    found = lambda c: em['per_trap'][c]['found']
    assert found('D: final simple') + found('D: final tras reemplazo') == 25
    assert found('D: superseded') + found('D: rejected') + found('D: pending') == 10
    assert em['deadline_errors']['ok'] == 12 and sum(em['deadline_errors'].values()) == 39
    assert em['task_states_predicted']['pending'] == 47
    assert em['non_participant_assignees'] == 2


def test_paired_comparison():
    a = {'M01': {'f': .5}, 'M02': {'f': .7}, 'M03': {'f': .2}}
    b = {'M01': {'f': .4}, 'M02': {'f': .7}, 'M03': {'f': .3}}
    assert paired_comparison(a, b, 'f') == {'wins': 1, 'ties': 1, 'losses': 1}
