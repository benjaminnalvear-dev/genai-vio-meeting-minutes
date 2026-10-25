"""Generic ReAct runner shared by all agents."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from jsonschema import Draft202012Validator

from minutes_agents.llm import LLM
from minutes_agents.prompts import Prompt
from minutes_agents.schemas import step_schema
from minutes_agents.tools import TOOLS
from minutes_agents.tracing import Tracer

ROOT = Path(__file__).resolve().parents[3]


@dataclass
class RunConfig:
    name: str
    react: bool = True
    auditor_rounds: int = 2
    fewshot: bool = True
    cot: bool = True
    max_steps: int = 3


@dataclass
class AgentSpec:
    name: str
    prompt: Prompt
    fewshot: Prompt | None
    tools: list[str]
    output: Callable[[dict, dict, RunConfig], dict[str, dict]]
    precompute: Callable[[dict, dict], list[dict]]


def transcript_text(tr):
    head = {k: tr.get(k) for k in ('meeting_id','meeting_date','title','participants')}
    lines = [json.dumps(head, ensure_ascii=False), 'INTERVENCIONES EN ORDEN:']
    lines += [f"{u['id']} | {u.get('timestamp','')} | {u['speaker']}: {u['text']}" for u in tr['utterances']]
    return '\n'.join(lines)


def user_message(tr: dict, *, feedback: list[dict] | None = None, items: dict | None = None) -> str:
    """Transcripción en el formato del D2 (copia de `transcript_text`, celda 4);
    en revisión agrega los ítems marcados y el feedback del Auditor."""
    text = transcript_text(tr)
    if items is not None:
        text += '\n\nÍTEMS A REVISAR:\n' + json.dumps(items, ensure_ascii=False)
    if feedback is not None:
        text += '\n\nFEEDBACK DEL AUDITOR:\n' + json.dumps(feedback, ensure_ascii=False)
    return text


def _prompt_file(prompt: Prompt) -> str:
    path = Path(prompt.path)
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _empty_output(output: dict[str, dict]) -> dict:
    empty = {}
    for key, sch in output.items():
        t = sch.get('type')
        is_array = t == 'array' or (isinstance(t, list) and 'array' in t)
        empty[key] = [] if is_array else None
    return empty


def _execute(tr: dict, call: dict, ctx: dict) -> dict | list:
    name = call.get('tool')
    fn = TOOLS.get(name)
    if fn is None:
        return {'tool': name, 'error': 'unknown tool'}
    return fn(tr, call, ctx)


def run_react(spec: AgentSpec, tr: dict, user_content: str, llm: LLM, tracer: Tracer,
              cfg: RunConfig, ctx: dict) -> dict:
    system = spec.prompt.text
    if cfg.fewshot and spec.fewshot is not None:
        system += '\n\n' + spec.fewshot.text
    user = user_content
    if not cfg.react:
        user += '\n\nINFORMES DE HERRAMIENTAS:\n' + json.dumps(spec.precompute(tr, ctx), ensure_ascii=False)
    messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]
    output_props = spec.output(tr, ctx, cfg)
    n_steps = cfg.max_steps if cfg.react else 1
    pfile, psha = _prompt_file(spec.prompt), spec.prompt.sha256
    calls = 0

    for step in range(1, n_steps + 1):
        allow_tools = cfg.react and step < n_steps
        schema = step_schema(tr, spec.tools, output_props, allow_tools=allow_tools, with_thought=cfg.cot)
        result = llm.chat(messages, schema)
        calls += 1
        parsed = result.get('parsed')
        base = dict(prompt_file=pfile, prompt_sha256=psha, seconds=result.get('seconds'),
                    tokens=result.get('eval_count'))
        if parsed is None or not Draft202012Validator(schema).is_valid(parsed):
            tracer.log(spec.name, step, thought=None, action=None, tool_calls=None,
                       observations=None, output=None, error='invalid_json', **base)
            return {'output': _empty_output(output_props), 'steps': step, 'calls': calls}

        action = parsed.get('action')
        tool_calls = parsed.get('tool_calls') or []
        if action == 'call_tools' and allow_tools:
            observations = [_execute(tr, c, ctx) for c in tool_calls]
            tracer.log(spec.name, step, thought=parsed.get('thought'), action=action,
                       tool_calls=tool_calls, observations=observations, output=None, **base)
            messages.append({'role': 'assistant', 'content': result['raw']})
            messages.append({'role': 'user',
                             'content': 'OBSERVACIONES:\n' + json.dumps(observations, ensure_ascii=False)})
            continue

        output = {k: parsed[k] for k in output_props}
        tracer.log(spec.name, step, thought=parsed.get('thought'), action=action,
                   tool_calls=tool_calls, observations=None, output=output, **base)
        return {'output': output, 'steps': step, 'calls': calls}

    return {'output': _empty_output(output_props), 'steps': n_steps, 'calls': calls}
