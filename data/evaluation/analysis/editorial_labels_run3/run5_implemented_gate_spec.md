# Run5b implemented gate specification

Status: repaired candidate for `EDITORIAL_GATE_POLICY=run5` before `gemini_run5b_editorial_gates`.  
Previous run5 remains immutable.

## Shared contract

- Input: merged mechanical + AI findings after adjudication.
- Output: kept / suppressed / audit events with `editorial_gate:<reason_code>`.
- Default policy remains `off`.
- Fail open to editor review when support for suppression cannot be demonstrated.

## R1 — attribution

Reason: `attribution_vague_or_already_attributed`

Suppress only vague-source nags or claims already attributed before the span.

Keep / fail open when:

- explanation identifies material unattributed publisher-voice claims;
- category is `attribution_strength` or explanation identifies certainty/confirmation escalation (`أكد`, `مؤكد`, modality inflation).

Do not treat the finding span itself as proof of prior attribution.

## R2 — clarity

Reason: `clarity_generic_no_concrete_defect`

Applies to Gemini/mock **and mechanical** clarity findings.

Suppress only generic long-paragraph / clarify / split advice without a concrete defect.

Keep digit-script mixing, ambiguous referents, contradictions, missing referents, and other concrete defects.

## R4 — headline

Reason: `headline_supported_compression`

Suppress only when:

1. explanation is ordinary compression / style certainty wording;
2. body positively supports the headline core claim (lexical overlap ≥ 0.4);
3. no material-conflict marker and no possibility→certainty escalation allegation.

Otherwise keep (fail open).

## Non-goals

No R3/R5, no numeric/date suppression, no prompt/model changes, no auto-publish.
