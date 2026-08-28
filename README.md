# Reliable Meeting Minutes from Noisy Transcripts

Semester project for **Generative Artificial Intelligence (580694), Spring 2026**, Universidad de Concepción.

> **Español:** Este proyecto crea actas confiables y verificables desde transcripciones desordenadas de reuniones. La documentación principal se presenta en inglés para la entrega, pero el resumen ejecutivo también está disponible completamente en español.

## Objective

Build a system that converts a Spanish meeting transcript into clear, structured, and evidence-grounded minutes. It must identify:

- final decisions and decisions revised during the conversation;
- agreed tasks, assignees, deadlines, conditions, and status;
- rejected, superseded, and unresolved proposals;
- pending issues and review alerts;
- an exact supporting excerpt and utterance ID for every decision or task.

The first controlled input is a text transcript. A future extension may accept MP3 audio, transcribe it with a separate speech-to-text component, and pass the transcript to the same analysis pipeline.

## Team

- Benjamin Alvear
- Eduardo Ruiz
- Xavier Godoy
- Damian Vera

## Why direct prompting is insufficient

Meetings contain interruptions, topic switching, implicit agreements, mentioned non-participants, changing decisions, relative dates, and conditional tasks. A small model can produce a fluent summary while still confusing proposals with final decisions, assigning the wrong person, dropping conditions, or inventing unsupported facts.

The proposed system separates preprocessing, extraction, temporal state resolution, evidence verification, and deterministic rendering. The planned open-weight candidates are Ministral 3 3B, Qwen 3.5 4B, and Phi-4 Mini.

## Reproducible direct-prompt experiments

The repository includes a synthetic, unscripted-style Spanish meeting with 69 utterances, four declared participants, and three people who are only mentioned. The reference annotation was created separately and was not included in the model context.

| Model / configuration | Main result | Local performance |
|---|---|---|
| Ministral 3 3B, default 4K | Input truncated; Markdown instead of JSON | Exploratory run |
| Ministral 3 3B, controlled 8K | Valid JSON, but incomplete and semantically inconsistent | 2,386 tokens in 22 min 6 s; 1.86 tok/s |
| Qwen 3.5 4B Q4_K_M, controlled 8K | Recovered temporal history, but exhausted 3,000 tokens and left invalid JSON | 3,000 tokens in 16 min 8 s; 3.24 tok/s |

The 8K run recovered the final launch date, SMTP/MailFast decision, and several tasks. However, it recovered 0 of 2 superseded states, omitted the WhatsApp rejection, merged responsibilities, assigned support to an absent person despite explicit contrary evidence, and interpreted 13:00 as 01:00.

Qwen represented both obsolete launch dates and recovered the WhatsApp rejection, but it was overly verbose and stopped inside its eighth action item. It also produced invalid decision states, invented or contradicted tasks, misresolved at least four calendar dates, and used non-entailing evidence. The model loaded locally at 75% CPU / 25% GPU with about 1.74 GB of observed VRAM use, demonstrating execution feasibility but not task completion.

## Standardized baseline prompt

The exact Spanish prompt used in the controlled Ministral and Qwen runs is preserved in [`pruebas/01_prompt_directo_ministral.md`](./pruebas/01_prompt_directo_ministral.md). Despite its historical filename, it is model-independent and is the canonical direct-prompt baseline for future comparisons.

The prompt requires every model to:

- return only valid JSON using the fixed `meeting`, `decisions`, `action_items`, `pending_issues`, and `review_alerts` structure;
- distinguish final, superseded, and rejected decisions without treating proposals as agreements;
- extract each task's assignee, deadline, conditions, and status, using `null` when information was not agreed;
- resolve relative dates from the meeting date;
- attach exact transcript quotes and utterance IDs that actually support each reported item;
- avoid inventing people, dates, tools, responsibilities, or agreements.

For a standardized model comparison, use this prompt and the same transcript without modifications, keep the reference annotation hidden, and record the model version, context size, output limit, temperature, seed, JSON mode, raw response, and runtime metrics. Any future prompt revision should be saved as a new version rather than overwriting this baseline.

## Standardized simulation transcript

The exact simulated meeting used in both controlled runs is preserved in [`pruebas/01_transcripcion_reunion_simulada.md`](./pruebas/01_transcripcion_reunion_simulada.md). It is the canonical input fixture for future baseline comparisons.

The simulation contains 69 timestamped utterances from four participants and separately identifies three people who are mentioned but are not present. It deliberately tests:

- interruptions and topic switching;
- launch dates that change from a proposal to rejected and superseded states before the final agreement;
- rejected tools and communication channels;
- conditional tasks, dependencies, missing owners, and revised deadlines;
- relative expressions such as “tomorrow” and “Monday” that must be resolved from the meeting date;
- the distinction between attendees, absent people, proposals, decisions, and pending issues.

Use the transcript byte-for-byte with the canonical prompt when comparing models. Do not include [`pruebas/01_gold_referencia.md`](./pruebas/01_gold_referencia.md) in the model context: it is reserved exclusively for evaluation. New simulations or corrections must be saved as separately versioned fixtures so previous results remain reproducible.

## Repository structure

```text
.
|-- Deliverable_1_BA_XG_ER_DV.md              # English LaTeX source
|-- Deliverable_1_BA_XG_ER_DV_ESPAÑOL.md      # Mirrored Spanish LaTeX source
|-- pruebas/
|   |-- 01_transcripcion_reunion_simulada.md  # Model-visible transcript
|   |-- 01_prompt_directo_ministral.md         # Direct-prompt baseline
|   |-- 01_gold_referencia.md                  # Withheld reference annotation
|   |-- 01_salida_ministral_8k.md              # Raw controlled output
|   |-- 01_auditoria_ministral.md              # Evidence-backed audit
|   |-- 02_salida_qwen_8k.json                 # Raw Qwen response and Ollama metrics
|   `-- 02_auditoria_qwen.md                   # Evidence-backed Qwen audit
`-- scripts/
    `-- run_ministral_test.ps1                 # Reproduction script
```

## Reproduce the controlled run

Requirements:

- Windows PowerShell 5.1 or PowerShell 7;
- [Ollama](https://ollama.com/) running locally;
- the selected model installed, for example `ollama pull ministral-3:3b` or `ollama pull qwen3.5:4b`.

From the repository root:

```powershell
.\scripts\run_ministral_test.ps1

# Equivalent Qwen run
.\scripts\run_ministral_test.ps1 -Model qwen3.5:4b
```

If the local execution policy blocks scripts, invoke the same command with `powershell -NoProfile -ExecutionPolicy Bypass -File`. The script reads and transports UTF-8 explicitly, uses an 8192-token context, temperature 0, seed 42, native JSON mode, and a 3000-token output limit. It creates a model-specific timestamped JSON result without overwriting an audited run.

## Current status

- [x] Task and correctness criteria defined
- [x] English and Spanish Deliverable 1 sources synchronized
- [x] Local Ministral model and hardware path validated
- [x] Reproducible 4K/8K direct-prompt experiment audited
- [x] Controlled Qwen 3.5 4B run and evidence audit
- [ ] Run the same controlled test with Phi-4 Mini
- [ ] Implement temporal resolver and evidence verifier stages
- [ ] Build and annotate a larger evaluation set

## Deliverable sources

- [English executive-summary source](./Deliverable_1_BA_XG_ER_DV.md)
- [Spanish executive-summary source](./Deliverable_1_BA_XG_ER_DV_ESPAÑOL.md)

Both files contain LaTeX ready to paste into Overleaf. Any future content or layout change must be applied to both language versions.
