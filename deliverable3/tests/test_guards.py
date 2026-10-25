"""Barandas determinísticas del Auditor (guards.py) sobre la reunión de test M01."""
import pytest

from minutes_agents.guards import dedupe_new, filter_verdicts, route_from
from minutes_agents.tools import find_revision_cues


def dec(i, ev, state='final', supersedes=None):
    return {'id': i, 'topic': 'x', 'statement': 'x', 'state': state, 'condition': None,
            'supersedes': supersedes, 'evidence_id': ev}


def task(i, ev, assignee=None, deadline=None, state='final'):
    return {'id': i, 'description': 'x', 'assignee': assignee, 'deadline': deadline,
            'condition': None, 'state': state, 'evidence_id': ev}


def bad(item_id, problem, detail='revisar'):
    return {'item_id': item_id, 'ok': False, 'problem': problem, 'detail': detail}


def run(m01, decisions, tasks, verdicts):
    return filter_verdicts(m01, decisions, tasks, verdicts)


# Ítems que ya citan los turnos de compromiso salvo u18/u19 (demostración técnica).
COVERED_TASKS = [task('t01', 'u08', 'Speaker 02'), task('t02', 'u37', 'Speaker 03'),
                 task('t03', 'u39', 'Speaker 01')]


def test_ok_verdicts_are_ignored(m01):
    acc, drop = run(m01, [dec('d01', 'u05')], [], [{'item_id': 'd01', 'ok': True, 'problem': None,
                                                     'detail': ''}])
    assert acc == [] and drop == []


def test_g1_new_citing_covered_turn_dropped(m01):
    acc, drop = run(m01, [dec('d01', 'u05')], COVERED_TASKS,
                    [bad('NEW', 'missing_item', 'falta la tarea de u08')])
    assert acc == [] and drop[0]['guard'] == 'G1'


def test_g1_new_citing_uncovered_commitment_accepted_as_task(m01):
    acc, drop = run(m01, [dec('d01', 'u05')], COVERED_TASKS,
                    [bad('NEW', 'missing_item', 'u19: Speaker 04 queda a cargo de la demo')])
    assert drop == [] and acc[0]['kind_hint'] == 'tasks'


def test_g1_new_citing_uncited_revision_cue_goes_to_decisions(m01):
    assert 'u25' in {c['id'] for c in find_revision_cues(m01)}
    acc, drop = run(m01, [dec('d01', 'u05')], COVERED_TASKS,
                    [bad('NEW', 'missing_item', 'u25 reemplaza la propuesta de formato')])
    assert drop == [] and acc[0]['kind_hint'] == 'decisions'


def test_g1_missing_item_on_existing_item_dropped(m01):
    acc, drop = run(m01, [dec('d01', 'u05')], [], [bad('d01', 'missing_item', 'u19')])
    assert acc == [] and drop[0]['guard'] == 'G1'


def test_g1_new_without_turn_id_dropped(m01):
    acc, drop = run(m01, [], [], [bad('NEW', 'missing_item', 'falta una tarea')])
    assert acc == [] and drop[0]['guard'] == 'G1'


def test_g2_deadline_matching_tool_day_dropped(m01):
    acc, drop = run(m01, [], [task('t01', 'u33', 'Speaker 04', '2026-09-18T17:00')],
                    [bad('t01', 'wrong_deadline')])
    assert acc == [] and drop[0]['guard'] == 'G2'


def test_g2_deadline_not_matching_accepted(m01):
    acc, drop = run(m01, [], [task('t01', 'u33', 'Speaker 04', '2026-09-20')],
                    [bad('t01', 'wrong_deadline')])
    assert drop == [] and len(acc) == 1


def test_g3_supported_superseded_dropped(m01):
    assert 'u31' in {c['id'] for c in find_revision_cues(m01)}
    ds = [dec('d01', 'u05', 'superseded'), dec('d02', 'u31', 'final', supersedes='d01')]
    acc, drop = run(m01, ds, [], [bad('d01', 'wrong_state', 'u05 no fue reemplazada')])
    assert acc == [] and drop[0]['guard'] == 'G3'


def test_g3_superseded_without_successor_accepted(m01):
    acc, drop = run(m01, [dec('d01', 'u05', 'superseded')], [], [bad('d01', 'wrong_state')])
    assert drop == [] and len(acc) == 1


def test_g3_pending_on_pendiente_turn_dropped(m01):
    acc, drop = run(m01, [dec('d01', 'u28', 'pending')], [], [bad('d01', 'wrong_state')])
    assert acc == [] and drop[0]['guard'] == 'G3'


def test_g3_rejected_without_descarte_accepted(m01):
    acc, drop = run(m01, [dec('d01', 'u36', 'rejected')], [], [bad('d01', 'wrong_state')])
    assert drop == [] and len(acc) == 1


def test_g3_final_never_dropped(m01):
    acc, drop = run(m01, [dec('d01', 'u31', 'final')], [], [bad('d01', 'wrong_state')])
    assert drop == [] and len(acc) == 1


def test_g4_task_wrong_state_always_dropped(m01):
    acc, drop = run(m01, [], [task('t01', 'u08', 'Speaker 02')], [bad('t01', 'wrong_state')])
    assert acc == [] and drop[0]['guard'] == 'G4'


def test_g5_assignee_named_in_turn_dropped(m01):
    acc, drop = run(m01, [], [task('t01', 'u19', 'Speaker 04')], [bad('t01', 'wrong_assignee')])
    assert acc == [] and drop[0]['guard'] == 'G5'


def test_g5_assignee_is_speaker_dropped(m01):
    acc, drop = run(m01, [], [task('t01', 'u08', 'Speaker 02')], [bad('t01', 'wrong_assignee')])
    assert acc == [] and drop[0]['guard'] == 'G5'


def test_g5_absent_third_party_accepted(m01):
    acc, drop = run(m01, [], [task('t01', 'u19', 'Paula')], [bad('t01', 'wrong_assignee')])
    assert drop == [] and len(acc) == 1


def test_g6_merged_on_chained_decision_dropped(m01):
    ds = [dec('d01', 'u05', 'superseded'), dec('d02', 'u31', 'final', supersedes='d01')]
    acc, drop = run(m01, ds, [], [bad('d01', 'merged_items'), bad('d02', 'merged_items')])
    assert acc == [] and [d['guard'] for d in drop] == ['G6', 'G6']


def test_g6_merged_on_standalone_decision_accepted(m01):
    acc, drop = run(m01, [dec('d01', 'u36')], [], [bad('d01', 'merged_items')])
    assert drop == [] and len(acc) == 1


def test_g0_unknown_item_dropped(m01):
    acc, drop = run(m01, [dec('d01', 'u36')], [], [bad('d09', 'evidence_not_supporting')])
    assert acc == [] and drop[0]['guard'] == 'G0' and drop[0]['reason'] == 'unknown item'


def test_evidence_not_supporting_accepted_unchanged(m01):
    v = bad('d01', 'evidence_not_supporting')
    acc, drop = run(m01, [dec('d01', 'u36')], [], [v])
    assert acc == [v] and drop == []


def test_dropped_entry_shape(m01):
    v = bad('t01', 'wrong_state')
    _, drop = run(m01, [], [task('t01', 'u08')], [v])
    assert set(drop[0]) == {'verdict', 'guard', 'reason'} and drop[0]['verdict'] == v
    assert isinstance(drop[0]['reason'], str) and drop[0]['reason']


@pytest.mark.parametrize('accepted,route', [
    ([], 'finish'),
    ([{'item_id': 'd01'}], 'decisions'),
    ([{'item_id': 't02'}], 'tasks'),
    ([{'item_id': 'd01'}, {'item_id': 't01'}], 'both'),
    ([{'item_id': 'NEW', 'kind_hint': 'tasks'}], 'tasks'),
    ([{'item_id': 'd01'}, {'item_id': 'NEW', 'kind_hint': 'tasks'}], 'both'),
    ([{'item_id': 'NEW'}], 'finish'),
])
def test_route_from(accepted, route):
    assert route_from(accepted) == route


def test_dedupe_new_drops_appended_item_with_existing_evidence():
    current = [task('t01', 'u08'), task('t02', 'u10')]
    merged = current + [task('t03', 'u08'), task('t04', 'u33')]
    kept, dropped = dedupe_new(current, merged)
    assert [t['id'] for t in kept] == ['t01', 't02', 't04']
    assert [t['id'] for t in dropped] == ['t03']


def test_g1_new_with_other_problem_dropped(m01):
    v = bad('NEW', 'wrong_state', 'u19 debería ser final')
    acc, drop = run(m01, [dec('d01', 'u05')], COVERED_TASKS, [v])
    assert acc == [] and drop == [{'verdict': v, 'guard': 'G1',
                                   'reason': 'NEW solo es válido con missing_item'}]


def test_g5_matches_whole_token_only():
    tr = {'meeting_id': 'X', 'meeting_date': '2026-09-14', 'title': 't', 'participants': [],
          'utterances': [{'id': 'u01', 'speaker': 'Speaker 1', 'text': 'Hola.'},
                         {'id': 'u02', 'speaker': 'Speaker 2', 'text': 'Speaker 10 queda a cargo del informe.'},
                         {'id': 'u03', 'speaker': 'Speaker 10', 'text': 'De acuerdo.'}]}
    acc, drop = filter_verdicts(tr, [], [task('t01', 'u02', 'Speaker 1')], [bad('t01', 'wrong_assignee')])
    assert drop == [] and len(acc) == 1  # 'speaker 1' no coincide con 'speaker 10'
    acc, drop = filter_verdicts(tr, [], [task('t01', 'u02', 'Speaker 10')], [bad('t01', 'wrong_assignee')])
    assert acc == [] and drop[0]['guard'] == 'G5'


def test_dedupe_new_exempts_split_of_merged_item():
    current = [task('t01', 'u08'), task('t02', 'u33')]
    merged = [task('t01', 'u08'), task('t02', 'u33'), task('t03', 'u08'), task('t04', 'u33')]
    kept, dropped = dedupe_new(current, merged, exempt_evidence={'u08'})
    assert [t['id'] for t in kept] == ['t01', 't02', 't03']
    assert [t['id'] for t in dropped] == ['t04']
