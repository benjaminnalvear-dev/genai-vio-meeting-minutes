from minutes_agents.tools import (TOOLS, check_participant, find_revision_cues,
                                  find_uncovered_commitments, inspect_evidence, resolve_deadline)


def test_resolve_deadline_matches_d2(m01):
    assert resolve_deadline(m01, 'u33')['suggested'] == '2026-09-18T17:00'
    r = resolve_deadline(m01, 'u08')
    assert (r['suggested'], r['reason']) == ('2026-09-14', 'hora ambigua: solo día calculado')


def test_inspect_and_cues(m01):
    assert inspect_evidence(m01, 'u01')['exists'] is True
    assert inspect_evidence(m01, 'zzz')['exists'] is False
    assert all({'id', 'speaker', 'text'} == set(c) for c in find_revision_cues(m01))


def test_check_participant(m01):
    assert check_participant(m01, 'Speaker 02')['is_participant'] is True
    p = check_participant(m01, 'Paula')
    assert (p['is_participant'], p['mentioned_in_text']) == (False, True)
    assert check_participant(m01, 'Reunión posterior')['mentioned_in_text'] is False


def test_uncovered_commitments_m01(m01, m01_gold):
    items = [x for x in m01_gold['decisions'] + m01_gold['tasks'] if x['evidence_id'] != 'u19']
    assert {u['id'] for u in find_uncovered_commitments(m01, items)} == {'u18', 'u19'}


def test_tool_adapters_return_error_not_raise(m01):
    assert 'error' in TOOLS['inspect_evidence'](m01, {'tool': 'inspect_evidence', 'evidence_id': None}, {'items': []})
    assert 'error' in TOOLS['inspect_evidence'](m01, {'tool': 'inspect_evidence', 'evidence_id': 'nope'}, {'items': []})
    assert 'error' in TOOLS['resolve_deadline'](m01, {'tool': 'resolve_deadline'}, {'items': []})
    assert 'error' in TOOLS['check_participant'](m01, {'tool': 'check_participant', 'name': ''}, {'items': []})
    assert 'error' in TOOLS['check_participant'](m01, {'tool': 'check_participant', 'name': None}, {'items': []})
    assert isinstance(TOOLS['find_uncovered_commitments'](m01, {'tool': 'find_uncovered_commitments'}, {'items': []}), list)
