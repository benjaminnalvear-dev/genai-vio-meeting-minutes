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
