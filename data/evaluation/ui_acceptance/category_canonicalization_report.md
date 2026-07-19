# Narrow Gemini category canonicalization report

Date: 2026-07-19  
Environment: local repository; Gemini `gemini-2.5-flash` through Vertex for replay  
Policies: `EDITORIAL_GATE_POLICY=off`, `PUNCTUATION_POLICY=off`  
Production deployment/configuration: unchanged

## Outcome

Implemented one exact category canonicalizer at the Gemini finding decode boundary.
It runs before `Finding.model_validate` for discovery, judgment, and repair
responses. The normal adjudication, gates, repair flow, and strict
`FindingValidator` still run afterward.

No contradiction salvage, fuzzy matching, free-text inference, Run5/Run5b
change, punctuation change, prompt change, or production change was made.

## Reviewed mappings

- Generic `consistency`, `internal_inconsistency`, or `contradiction` uses
  deterministic rule precedence:
  `CONS-DATE` > `CONS-NUMBER` > `CONS-NAME` > `CONS-CLAIM`.
- `numbers` requires `CONS-NUMBER`.
- `date` requires `CONS-DATE`.
- `name` requires `CONS-NAME`.
- Existing canonical categories pass through after exact syntax normalization.
- Unknown and uncorroborated aliases remain unknown for strict rejection.

Normalization is limited to casing, surrounding whitespace, spaces, hyphens,
and repeated underscores. There is no substring, fuzzy, Arabic-keyword, or
explanation-based category inference.

## Historical D06 before/after

Historical model payload before canonicalization:

```json
{
  "finding_id": "FND-AI-0001",
  "document_id": "UI-D06",
  "segment_id": "SEG-002",
  "source": "gemini",
  "category": "internal_inconsistency",
  "decision": "needs_editor_review",
  "severity": "high",
  "original_text": "تنفيذ المشروع سيبدأ في سبتمبر المقبل. وأضافت أن الأعمال انطلقت فعليا في يوليو",
  "suggested_text": null,
  "start_offset": 13,
  "end_offset": 88,
  "rule_ids": ["CONS-CLAIM"],
  "entity_ids": [],
  "explanation_ar": "يوجد تناقض داخلي في النص حيث يذكر أن تنفيذ المشروع سيبدأ في سبتمبر المقبل ثم يضيف أن الأعمال انطلقت فعليا في يوليو.",
  "confidence": 1.0,
  "requires_editor_review": true
}
```

After decode-boundary canonicalization and ordinary deterministic offset
realignment:

```json
{
  "finding_id": "FND-AI-0001",
  "document_id": "UI-D06",
  "segment_id": "SEG-002",
  "source": "gemini",
  "category": "claim_contradiction",
  "decision": "needs_editor_review",
  "severity": "high",
  "original_text": "تنفيذ المشروع سيبدأ في سبتمبر المقبل. وأضافت أن الأعمال انطلقت فعليا في يوليو",
  "suggested_text": null,
  "start_offset": 15,
  "end_offset": 92,
  "rule_ids": ["CONS-CLAIM"],
  "entity_ids": [],
  "confidence": 1.0,
  "requires_editor_review": true,
  "validation_status": "valid",
  "validation_errors": []
}
```

Exact mapping audit:

```json
{
  "raw_category": "internal_inconsistency",
  "normalized_category": "internal_inconsistency",
  "canonical_category": "claim_contradiction",
  "rule_ids": ["CONS-CLAIM"],
  "mapping_occurred": true,
  "alias_mapping_occurred": true,
  "reason_code": "category_canonicalization:cons-claim"
}
```

The focused historical-payload test confirms `[13, 88)` realigns to
`[15, 92)`, category validation passes, `suggested_text` remains `null`, and no
validator errors remain.

## D01-D07 live local replay

Primary evidence:
`data/evaluation/ui_acceptance/category_canonicalization_d01_d07_replay.json`

Supplemental D05 retry:
`data/evaluation/ui_acceptance/category_canonicalization_d05_retry.json`

| Case | Final local result | Category / decision | Category mapping |
|---|---|---|---|
| D01 | Surfaced; validator valid | `numeric_contradiction` / `replace` | Canonical unchanged |
| D02 | Surfaced; validator valid | `numeric_contradiction` / `hard_warning`; no replacement | Canonical unchanged |
| D03 | Surfaced; validator valid | `numeric_contradiction` / `replace` | Canonical unchanged |
| D04 | Surfaced; validator valid | `numeric_contradiction` / `hard_warning`; no replacement | Canonical unchanged |
| D05 | Primary pass hit existing top-level-list parser defect; one retry surfaced normally | `headline_body_mismatch` / `needs_editor_review`; no replacement | Canonical unchanged |
| D06 | Surfaced; validator valid; suggest-only | `numeric_contradiction` / `hard_warning`; `suggested_text=null` | Canonical unchanged in this stochastic live response |
| D07 | Clean; zero findings | None | None |

D02 and D03 happened to surface in this live replay, but this task did not
change numeric detection or judgment logic and does not claim to fix them.

The live D06 response did not reproduce the historical alias: Gemini emitted
the already-known `numeric_contradiction` category with `CONS-CLAIM` and
`CONS-DATE`. Per the approved design, known canonical categories are preserved.
The historical D06 payload and all approved alias paths are therefore covered
deterministically in focused tests.

Every parsed category in the live replay was already canonical, so the audit
recorded no semantic category mappings outside the targeted historical-payload
tests. Editorial and punctuation gate logs remained `off`.

## Tests

Focused:

```text
python -m pytest tests/test_category_canonicalization.py tests/test_gemini_gate.py tests/test_validator.py tests/test_validator_pipeline_diagnostics.py -q
31 passed
```

Complete local-safe suite:

```text
AI_CLIENT=mock
USE_GCP=false
PUNCTUATION_POLICY=off
EDITORIAL_GATE_POLICY=off
python -m pytest -q
149 passed, 1 skipped in 6.44s
```

Coverage includes exact mapping, rule precedence, canonical passthrough,
uncorroborated-alias rejection, no fuzzy matching, discovery/judgment/repair
parsing, D06 strict validation, offset realignment, and continued rejection of
invalid document, segment, rule, entity, span, and explanation fields.

## Internal audit evidence

Admin pipeline logs now retain per decoded finding:

- phase (`discover`, `judge`, or `repair`);
- raw and normalized model category;
- final canonical category;
- supplied rule IDs;
- whether syntax or alias mapping occurred;
- structured reason code.

Public `ReviewStage` summaries do not expose raw model responses, prompts, or
the detailed canonicalization audit.

## Changed files

- `app/category_canonicalization.py`
- `app/ai/gemini_client.py`
- `app/postprocess/gemini_gate.py`
- `app/postprocess/adjudicator.py`
- `app/orchestration/review.py`
- `scripts/replay_contradiction_salvage.py`
- `tests/test_category_canonicalization.py`
- `tests/test_gemini_gate.py`
- `tests/test_validator_pipeline_diagnostics.py`
- `data/evaluation/ui_acceptance/category_canonicalization_d01_d07_replay.json`
- `data/evaluation/ui_acceptance/category_canonicalization_d05_retry.json`
- `data/evaluation/ui_acceptance/category_canonicalization_report.md`
- `handoff/to_chatgpt.md`

## Remaining risks and follow-ups

1. Gemini still emits invalid `adjudication_verdict` values such as `accepted`
   and `kept`; the existing heuristic fallback handled them. This task did not
   change those values.
2. The primary D05 replay exposed an existing decoder defect when Gemini
   returned a top-level JSON list. A retry returned the expected object
   envelope and D05 surfaced. List-envelope handling was not changed because it
   is outside this category-only task.
3. The live D06 response labeled a timeline issue as the already-known
   `numeric_contradiction` despite carrying `CONS-DATE`. The approved rule says
   existing canonical categories remain unchanged, so this was not rewritten.
4. Live Gemini output is stochastic. The deterministic mapping and strict
   rejection tests are the acceptance evidence for the category boundary.

## Safety conclusion

Strict rejection remains in force for arbitrary unknown categories and for
reviewed aliases that lack the required structured rule. Canonicalization does
not bypass any other validator error.

The narrow change is suitable for deployment review, with the D05 list-envelope
defect and invalid adjudication verdicts explicitly tracked as separate
follow-ups. No deployment was performed.
