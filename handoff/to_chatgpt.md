# Cursor → ChatGPT

Paste this whole file into ChatGPT.

## Latest outcome: Gemini response-envelope hardening

Implemented only Gemini JSON response-envelope hardening and safe parser/system
failure reporting.

Full evidence:

`data/evaluation/ui_acceptance/gemini_envelope_hardening_report.md`

Live replay:

`data/evaluation/ui_acceptance/gemini_envelope_hardening_d01_d07_replay.json`

No deployment, commit, push, prompt change, Run5b activation, punctuation
change, production setting change, frozen-artifact edit, or Chrome production
test was performed.

## Root cause and fix

`GeminiEditorialAIClient._parse_findings` called `data.get(...)` before safely
branching on a decoded top-level list. A valid D05 list therefore raised:

`'list' object has no attribute 'get'`

Discovery converted that technical failure into synthetic
`FND-AI-FALLBACK`, making a parser error resemble an article defect.

Now one shared typed decoder supports:

- top-level list;
- object containing a list-valued `findings`;
- valid empty lists.

It safely rejects primitives, unsupported single objects, and non-list
`findings`. The equivalent rule-authoring list/object bug now uses the same
decoder without changing rule semantics.

Items are parsed independently. Valid siblings survive malformed items.
Diagnostics retain only indexes and safe summarized reasons, never rejected
payloads.

## Failure behavior

- Discovery parse/system failure returns zero AI findings and an internal
  degraded-analysis diagnostic. No fabricated editorial finding is created.
- Judgment parse failure may use the existing heuristic fallback and records it
  explicitly.
- Repair parse failure uses local repair or leaves strict validator rejection
  intact.
- Admin pipeline logs record phase, envelope, failure type, counts, rejected
  indexes, and fallback status.
- Public stages contain no prompts or raw model responses.

Category canonicalization still runs before `Finding.model_validate`. Its
reviewed mappings were not modified.

## Tests

- Focused envelope/canonicalization/validator suite: **49 passed**
- Complete local-safe suite: **167 passed, 1 skipped**

The deterministic exact D05 top-level-list fixture surfaced its valid
contradiction warning on the first orchestrator pass, with no retry and no
`FND-AI-FALLBACK`.

Coverage includes all required envelopes and failures, mixed valid/invalid
items, sibling survival, discovery/judgment/repair behavior, explicit fallback
diagnostics, repair followed by strict rejection, public-output safety,
rule-authoring lists, and unchanged historical D06 canonicalization.

## D01-D07 live replay

Configuration:

- Gemini `gemini-2.5-flash` through Vertex
- `EDITORIAL_GATE_POLICY=off`
- `PUNCTUATION_POLICY=off`

Results:

- D01 surfaced and passed strict validation.
- D02 surfaced; observational only.
- D03 surfaced as an editor suggestion only; nothing was applied.
- D04 surfaced and passed strict validation.
- D05's envelope parsed on the single live pass without retry; invalid judgment
  enums triggered the existing explicitly diagnosed heuristic fallback.
- D06 surfaced and passed strict validation.
- D07 remained clean with zero findings.

The live D05 response used an object envelope; the deterministic fixture proves
the exact top-level-list envelope that previously failed.

## Changed files

- `app/ai/gemini_client.py`
- `app/orchestration/review.py`
- `scripts/replay_contradiction_salvage.py`
- `tests/test_gemini_envelope.py`
- `data/evaluation/ui_acceptance/gemini_envelope_hardening_d01_d07_replay.json`
- `data/evaluation/ui_acceptance/gemini_envelope_hardening_report.md`
- this handoff

## Remaining risks

1. Invalid Gemini `adjudication_verdict` values (`accepted`, `kept`) remain a
   separate follow-up. They are now safely diagnosed per item; they were not
   normalized.
2. Unsupported single-finding objects are deliberately rejected because the
   established contracts are list or named list envelope.
3. Live model output remains stochastic; deterministic fixtures provide
   envelope acceptance evidence.

## Recommendation

The response-envelope hardening is **ready for deployment review**. D05's exact
list shape passes on the first deterministic attempt, parser/system failures no
longer appear as editorial findings, valid siblings survive malformed items,
and strict validation remains intact.

No deployment or commit was performed.
