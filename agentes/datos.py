"""Carga de reuniones desde `Fine Tuning.zip` (mismas validaciones que el notebook de D2)."""
import io
import json
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ZIP_DEFECTO = RAIZ / 'GenAI Constrained+Tool use' / 'Fine Tuning.zip'


def load_split(split, zip_path=ZIP_DEFECTO):
    transcripts, gold = {}, {}
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            p = Path(info.filename)
            if info.is_dir() or p.suffix != '.json' or split not in p.parts:
                continue
            item = json.loads(z.read(info).decode('utf-8'))
            bucket = transcripts if 'utterances' in item else gold
            mid = item['meeting_id']
            if mid in bucket: raise ValueError(f'ID duplicado en {split}: {mid}')
            bucket[mid] = item
    if set(transcripts) != set(gold):
        raise ValueError(f'Pares incompletos en {split}: {set(transcripts)^set(gold)}')
    for mid, tr in transcripts.items():
        ids = {u['id'] for u in tr['utterances']}
        for item in gold[mid]['decisions'] + gold[mid]['tasks']:
            if item['evidence_id'] not in ids:
                raise ValueError(f'Evidencia inválida en rúbrica {mid}: {item}')
    return transcripts, gold


# ---- Copiado de D2 (sin cambios) ----
def transcript_text(tr):
    head = {k: tr.get(k) for k in ('meeting_id','meeting_date','title','participants')}
    lines = [json.dumps(head, ensure_ascii=False), 'INTERVENCIONES EN ORDEN:']
    lines += [f"{u['id']} | {u.get('timestamp','')} | {u['speaker']}: {u['text']}" for u in tr['utterances']]
    return '\n'.join(lines)
