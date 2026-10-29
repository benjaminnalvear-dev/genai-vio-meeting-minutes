"""Post-hoc diagnosis of the Finalizer's decision/task overlap rule, without calling the model.

Re-runs the real graph (guards, merge, Finalizer) for each agentic condition and meeting, but
every agent invocation returns the output recorded in its trace. With the rule on, the replay
must reproduce the frozen result exactly (checked); then it is repeated with the rule off and
both are scored with the D2 evaluator. The official numbers are not changed.

Usage (from deliverable3/):
python scripts/replay_from_traces.py --data <dir|Fine Tuning.zip> --runs runs/test --out runs/test/posthoc_overlap_rule.json
"""
import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import minutes_agents.finalize as fin  # noqa: E402
import minutes_agents.graph as graph  # noqa: E402
from minutes_agents.agents.base import _empty_output  # noqa: E402
from minutes_agents.data import extract_dataset, load_split  # noqa: E402
from minutes_agents.evaluate import evaluate_arm  # noqa: E402
from minutes_agents.experiment import load_config  # noqa: E402
from minutes_agents.metrics import extended_metrics, paired_comparison  # noqa: E402

AGENTS = ('decisions', 'tasks', 'auditor')
CONDS = ['full', 'no_react', 'no_auditor', 'no_fewshot', 'no_cot', 'no_guards']


def invocations(trace_path: Path) -> list[list[dict]]:
    """Agent events grouped per run_react call: a call ends at the step that logs an output or an error."""
    out, cur = [], []
    for line in Path(trace_path).read_text(encoding='utf-8').splitlines():
        e = json.loads(line) if line.strip() else None
        if not e or e['agent'] not in AGENTS:
            continue
        cur.append(e)
        if e.get('output') is not None or e.get('error'):
            out.append(cur)
            cur = []
    if cur:
        raise ValueError(f'unterminated agent call in {trace_path}')
    return out


def _replay_react(queue):
    def run_react(spec, tr, user_content, llm, tracer, cfg, ctx):
        inv = queue.pop(0)
        last = inv[-1]
        if last['agent'] != spec.name:
            raise ValueError(f"trace order mismatch: expected {spec.name}, got {last['agent']}")
        output = last['output'] if last.get('output') is not None else _empty_output(spec.output(tr, ctx, cfg))
        return {'output': copy.deepcopy(output), 'steps': len(inv), 'calls': len(inv)}
    return run_react


def replay_meeting(trace_path: Path, tr: dict, cond: str, overlap_rule: bool = True) -> dict:
    queue = invocations(trace_path)
    real_react, real_drop = graph.run_react, fin._drop_overlaps
    graph.run_react = _replay_react(queue)
    if not overlap_rule:
        fin._drop_overlaps = lambda decisions, tasks: (decisions, tasks, [])
    try:
        parsed = graph.run_meeting(tr, llm=None, cfg=load_config(cond), trace_path=None)['parsed']
    finally:
        graph.run_react, fin._drop_overlaps = real_react, real_drop
    if queue:
        raise ValueError(f'{len(queue)} recorded agent calls left unused in {trace_path}')
    return parsed


def _score(outputs, transcripts, gold, cond):
    prim = evaluate_arm(outputs, transcripts, gold, False, cond)
    ext = extended_metrics(outputs, transcripts, gold, False)
    return {'decisions': prim['decisions'], 'tasks': prim['tasks'], 'strict_f1': ext['strict_f1'],
            'per_trap': ext['per_trap'], 'per_meeting': ext['per_meeting']}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', type=Path, required=True, help='dir with train/validation/test, or Fine Tuning.zip')
    ap.add_argument('--runs', type=Path, default=Path('runs/test'))
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(argv)
    with tempfile.TemporaryDirectory() as tmp:
        root = extract_dataset(a.data, Path(tmp)) if a.data.suffix.lower() == '.zip' else a.data
        transcripts, gold = load_split(root, 'test')
    report = {}
    for cond in CONDS:
        arms = {}
        for rule in (True, False):
            outputs = {}
            for mid in sorted(transcripts):
                frozen = json.loads((a.runs / 'results' / cond / f'{mid}.json').read_text(encoding='utf-8'))
                parsed = replay_meeting(a.runs / 'traces' / cond / f'{mid}.jsonl', transcripts[mid], cond, rule)
                if rule and parsed != frozen['parsed']:
                    raise SystemExit(f'replay does not reproduce the frozen result: {cond} {mid}')
                outputs[mid] = dict(frozen, parsed=parsed, raw=json.dumps(parsed, ensure_ascii=False))
            arms['with_rule' if rule else 'without_rule'] = _score(outputs, transcripts, gold, cond)
        report[cond] = arms
        w, wo = arms['with_rule'], arms['without_rule']
        print(f"{cond:11s} decisions F1 {w['decisions']['f1']:.3f} -> {wo['decisions']['f1']:.3f} "
              f"(matched/predicted {w['decisions']['matched']}/{w['decisions']['predicted']} -> "
              f"{wo['decisions']['matched']}/{wo['decisions']['predicted']}) | "
              f"tasks F1 {w['tasks']['f1']:.3f} -> {wo['tasks']['f1']:.3f}")
    d2 = json.loads((a.runs / 'results' / 'summary.json').read_text(encoding='utf-8'))['d2']['extended']['per_meeting']
    pm = report['full']['without_rule']['per_meeting']
    report['paired_full_without_rule_vs_d2'] = {k: paired_comparison(pm, d2, k)
                                                for k in ('decisions_f1', 'tasks_f1', 'strict_f1')}
    print('paired full (without rule) vs d2:', report['paired_full_without_rule_vs_d2'])
    a.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
