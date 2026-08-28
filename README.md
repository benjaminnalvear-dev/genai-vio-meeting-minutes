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

## Reproducible Ministral experiment

The repository includes a synthetic, unscripted-style Spanish meeting with 69 utterances, four declared participants, and three people who are only mentioned. The reference annotation was created separately and was not included in the model context.

| Configuration | Main result |
|---|---|
| Ollama default, 4K context | Input truncated; Markdown returned instead of JSON |
| Controlled 8K, temperature 0, seed 42, JSON mode | Valid JSON, but incomplete and semantically inconsistent |
| Performance on local hardware | 2,386 generated tokens in 22 min 6 s; 1.86 tokens/s |

The 8K run recovered the final launch date, SMTP/MailFast decision, and several tasks. However, it recovered 0 of 2 superseded states, omitted the WhatsApp rejection, merged responsibilities, assigned support to an absent person despite explicit contrary evidence, and interpreted 13:00 as 01:00.

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
|   `-- 01_auditoria_ministral.md              # Evidence-backed audit
`-- scripts/
    `-- run_ministral_test.ps1                 # Reproduction script
```

## Reproduce the controlled run

Requirements:

- Windows PowerShell 7 or later;
- [Ollama](https://ollama.com/) running locally;
- `ministral-3:3b` installed with `ollama pull ministral-3:3b`.

From the repository root:

```powershell
.\scripts\run_ministral_test.ps1
```

The script uses the same prompt and transcript with an 8192-token context, temperature 0, seed 42, native JSON mode, and a 3000-token output limit. It creates a new timestamped JSON result without overwriting the audited run.

## Current status

- [x] Task and correctness criteria defined
- [x] English and Spanish Deliverable 1 sources synchronized
- [x] Local Ministral model and hardware path validated
- [x] Reproducible 4K/8K direct-prompt experiment audited
- [ ] Run the same controlled test with Qwen 3.5 4B and Phi-4 Mini
- [ ] Implement temporal resolver and evidence verifier stages
- [ ] Build and annotate a larger evaluation set

## Deliverable sources

- [English executive-summary source](./Deliverable_1_BA_XG_ER_DV.md)
- [Spanish executive-summary source](./Deliverable_1_BA_XG_ER_DV_ESPAÑOL.md)

Both files contain LaTeX ready to paste into Overleaf. Any future content or layout change must be applied to both language versions.
