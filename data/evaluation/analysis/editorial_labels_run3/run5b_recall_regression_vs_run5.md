# Run5 critical-recall regression attribution

Baseline: `benchmark_v2\results\report_gemini_run5_editorial_gates.json`  
Candidate: `benchmark_v2\results\report_gemini_run5b_editorial_gates.json`

## Aggregate

- Lost critical items (matched in baseline, unmatched in candidate): **5**
- Gate-suppressible under current R1/R2/R4 replay: **0**

### By root cause

- `emitted_but_below_match_threshold_or_wrong_span`: 3
- `model_or_pipeline_did_not_emit_matching_finding`: 2

### By gate reason (replay on baseline finding)

- none

### Attribution caveat

Run5 benchmark outputs did not persist `rejected_findings` or gate reason codes.
Therefore live suppressions cannot be proven from artifacts alone.
Attribution below combines missing exposed matches with deterministic replay of
the baseline matched finding through the current editorial gate.

## Lost critical items

### case-0010 gold_index=0

- category: `caption_framing`
- expected spans: ['المعارضة المخربة']
- baseline finding: `FND-AI-0001` / `headline_body_mismatch` / `قوات الأمن تطارد عناصر المعارضة المخربة`
- gate replay on baseline finding: `None`
- disposition: `present_but_unmatched`
- root cause: `emitted_but_below_match_threshold_or_wrong_span`

### case-0033 gold_index=0

- category: `publisher_voice`
- expected spans: ['وقد اعترف المتهم بالفعل']
- baseline finding: `FND-AI-0001` / `claim_contradiction` / `قال مصدر أمني إن الموقوف اعترف. وقال محاميه إن موكله ينفي الاعتراف. وكتب التقرير: وقد اعترف المتهم بالفعل.`
- gate replay on baseline finding: `None`
- disposition: `missing_from_exposed_findings`
- root cause: `model_or_pipeline_did_not_emit_matching_finding`

### case-0035 gold_index=0

- category: `economic_reasoning`
- expected spans: ['نمو حقيقي بنسبة 20%']
- baseline finding: `FND-AI-0001` / `numeric_contradiction` / `وبعد تضخم 25% وصف التقرير الارتفاع بأنه نمو حقيقي بنسبة 20%.`
- gate replay on baseline finding: `None`
- disposition: `missing_from_exposed_findings`
- root cause: `model_or_pipeline_did_not_emit_matching_finding`

### case-0036 gold_index=0

- category: `exaggeration`
- expected spans: ['يكتسح جميع الدوائر']
- baseline finding: `FND-AI-0001` / `headline_body_mismatch` / `الحزب يكتسح جميع الدوائر`
- gate replay on baseline finding: `None`
- disposition: `present_but_unmatched`
- root cause: `emitted_but_below_match_threshold_or_wrong_span`

### case-0039 gold_index=0

- category: `scope_error`
- expected spans: ['دون إصابات']
- baseline finding: `FND-AI-0001` / `headline_body_mismatch` / `الاحتجاجات تنتهي دون إصابات`
- gate replay on baseline finding: `None`
- disposition: `present_but_unmatched`
- root cause: `emitted_but_below_match_threshold_or_wrong_span`

