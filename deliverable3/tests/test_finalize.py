from minutes_agents.finalize import finalize, merge


def test_merge_keeps_unflagged():
    cur = [{'id': 'd01', 'x': 1}, {'id': 'd02', 'x': 2}]
    out = merge(cur, [{'id': 'd02', 'x': 9}, {'id': 'd03', 'x': 3}, {'id': 'd01', 'x': 7}], {'d02'})
    assert out == [{'id': 'd01', 'x': 1}, {'id': 'd02', 'x': 9}, {'id': 'd03', 'x': 3}]


def test_merge_never_loses_flagged_item_and_appends_new_with_unique_ids():
    cur = [{'id': 'd01', 'x': 1}]
    out = merge(cur, [{'id': 'NEW', 'x': 5}, {'id': 'NEW', 'x': 6}], {'d01', 'NEW'})
    assert out == [{'id': 'd01', 'x': 1}, {'id': 'd02', 'x': 5}, {'id': 'd03', 'x': 6}]


def test_merge_second_round_new_items_no_loss_no_duplication():
    # Ronda 1: el Auditor reporta una omisión ('NEW') y el especialista la agrega.
    r1 = merge([{'id': 'd01', 'x': 1}], [{'id': 'NEW', 'x': 2}], {'NEW'})
    assert r1 == [{'id': 'd01', 'x': 1}, {'id': 'd02', 'x': 2}]
    # Ronda 2: 'NEW' vuelve a aparecer en flagged_ids (otra omisión) y el ítem agregado se corrige.
    r2 = merge(r1, [{'id': 'NEW', 'x': 3}, {'id': 'd02', 'x': 9}], {'NEW', 'd02'})
    assert r2 == [{'id': 'd01', 'x': 1}, {'id': 'd02', 'x': 9}, {'id': 'd03', 'x': 3}]
    # Caso del review: NEW nunca se reemplaza ni se duplica.
    out = merge([{'id': 'd01'}, {'id': 'NEW', 'x': 'x'}], [{'id': 'NEW', 'x': 'y'}], {'NEW'})
    assert out == [{'id': 'd01'}, {'id': 'NEW', 'x': 'x'}, {'id': 'd02', 'x': 'y'}]


def test_merge_split_item_gets_unique_ids_and_prefix():
    cur = [{'id': 't01'}, {'id': 't02'}]
    out = merge(cur, [{'id': 't01', 'x': 'a'}, {'id': 't01', 'x': 'b'}], {'t01'})
    assert [i['id'] for i in out] == ['t01', 't03', 't02']
    assert [i['id'] for i in merge([], [{'id': 'NEW'}], {'NEW'}, prefix='t')] == ['t01']


def test_merge_remaps_supersedes_to_provisional_id_without_mutating_input():
    rev = [{'id': 'q1', 'supersedes': None}, {'id': 'NEW2', 'supersedes': 'q1'}]
    out = merge([{'id': 'd01'}], rev, set())
    assert out[1:] == [{'id': 'd02', 'supersedes': None}, {'id': 'd03', 'supersedes': 'd02'}]
    assert rev[1] == {'id': 'NEW2', 'supersedes': 'q1'}


def test_finalize_remaps_supersedes_and_drops_dangling(m01):
    ds = [{'id': 'a', 'evidence_id': 'u31', 'supersedes': 'b', 'state': 'final'},
          {'id': 'b', 'evidence_id': 'u05', 'supersedes': 'zz', 'state': 'superseded'}]
    out = finalize(m01, ds, [])['decisions']
    assert [d['id'] for d in out] == ['d01', 'd02'] and out[1]['supersedes'] == 'd01' and out[0]['supersedes'] is None


def test_finalize_orders_tasks_and_applies_safe_checks(m01):
    ts = [{'id': 'x', 'evidence_id': 'u20', 'deadline': 'mañana'},
          {'id': 'y', 'evidence_id': 'u99', 'deadline': None},
          {'id': 'z', 'evidence_id': 'u03', 'deadline': '2026-10-04T9:00'},
          {'id': 'w', 'evidence_id': 'u03', 'deadline': '2026-10-04T09:00'}]
    res = finalize(m01, [], ts)
    assert [(t['id'], t['evidence_id']) for t in res['tasks']] == [('t01', 'u03'), ('t02', 'u03'), ('t03', 'u20')]
    assert [t['deadline'] for t in res['tasks']] == [None, '2026-10-04T09:00', None]
    assert 'descartado: evidence_id inexistente' in res['mechanical_actions']
    assert ts[0]['deadline'] == 'mañana' and ts[0]['id'] == 'x'  # inputs not mutated


def test_finalize_nulls_supersedes_to_dropped_item(m01):
    ds = [{'id': 'a', 'evidence_id': 'u10', 'supersedes': 'b', 'state': 'final'},
          {'id': 'b', 'evidence_id': 'u99', 'supersedes': None, 'state': 'superseded'}]
    res = finalize(m01, ds, [])
    assert [d['id'] for d in res['decisions']] == ['d01'] and res['decisions'][0]['supersedes'] is None


def test_merge_flagged_id_absent_from_current_is_appended():
    out = merge([{'id': 'd01'}], [{'id': 'd07', 'x': 1}], {'d07'})
    assert out == [{'id': 'd01'}, {'id': 'd02', 'x': 1}]
