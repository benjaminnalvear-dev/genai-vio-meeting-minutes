"""Condiciones de referencia del D2 (baseline y combined_v2) con prompts en archivos.

Reproduce `run_one` del notebook D2 (celda 6): mismos mensajes, mismo flujo.
"""
from __future__ import annotations

import json

from minutes_agents.agents.base import transcript_text
from minutes_agents.finalize import apply_safe_checks
from minutes_agents.llm import LLM
from minutes_agents.prompts import load_prompt
from minutes_agents.schemas import make_schema
from minutes_agents.tools import find_revision_cues, inspect_evidence, resolve_deadline


def tool_bundle(tr, parsed):
    reports=[]
    for kind in ('decisions','tasks'):
        for item in parsed.get(kind,[]) if isinstance(parsed.get(kind),list) else []:
            if not isinstance(item,dict): continue
            report={'kind':kind,'id':item.get('id'),
                    'evidence':inspect_evidence(tr,item.get('evidence_id'))}
            if kind=='tasks':
                report['assignee_named_in_meeting'] = (item.get('assignee') is None or
                    any(str(item.get('assignee')).lower() in u['text'].lower() or
                        item.get('assignee') == u['speaker'] for u in tr['utterances']))
                if item.get('deadline') is not None:
                    report['deadline_check']=resolve_deadline(tr,item.get('evidence_id'),item.get('deadline'))
            reports.append(report)
    return reports


def _messages(tr: dict) -> list[dict]:
    return [{'role': 'system', 'content': load_prompt('d2_system.v1').text},
            {'role': 'user', 'content': transcript_text(tr)}]


def run_baseline(tr: dict, llm: LLM) -> dict:
    """Condición 1: D2 `baseline` (sin esquema), 1 llamada."""
    out = llm.chat(_messages(tr), None)
    out['calls'] = 1
    return out


def run_d2_structured(tr: dict, llm: LLM) -> dict:
    """Borrador estructurado del D2 (`structured`), 1 llamada con esquema."""
    out = llm.chat(_messages(tr), make_schema(tr))
    out['calls'] = 1
    return out


def run_d2_combined(tr: dict, llm: LLM) -> dict:
    """Condición 2: D2 `combined_v2` = borrador estructurado + herramientas + revisión (2 llamadas).

    `seconds` conserva el comportamiento del D2 (solo la llamada de revisión);
    `seconds_total` suma ambas llamadas.
    """
    msgs = _messages(tr)
    schema = make_schema(tr)
    structured = llm.chat(msgs, schema)
    draft = structured['parsed'] if isinstance(structured['parsed'], dict) else {'decisions': [], 'tasks': []}
    reports = tool_bundle(tr, draft)
    review = 'BORRADOR (puede contener errores):\n' + json.dumps(draft, ensure_ascii=False)
    review += '\nSALIDAS DE HERRAMIENTAS (no incluyen rúbrica):\n' + json.dumps(reports, ensure_ascii=False)
    review += '\nINDICIOS DE CAMBIOS LOCALIZADOS POR HERRAMIENTA:\n' + json.dumps(find_revision_cues(tr), ensure_ascii=False)
    review += '\n' + load_prompt('d2_review.v1').text
    out = llm.chat(msgs + [{'role': 'assistant', 'content': json.dumps(draft, ensure_ascii=False)},
                           {'role': 'user', 'content': review}], schema)
    out['tool_reports'] = reports
    out = apply_safe_checks(tr, out)
    out['calls'] = 2
    out['seconds_total'] = round(structured.get('seconds', 0) + out.get('seconds', 0), 2)
    return out
