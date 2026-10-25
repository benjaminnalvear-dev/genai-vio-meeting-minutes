import importlib.util
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'package_for_colab.py'


def _load():
    spec = importlib.util.spec_from_file_location('package_for_colab', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_zip_contents(tmp_path):
    out = tmp_path / 'x.zip'
    _load().main(['--out', str(out)])
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert 'deliverable3/src/minutes_agents/graph.py' in names
        assert 'deliverable3/prompts/decisions.v1.md' in names
        assert 'deliverable3/COMMIT.txt' in names
        assert z.read('deliverable3/COMMIT.txt').decode().strip()
    assert not any('.venv/' in n or '__pycache__' in n or '.cache/' in n or 'dist/' in n for n in names)
