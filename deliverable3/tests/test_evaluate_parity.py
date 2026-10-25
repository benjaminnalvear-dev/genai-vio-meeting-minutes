import json

from minutes_agents.data import load_split
from minutes_agents.evaluate import evaluate_arm

ARMS = {'baseline': 'baseline', 'structured': 'structured', 'combined': 'combined_v2'}
KEYS = ['json_valid', 'schema_valid', 'state_accuracy_matched', 'assignee_accuracy_matched',
        'deadline_accuracy_matched', 'evidence_exact_matched', 'evidence_id_exists', 'seconds_total']


def test_evaluator_reproduces_d2_summary(dataset_dir, d2_results_dir):
    transcripts, gold = load_split(dataset_dir, 'test')
    expected = {row['arm']: row for row in json.loads((d2_results_dir / 'summary.json').read_text('utf-8'))}
    for arm, suffix in ARMS.items():
        outputs = {m: json.loads((d2_results_dir / f'{m}_{suffix}.json').read_text('utf-8')) for m in sorted(transcripts)}
        got = evaluate_arm(outputs, transcripts, gold, is_baseline=(arm == 'baseline'), arm=arm)
        for kind in ('decisions', 'tasks'):
            assert got[kind] == expected[arm][kind]
        for k in KEYS:
            assert got[k] == expected[arm][k]


def test_load_split_counts(dataset_dir):
    assert [len(load_split(dataset_dir, s)[0]) for s in ('train', 'validation', 'test')] == [50, 10, 10]
