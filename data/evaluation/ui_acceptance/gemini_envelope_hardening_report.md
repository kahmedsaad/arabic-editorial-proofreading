# Gemini response-envelope hardening report

Date: 2026-07-19  
Environment: local repository; Gemini `gemini-2.5-flash` through Vertex for the
single live replay  
Policies: `EDITORIAL_GATE_POLICY=off`, `PUNCTUATION_POLICY=off`  
Production deployment/configuration: unchanged

## Outcome

Gemini finding parsing now accepts both supported response envelopes through one
shared decoder:

- a top-level JSON list;
- an object whose `findings` field is a list.

Empty lists are valid zero-finding responses. Primitive top-level values,
single-finding objects without the required envelope, and non-list `findings`
fields fail with typed, safe diagnostics.

The equivalent unsafe list/object expression in rule authoring now uses the
same generic array-envelope decoder with the `rules` field. Rule-authoring
semantics were otherwise unchanged.

No category mapping, prompt, validator, gate, punctuation, production, frozen
run, or deployment setting was changed.

## Root cause

The previous parser decoded JSON and then evaluated:

```python
data.get("findings", data if isinstance(data, list) else [])
```

Python resolves the receiver before the default expression, so a valid
top-level list attempted `list.get(...)` and raised:

```text
'list' object has no attribute 'get'
```

Discovery caught that exception and created `FND-AI-FALLBACK`, a synthetic
`clarity` finding whose Arabic explanation described the technical failure.
That made a parser/model failure look like an article defect.

## D05 before and after

Previously observed valid response shape:

```json
[
  {
    "finding_id": "FND-D05-LIST",
    "document_id": "UI-D05",
    "segment_id": "SEG-001",
    "category": "headline_body_mismatch",
    "decision": "needs_editor_review",
    "severity": "high",
    "original_text": "فوز الفريق في النهائي",
    "suggested_text": null,
    "rule_ids": ["CONS-CLAIM"]
  }
]
```

Before hardening:

- parser raised `AttributeError`;
- discovery fabricated `FND-AI-FALLBACK`;
- the fallback was later gated for low confidence;
- D05 did not surface on that pass.

After hardening, the deterministic exact-shape fixture:

- identifies `top_level_list`;
- parses one valid item and rejects zero items;
- preserves category canonicalization before `Finding.model_validate`;
- surfaces `FND-D05-LIST` on the first orchestrator pass;
- keeps `suggested_text=null`;
- creates no parser/system editorial finding;
- requires no retry.

Diagnostic:

```json
{
  "phase": "discover",
  "status": "ok",
  "failure_type": null,
  "safe_reason": "parsed",
  "envelope_type": "top_level_list",
  "valid_item_count": 1,
  "rejected_item_count": 0,
  "rejected_item_indexes": [],
  "fallback_used": false,
  "fallback_type": null
}
```

## Item isolation and safe diagnostics

Finding items are parsed independently. A non-object or schema-invalid item is
recorded by zero-based index and safe summarized reason; valid siblings survive.
Diagnostics contain no rejected item payload.

Internal/admin diagnostics record:

- phase: `discover`, `judge`, or `repair`;
- envelope type and status;
- typed failure and safe reason;
- valid and rejected item counts;
- rejected item indexes and safe item-level reasons;
- whether a fallback ran and its type.

Phase behavior:

- discovery parse/system failure returns no AI finding and records degraded
  analysis;
- judgment parse failure may use the existing heuristic candidate fallback and
  records `fallback_type=heuristic_judge`;
- repair parse failure uses local repair or leaves the finding for strict
  rejection and records `fallback_type=local_repair`;
- valid empty discovery, judgment, and repair envelopes remain valid empty
  results.

Detailed diagnostics and raw traces stay in the existing admin-only pipeline
log. Public `ReviewStage` summaries contain neither prompts nor raw responses.

## Deterministic tests

Focused command:

```text
AI_CLIENT=mock
USE_GCP=false
PUNCTUATION_POLICY=off
EDITORIAL_GATE_POLICY=off
python -m pytest tests/test_gemini_envelope.py tests/test_category_canonicalization.py tests/test_gemini_gate.py tests/test_validator.py tests/test_validator_pipeline_diagnostics.py -q
```

Result: **49 passed**.

Coverage includes:

- top-level list and object envelopes;
- empty top-level and `findings` lists;
- primitive top-level values;
- non-list `findings`;
- unsupported single-finding objects;
- mixed valid and malformed items;
- valid sibling survival;
- list-envelope category canonicalization;
- discovery, judgment, and repair list envelopes;
- valid empty judgment output;
- no fabricated discovery finding on parse failure;
- explicit judgment fallback diagnostics;
- repair failure followed by strict validator rejection;
- no raw response in public stages;
- D05 first-pass deterministic orchestrator replay;
- top-level rule list handling;
- unchanged historical D06 canonicalization and strict validation.

Complete local-safe suite:

```text
AI_CLIENT=mock
USE_GCP=false
PUNCTUATION_POLICY=off
EDITORIAL_GATE_POLICY=off
python -m pytest -q
```

Result: **167 passed, 1 skipped in 15.45s**.

## Live D01-D07 replay

Evidence:

`data/evaluation/ui_acceptance/gemini_envelope_hardening_d01_d07_replay.json`

| Case | Final result | Notes |
|---|---|---|
| D01 | Surfaced, strict-valid | `numeric_contradiction`; editor warning |
| D02 | Surfaced, strict-valid | Observational; numeric logic unchanged |
| D03 | Surfaced, strict-valid | `25 بالمئة` → `15 بالمئة` suggestion only; not applied |
| D04 | Surfaced, strict-valid | Non-actionable numeric warning |
| D05 | Surfaced on the single live pass | Object envelope parsed; invalid judgment enums triggered the existing diagnosed heuristic fallback |
| D06 | Surfaced, strict-valid | Timeline/headline contradiction remained editor-reviewed |
| D07 | Clean | Zero findings |

The live D05 response used the object envelope, while the deterministic D05
fixture proves the exact top-level-list shape that previously failed. During
live judgment, invalid `adjudication_verdict` values were rejected item by item
and explicitly diagnosed; the existing heuristic fallback preserved candidates.
No raw item payload appeared in those diagnostics.

No suggestion was accepted, applied, or published. D03 remained an editor
suggestion only.

## Changed files

- `app/ai/gemini_client.py`
- `app/orchestration/review.py`
- `scripts/replay_contradiction_salvage.py`
- `tests/test_gemini_envelope.py`
- `data/evaluation/ui_acceptance/gemini_envelope_hardening_d01_d07_replay.json`
- `data/evaluation/ui_acceptance/gemini_envelope_hardening_report.md`
- `handoff/to_chatgpt.md`

## Remaining risks and follow-ups

1. Gemini still emits invalid `adjudication_verdict` values such as `accepted`
   and `kept`. They are now safely diagnosed per item, but normalization remains
   a separate task as required.
2. Unsupported single-finding objects are deliberately rejected because the
   established contracts are list or named list envelope.
3. Live Gemini output remains stochastic; deterministic fixtures are the
   acceptance evidence for every envelope branch.
4. Existing canonical categories and reviewed alias mappings remain unchanged.

## Recommendation

The envelope hardening is ready for deployment review. D05's exact list shape
passes on the first deterministic attempt, parser/system failures are no longer
converted into editorial findings, valid siblings survive malformed items, and
strict category/structural validation remains intact.

No commit, push, deployment, production configuration change, or production UI
test was performed.
