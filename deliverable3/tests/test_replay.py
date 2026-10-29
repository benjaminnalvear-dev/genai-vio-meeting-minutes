import json
import sys
from pathlib import Path

import minutes_agents.finalize as fin
import minutes_agents.graph as graph
from minutes_agents.data import load_split

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'runs' / 'test'
sys.path.insert(0, str(ROOT / 'scripts'))
import replay_from_traces as rp  # noqa: E402


def test_replay_reproduces_frozen_results_and_restores_patches(dataset_dir):
    transcripts, _ = load_split(dataset_dir, 'test')
    real_react, real_drop = graph.run_react, fin._drop_overlaps
    for cond, mid in [('full', 'M09'), ('no_react', 'M01')]:
        frozen = json.loads((RUNS / 'results' / cond / f'{mid}.json').read_text(encoding='utf-8'))
        trace = RUNS / 'traces' / cond / f'{mid}.jsonl'
        assert rp.replay_meeting(trace, transcripts[mid], cond) == frozen['parsed']
    without = rp.replay_meeting(RUNS / 'traces' / 'full' / 'M09.jsonl', transcripts['M09'], 'full', overlap_rule=False)
    assert 'u17' in {d['evidence_id'] for d in without['decisions']}  # the decision the rule drops in M09
    assert graph.run_react is real_react and fin._drop_overlaps is real_drop
