# Run5 critical-recall regression attribution

Baseline: `benchmark_v2/results/report_gemini_run2.json`  
Candidate: `benchmark_v2/results/report_gemini_run5_editorial_gates.json`

## Aggregate

- Lost critical items (matched in baseline, unmatched in candidate): **3**
- Gate-suppressible under current R1/R2/R4 replay: **2**

### By root cause

- `likely_gate_or_nonemit; baseline_finding_matches_suppress_rule:attribution_vague_or_already_attributed`: 2
- `emitted_but_below_match_threshold_or_wrong_span`: 1

### By gate reason (replay on baseline finding)

- `attribution_vague_or_already_attributed`: 2

### Attribution caveat

Run5 benchmark outputs did not persist `rejected_findings` or gate reason codes.
Therefore live suppressions cannot be proven from artifacts alone.
Attribution below combines missing exposed matches with deterministic replay of
the baseline matched finding through the **run5** editorial gate rules as frozen
in the run5 evaluation artifacts / then-current implementation.

## Gate-loss summary (exact)

| Source | Lost critical items |
|--------|--------------------:|
| R1 `attribution_vague_or_already_attributed` | **2** (case-0005 gold_index=1; case-0038 gold_index=0) |
| R2 `clarity_generic_no_concrete_defect` | **0** |
| R4 `headline_supported_compression` | **0** |
| Non-gate (model/match variance) | **1** (case-0006 majority/numeric mismatch) |

## R2 zero-fire root cause (run5)

Of 34 run5 clarity findings, **33 were `mechanical`** (`MECH-MALFORMED` long-segment / digit-mix).
The run5 gate ran only on AI findings (`ai_kept`), so mechanical clarity bypassed R2 entirely
despite explanations matching `مقطع طويل جداً قد يحتاج إعادة تقسيم.`

## Lost critical items

### case-0005 gold_index=1

- category: `pronoun_ambiguity`
- expected spans: ['وأكد أنه وافق']
- baseline finding: `FND-AI-0002` / `attribution_strength` / `وأكد`
- gate replay on baseline finding: `attribution_vague_or_already_attributed`
- disposition: `not_in_exposed_findings;_rejected_findings_not_persisted`
- root cause: `likely_gate_or_nonemit; baseline_finding_matches_suppress_rule:attribution_vague_or_already_attributed`

### case-0006 gold_index=0

- category: `majority_precision`
- expected spans: ['بأغلبية أعضائه']
- baseline finding: `FND-AI-0001` / `numeric_contradiction` / `البرلمان يعتمد القانون بأغلبية أعضائه`
- gate replay on baseline finding: `None`
- disposition: `present_but_unmatched`
- root cause: `emitted_but_below_match_threshold_or_wrong_span`

### case-0038 gold_index=0

- category: `attribution_strength`
- expected spans: ['وشيكًا ومؤكدًا']
- baseline finding: `FND-AI-0005` / `attribution_strength` / `مؤكدًا`
- gate replay on baseline finding: `attribution_vague_or_already_attributed`
- disposition: `not_in_exposed_findings;_rejected_findings_not_persisted`
- root cause: `likely_gate_or_nonemit; baseline_finding_matches_suppress_rule:attribution_vague_or_already_attributed`
