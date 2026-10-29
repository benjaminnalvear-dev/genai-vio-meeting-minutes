import json
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / 'notebooks' / 'D3_Colab.ipynb'


def test_notebook_structure_and_code_compiles():
    nb = json.loads(NB.read_text(encoding='utf-8'))
    assert nb['nbformat'] == 4 and isinstance(nb['cells'], list) and nb['cells']
    text = ''
    for i, c in enumerate(nb['cells']):
        assert c['cell_type'] in ('markdown', 'code') and 'source' in c
        src = ''.join(c['source'])
        text += src
        if c['cell_type'] == 'code':
            clean = '\n'.join(l for l in src.splitlines() if not l.lstrip().startswith(('!', '%')))
            compile(clean, f'cell{i}', 'exec')
    assert 'run_experiment.py' in text and 'make_figures.py' in text


def test_notebook_persists_streams_and_reports():
    cells = [''.join(c['source']) for c in json.loads(NB.read_text(encoding='utf-8'))['cells']]
    cfg, ollama, run, trace, acta = cells[1], cells[2], cells[5], cells[6], cells[7]
    assert "PERSIST_DIR = '/content/drive/MyDrive/d3_runs'" in cfg and 'drive.mount' in cfg
    assert "TRACES = f'{PERSIST_DIR}/traces/{SPLIT}'" in cfg
    assert all(f in run for f in ("'--out', RESULTS", "'--traces', TRACES", "'--cache', CACHE"))
    assert 'subprocess.Popen(' in run and 'bufsize=1' in run and 'proc.wait() != 0' in run
    assert "meta.get('failed')" in run
    assert "except requests.RequestException:\n        pass\n    time.sleep(1)" in ollama
    assert "flagged={ev.get('flagged')}" in trace and "next={ev.get('next')}" in trace
    assert "ev.get('mechanical_actions')" in trace
    assert "acta['parsed']" in acta


def test_notebook_guards_uploads_and_conditions():
    cells = [''.join(c['source']) for c in json.loads(NB.read_text(encoding='utf-8'))['cells']]
    cfg, code, data, trace = cells[1], cells[3], cells[4], cells[6]
    assert "ALL_CONDITIONS = 'baseline,d2,full,no_react,no_auditor,no_fewshot,no_cot,no_guards'" in cfg
    assert "'deliverable3' not in zname" in code and 'en esta celda va deliverable3_colab.zip' in code
    assert "'Fine' not in dname" in data and 'en esta celda va Fine Tuning.zip' in data
    assert "SOURCE = 'git'" in cfg and "GenAI Constrained+Tool use/Fine Tuning.zip" in data
    assert "if SOURCE == 'git' and REPO_DATA.exists():" in data
    assert "agent == 'guard'" in trace and '[baranda ' in trace and 'auditor_route' in trace


def test_requests_unpinned():
    reqs = (NB.parents[1] / 'requirements.txt').read_text(encoding='utf-8').split()
    assert 'requests' in reqs and not any(r.startswith('requests=') for r in reqs)
