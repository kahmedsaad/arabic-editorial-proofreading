Working in C:\Users\khhab\Downloads\ai-proofreading. Read docs/EDITORIAL_LABELING.md and docs/RUN4_NO_PUNCTUATION.md first. Do not overwrite run3 or add run5 gates until labels are done.

# Task: harden Gemini response-envelope parsing

Labels are complete. The narrow category-canonicalization implementation is accepted. Do not modify its reviewed mappings in this task.

Implement only Gemini JSON response-envelope hardening and safe parser-failure reporting.

Do not deploy, enable Run5b, change prompts, loosen validation, modify punctuation policy, or edit frozen artifacts.

## Confirmed defect

`GeminiEditorialAIClient._parse_findings` accesses `data.get(...)` before safely handling a decoded top-level JSON list.

During D05, Gemini returned a valid top-level list. This caused:

`'list' object has no attribute 'get'`

The exception was then converted into an apparent editorial finding with an explanation such as `تعذر إكمال تحليل النموذج`. A technical model/parser failure must never be presented as a defect in the editor's article.

Read:

- `handoff/to_chatgpt.md`
- `data/evaluation/ui_acceptance/category_canonicalization_report.md`
- `data/evaluation/ui_acceptance/category_canonicalization_d01_d07_replay.json`
- `data/evaluation/ui_acceptance/category_canonicalization_d05_retry.json`
- `app/ai/gemini_client.py`
- existing parser, orchestrator, validator, and canonicalization tests

## Required parser behavior

After JSON decoding, branch explicitly by type:

- Top-level list: use it as the findings list.
- Top-level object containing `findings`: require `findings` to be a list.
- Empty top-level list or empty `findings` list: valid zero-finding response.
- A single-finding object: support it only if the established contract permits it; otherwise reject with a typed diagnostic.
- Any other top-level type: reject safely with a typed diagnostic.

For individual items:

- Require a JSON object.
- Parse items independently.
- A malformed item must not discard valid siblings.
- Record the rejected item index and a safe summarized reason.
- Do not expose prompts or unrestricted raw model output.
- Keep category canonicalization before `Finding.model_validate`.

Use the same envelope logic for discovery, judgment, and repair. Avoid three separate parser implementations.

Inspect rule-authoring for the same unsafe list/object expression. Fix only the equivalent envelope bug if present; do not change rule-authoring semantics.

## Failure handling

Do not convert JSON decoding, envelope, or schema failures into editorial findings.

Record through internal/admin diagnostics:

- phase: discover, judge, or repair;
- failure type and safe reason;
- valid and rejected item counts;
- rejected item indexes;
- whether a heuristic or local fallback was used.

Preserve safe phase behavior:

- Discovery parse failure: return no fabricated article finding and record degraded analysis.
- Judgment parse failure: the existing heuristic fallback may preserve candidates, but diagnose it explicitly.
- Repair parse failure: use existing local repair or strict rejection; never force an invalid finding through validation.

If no non-editorial degraded-analysis channel exists, add the smallest internal/admin stage diagnostic. Do not add system failures to `response.findings`.

Do not normalize invalid `adjudication_verdict` values such as `accepted` or `kept` in this task. Track that as a separate follow-up because it can change judgment behavior.

## Tests

Add deterministic tests for:

- top-level list containing a valid finding;
- object envelope containing `findings`;
- empty top-level list;
- empty `findings` list;
- primitive top-level JSON values;
- object with non-list `findings`;
- mixed valid and malformed items;
- valid siblings surviving malformed items;
- canonicalization running for list-envelope items;
- discovery, judgment, and repair list envelopes;
- parse failures producing no editorial finding;
- explicit judgment-fallback diagnostics;
- repair failure preserving strict validation;
- no prompt/raw payload leakage into public output;
- historical D06 canonicalization remaining unchanged.

Run focused tests and the complete local-safe suite.

## Replay

Replay D01-D07 locally with:

- `EDITORIAL_GATE_POLICY=off`
- `PUNCTUATION_POLICY=off`

For D05, use a deterministic fixture with the exact top-level-list shape that previously failed. D05 must surface the valid contradiction warning on the first pass without retry.

Then perform one live-model D01-D07 replay only if credentials are already configured.

Acceptance criteria:

- D05 list envelope parses on the first attempt.
- No parser/system error appears as an editorial finding.
- D01, D04, D05, and D06 remain surfaced.
- D07 remains clean.
- D02 and D03 are observational only.
- Category canonicalization and strict validation remain intact.
- D03 remains an editor suggestion only and is never automatically applied or published.

## Deliverables

Create:

`data/evaluation/ui_acceptance/gemini_envelope_hardening_report.md`

Include root cause, before/after D05 behavior, deterministic tests, replay results, changed files, remaining risks, and confirmation that technical failures no longer appear as editorial findings.

Update `handoff/to_chatgpt.md` with the evidence and recommendation.

Do not commit, push, deploy, modify production configuration, or use Chrome MCP against production during this task.
