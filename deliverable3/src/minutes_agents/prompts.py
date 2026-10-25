"""Versioned prompt loader: prompts/<name>.md with sha256 of its content."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[2] / 'prompts'


@dataclass(frozen=True)
class Prompt:
    name: str
    text: str
    path: Path
    sha256: str


def load_prompt(name: str, prompts_dir: Path = PROMPTS_DIR) -> Prompt:
    path = Path(prompts_dir) / f'{name}.md'
    text = path.read_bytes().decode('utf-8').replace('
', '
')
    return Prompt(name=name, text=text, path=path,
                  sha256=hashlib.sha256(text.encode('utf-8')).hexdigest())
