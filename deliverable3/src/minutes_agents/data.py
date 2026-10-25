"""Carga del dataset (port de la celda 2 del D2)."""
import json
import zipfile
from pathlib import Path


def extract_dataset(zip_path: Path, dest: Path) -> Path:
    """Descomprime train/validation/test de Fine Tuning.zip en dest/<split>/*.json."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.endswith('.json'):
                continue
            p = Path(info.filename)
            split = next((s for s in ('train', 'validation', 'test') if s in p.parts), None)
            if split is None:
                continue
            target = dest / split / p.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(info))
    return dest


def load_split(root: Path, split: str) -> tuple[dict[str, dict], dict[str, dict]]:
    """Devuelve (transcripts, gold) indexados por meeting_id, con las validaciones del D2."""
    transcripts, gold = {}, {}
    for path in sorted((Path(root) / split).glob('*.json')):
        item = json.loads(path.read_text(encoding='utf-8'))
        bucket = transcripts if 'utterances' in item else gold
        mid = item['meeting_id']
        if mid in bucket:
            raise ValueError(f'ID duplicado en {split}: {mid}')
        bucket[mid] = item
    if set(transcripts) != set(gold):
        raise ValueError(f'Pares incompletos en {split}: {set(transcripts) ^ set(gold)}')
    for mid, tr in transcripts.items():
        ids = {u['id'] for u in tr['utterances']}
        for item in gold[mid]['decisions'] + gold[mid]['tasks']:
            if item['evidence_id'] not in ids:
                raise ValueError(f'Evidencia inválida en rúbrica {mid}: {item}')
    return transcripts, gold
