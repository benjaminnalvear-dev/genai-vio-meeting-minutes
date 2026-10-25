import zipfile
from pathlib import Path

import pytest

from minutes_agents.data import extract_dataset


@pytest.fixture(scope='session')
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope='session')
def dataset_dir(repo_root, tmp_path_factory) -> Path:
    zip_path = repo_root / 'GenAI Constrained+Tool use' / 'Fine Tuning.zip'
    return extract_dataset(zip_path, tmp_path_factory.mktemp('dataset'))


@pytest.fixture(scope='session')
def d2_results_dir(repo_root, tmp_path_factory) -> Path:
    dest = tmp_path_factory.mktemp('d2_results')
    with zipfile.ZipFile(repo_root / 'GenAI Constrained+Tool use' / 'minutas_resultados_test.zip') as z:
        z.extractall(dest)
    return dest
