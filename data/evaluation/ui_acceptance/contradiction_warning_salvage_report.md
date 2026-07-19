# Contradiction-warning salvage report

Date: 2026-07-19  
Status: **blocked safely; salvage not implemented**

## Decision

The requested contradiction-warning salvage path was not implemented.

The exact autopsy found:

- D01 currently passes normal validation after deterministic offset
  realignment, so there is no reproducible D01 validator failure to salvage.
- D06 fails with `unknown category: internal_inconsistency`.
- Ordinary repair returns D06 as `category=contradiction`, which fails with
  `unknown category: contradiction`.

Unknown categories are expressly non-allowlisted by the task. This triggers the
instruction to stop rather than force the finding through validation.

## Before/after

There is no behavior change to finding exposure:

| Case | Before | After this task |
|------|--------|-----------------|
| D01 current local live replay | hard warning surfaced | unchanged |
| D06 current local live replay | rejected: unknown category | unchanged |
| D02/D03 | separate earlier-stage misses | unchanged; not investigated or fixed |
| D04/D05 | existing hard warnings | unchanged |
| D07 | clean zero finding | unchanged |

No `CONTRADICTION_WARNING_SALVAGE` setting was added because no compliant
salvage behavior could be enabled.

## Implementation delivered

Only diagnostic/audit improvements were made:

- First and second validator passes retain complete admin-only payloads.
- Offset realignment is explicitly recorded.
- Repair-returned IDs and payloads are recorded.
- Final rejected payloads are recorded.
- Public UI stage summaries remain limited and do not expose prompts or raw
  model internals.

## Focused test results

Command:

```text
python -m pytest tests/test_validator.py tests/test_validator_pipeline_diagnostics.py -q
```

Result: **5 passed**.

Coverage added:

- deterministic offset realignment is audited;
- non-allowlisted unknown category remains rejected;
- D06-shaped first-pass and repaired second-pass failures are both audited;
- repair response is retained in the admin pipeline log;
- final exposure remains empty for the prohibited unknown category.

## Full-suite and D01–D07 replay status

The task's stop condition was reached during Phase 1. Therefore:

- no salvage implementation was created;
- no setting-on replay exists;
- the requested setting-off versus setting-on comparison is not applicable;
- no claim is made that D01/D06, D02/D03, or the seven-case suite was fixed.

An unrestricted `pytest -q` run inherited `.env`'s live Gemini configuration,
entered network-backed tests, and was stopped after more than eight minutes
because it was not a deterministic local suite.

The complete local-safe suite was then run with:

```text
AI_CLIENT=mock
USE_GCP=false
PUNCTUATION_POLICY=off
EDITORIAL_GATE_POLICY=off
python -m pytest -q
```

Final result after the concurrency-safe diagnostics refactor:
**127 passed, 1 skipped in 12.68s**.

## Remaining risks

1. Historical D01 rejection is not reproducible and its old payload/error was
   not retained. Future occurrences are now auditable.
2. Gemini judgment responses used invalid adjudication enum values
   (`accepted`, `kept`), causing the existing heuristic fallback. That did not
   cause the validator rejection, but it is another schema-compliance signal.
3. A broad alias such as `contradiction → claim_contradiction` could
   misclassify numeric, temporal, legal, or cross-paragraph findings.
4. D02 and D03 remain separate detection/judgment failures and must not be
   represented as validator or salvage fixes.

## Recommendation

**Not ready for deployment review as a recall fix.** The diagnostics-only
change is low risk, but it does not change D06 behavior.

Request a separate, narrowly reviewed category-canonicalization task:

- choose explicit aliases based on evidence;
- canonicalize before adjudication/validation;
- retain strict rejection of unknown aliases;
- run D01–D07 with editorial gate and punctuation both off;
- only after that evidence, reconsider an anchoring-only salvage fallback.
