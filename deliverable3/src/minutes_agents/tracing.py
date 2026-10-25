"""JSONL tracer for inter-agent messages."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class Tracer:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else None
        self.events: list[dict] = []
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, agent: str, step: int, **fields) -> dict:
        event = {'ts': datetime.now(timezone.utc).isoformat(), 'agent': agent, 'step': step, **fields}
        self.events.append(event)
        if self.path is not None:
            with self.path.open('a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        return event
