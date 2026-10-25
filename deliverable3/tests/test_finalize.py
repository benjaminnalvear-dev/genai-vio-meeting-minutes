from minutes_agents.finalize import finalize, merge


def test_merge_keeps_unflagged():
    cur = [{'id': 'd01', 'x': 1}, {'id': 'd02', 'x': 2}]
    out = merge(cur, [{'id': 'd02', 'x': 9}, {'id': 'd03', 'x': 3}, {'id': 'd01', 'x': 7}], {'d02'})
    assert out == [{'id': 'd01', 'x': 1}, {'id': 'd02', 'x': 9}, {'id': 'd03', 'x': 3}]


def test_merge_never_loses_flagged_item_and_appends_new():
    cur = [{'id': 'd01', 'x': 1}]
    out = merge(cur, [{'id': 'NEW', 'x': 5}, {'id': 'NEW', 'x': 6}], {'d01'})
    assert out == [{'id': 'd01', 'x': 1}, {'id': 'NEW', 'x': 5}, {'id': 'NEW', 'x': 6}]


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
