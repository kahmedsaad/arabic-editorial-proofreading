# Validator autopsy: D01 and D06

Date: 2026-07-19  
Environment: local real review pipeline, Gemini `gemini-2.5-flash` through Vertex  
Overrides: `EDITORIAL_GATE_POLICY=off`, `PUNCTUATION_POLICY=off`

## Scope and immutability

This autopsy did not change prompts, frozen Run3/Run4/Run5/Run5b outputs,
gold data, evaluation runs, production configuration, or production data.
The model was called locally through the real `ReviewOrchestrator`.

Raw safe trace (no prompts or raw model responses):

`data/evaluation/ui_acceptance/d01_d06_autopsy_raw.json`

## Executive conclusion

- **D01's production rejection did not reproduce.** The current model emitted a
  known category (`numeric_contradiction`). Deterministic offset realignment
  corrected the span and the finding passed validation.
- **D06 did reproduce a validation failure**, but its only error was an
  explicitly non-allowlisted structural/schema error:
  `unknown category: internal_inconsistency`.
- The ordinary LLM repair returned D06, but changed the category to another
  unknown value, `contradiction`. The second pass therefore failed with
  `unknown category: contradiction`.
- Because unknown categories are forbidden salvage inputs, no contradiction
  warning salvage was implemented.

## D01 — current live-model reproduction

### Article segmentation

- Document: `UI-D01`
- Headline: `SEG-001`, `ارتفاع المبيعات`
- Body: `SEG-002`

### Candidate generation payload

```json
{
  "finding_id": "FND-AI-001",
  "document_id": "UI-D01",
  "segment_id": "SEG-002",
  "source": "gemini",
  "category": "numeric_contradiction",
  "decision": "hard_warning",
  "severity": "high",
  "original_text": "وهو ما يمثل تراجعا قدره مليونا ريال.",
  "suggested_text": "وهو ما يمثل ارتفاعا قدره مليونا ريال.",
  "start_offset": 75,
  "end_offset": 108,
  "rule_ids": ["CONS-CLAIM", "CONS-NUMBER"],
  "entity_ids": [],
  "explanation_ar": "الجملة تشير إلى تراجع في المبيعات بمقدار مليوني ريال، بينما الأرقام المذكورة سابقًا (من 10 ملايين إلى 12 مليون ريال) تشير إلى ارتفاع بنفس المقدار. هذا تناقض مباشر في المعلومات العددية.",
  "confidence": 1.0,
  "requires_editor_review": true
}
```

### Stage-by-stage decisions

1. **Candidate generation:** one candidate (payload above).
2. **Judgment:** Gemini returned an otherwise matching finding with invalid
   `adjudication_verdict="accepted"`. Schema parsing rejected that judgment
   payload, and `judge_candidates` used its existing heuristic fallback,
   preserving the candidate.
3. **Non-LLM gate:** kept.
4. **Adjudication:** `SHOW`.
5. **Editorial gate:** policy `off`; kept.
6. **Punctuation gate:** policy `off`; kept.
7. **First validator pass:** offset realignment ran. The supplied
   `[75, 108)` span did not match the original text; unique-text realignment
   moved it to `[72, 108)`. No validation errors remained.
8. **Repair request/response:** not invoked because validation passed.
9. **Second validator pass:** not invoked.
10. **Final exposure:** one valid `hard_warning`.

### D01 root-cause status

The earlier production run recorded one validator rejection but did not retain
the rejected payload or exact error. With the current live model, D01 passes.
Therefore the production D01 root cause cannot be established from available
evidence and must not be guessed. The added admin-only validation diagnostics
will retain the exact payload, realignment, and errors on future occurrences.

## D06 — reproduced failure

### Article segmentation

- Document: `UI-D06`
- Headline: `SEG-001`, `بدء المشروع في سبتمبر`
- Body: `SEG-002`

### Candidate generation payload

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
  "explanation_ar": "يوجد تناقض داخلي في النص حيث يذكر أن 'تنفيذ المشروع سيبدأ في سبتمبر المقبل' ثم يضيف أن 'الأعمال انطلقت فعليا في يوليو'. هذا يخلق ارتباكًا حول تاريخ بدء المشروع الفعلي، مما يؤثر أيضًا على دقة العنوان الذي يشير إلى بدء المشروع في سبتمبر.",
  "confidence": 1.0,
  "requires_editor_review": true
}
```

### Stage-by-stage decisions

1. **Candidate generation:** one candidate (payload above).
2. **Judgment:** Gemini returned an otherwise matching finding with invalid
   `adjudication_verdict="kept"`. Schema parsing rejected that judgment
   payload, and the existing heuristic fallback preserved the candidate.
3. **Non-LLM gate:** kept.
4. **Adjudication:** `SHOW`.
5. **Editorial gate:** policy `off`; kept.
6. **Punctuation gate:** policy `off`; kept.
7. **First validator pass:**
   - Offset realignment ran: `[13, 88)` → `[15, 92)`.
   - Document ID valid.
   - Segment ID valid.
   - Realigned original text and bounds valid.
   - Rule `CONS-CLAIM` approved.
   - No entity IDs.
   - Explanation present.
   - Decision and severity valid.
   - Exact error: `unknown category: internal_inconsistency`.
8. **Repair request:** included the complete rejected finding and exact error.
9. **Repair response:** returned the same finding and span, but changed
   `category` to `contradiction`.
10. **Second validator pass:** no offset realignment was needed; exact error:
    `unknown category: contradiction`.
11. **Final exposure:** zero findings; the repaired finding remained rejected.

### D06 root cause

The model and repair model used category names outside the repository's
authoritative category set. This is a schema/category canonicalization failure,
not an anchoring-only problem. Both errors are explicitly prohibited from
salvage.

Known relevant categories already include:

- `temporal_contradiction`
- `claim_contradiction`
- `cross_paragraph_contradiction`
- `numeric_contradiction`
- `consistency`

Neither `internal_inconsistency` nor `contradiction` is known.

## Diagnostics added

Admin-only pipeline diagnostics now record:

- complete pre-realignment finding payload;
- complete post-realignment payload;
- whether offset realignment changed offsets;
- exact first-pass and second-pass validation errors;
- repair-returned IDs and payloads;
- final rejected payloads.

Public `ReviewStage` output remains count/sample based. Prompts and sensitive raw
model internals were not added to public UI output.

Changed diagnostic code:

- `app/validation/validator.py`
- `app/orchestration/review.py`

Tests:

- `tests/test_validator.py`
- `tests/test_validator_pipeline_diagnostics.py`

## Stop decision and narrower recommendation

The task explicitly forbids salvaging unknown categories. D06 failed for an
unknown category on both validator passes, so forcing it through as a warning
would weaken schema enforcement and violate the requested safety boundary.

Recommended separate narrow fix:

1. Define and approve a small category-alias table at the model-output parsing
   boundary (for example, only explicitly reviewed mappings to existing
   categories).
2. Re-run the normal validator after canonicalization; do not bypass it.
3. Keep unknown/unmapped categories rejected.
4. Add D06-specific tests proving the selected canonical category is correct.
5. Re-run D01–D07 before reconsidering any salvage fallback.

No alias was chosen or implemented in this task because deciding whether D06 is
`temporal_contradiction`, `claim_contradiction`, or
`cross_paragraph_contradiction` is a schema decision, not a presentation repair.
