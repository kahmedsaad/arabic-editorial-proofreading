# Run5 implementation and validation report

Release recommendation: **`needs_adjustment`**

Gates R1/R2/R4 are implemented and measurable, but silence-set targets were missed and critical recall regressed beyond the acceptance band.

## 1. Correction adjudication and final label metrics

Immutable audit: `correction_adjudications.jsonl`  
Derived scoring input: `final_adjudicated_for_scoring.jsonl`  
Evidence summary: `FINAL_ADJUDICATION_EVIDENCE.md`

| Outcome | Count |
|---------|------:|
| accept | 13 |
| reject | 0 |
| uncertain | 4 |

| Metric | Original | Final adjudicated |
|--------|---------:|------------------:|
| keep | 23 | 18 |
| drop | 128 | 131 |
| uncertain | 12 | 14 |
| precision | 0.1523 | **0.1208** |

`expert_labels.jsonl` and source templates were not overwritten.

## 2. Exact gates implemented

Spec: `run5_implemented_gate_spec.md`  
Code: `app/postprocess/editorial_gate.py`  
Enforcement point: after adjudication, before punctuation gate / editor exposure (`app/orchestration/review.py`)

| Gate | Reason code | Scope |
|------|-------------|-------|
| R1 | `attribution_vague_or_already_attributed` | vague-source or already-attributed only |
| R2 | `clarity_generic_no_concrete_defect` | generic clarity / long-paragraph only |
| R4 | `headline_supported_compression` | supported certainty/compression only |

Non-goals confirmed:

- no R3 entity/militia
- no R5 spelling
- no numeric/date suppression
- no prompt/model change
- no auto-publish / auto-edit
- punctuation policy unchanged (`off` for this run)

Policy is opt-in: `EDITORIAL_GATE_POLICY=run5` (default `off`).

## 3. Files changed and commands run

Key files:

- `app/postprocess/editorial_gate.py`
- `app/orchestration/review.py`
- `app/config.py`
- `.env.example`
- `scripts/adjudicate_editorial_corrections.py`
- `scripts/run_silence_eval.py`
- `tests/test_editorial_gate.py`
- docs / evidence / handoff updates

Commands:

```powershell
python scripts/adjudicate_editorial_corrections.py
python scripts/validate_editorial_label_file.py --input data/evaluation/analysis/editorial_labels_run3/final_adjudicated_for_scoring.jsonl
python scripts/score_editorial_labels.py --input data/evaluation/analysis/editorial_labels_run3/final_adjudicated_for_scoring.jsonl --out-dir data/evaluation/analysis/editorial_labels_run3/final_adjudicated

$env:DEMO_AUTH_REQUIRED="false"; $env:AI_CLIENT="mock"; $env:USE_GCP="false"; $env:ADMIN_PASSWORD="admin"
python -m pytest -q --tb=short

$env:PYTHONIOENCODING="utf-8"
$env:AI_CLIENT="gemini"; $env:USE_GCP="true"
$env:PUNCTUATION_POLICY="off"; $env:EDITORIAL_GATE_POLICY="run5"
python scripts/run_silence_eval.py --dataset data/local/sprint2/silence_v1.jsonl --run-id gemini_run5_editorial_gates

python -m benchmark_v2.public.run_engine --out benchmark_v2/results/engine_outputs_gemini_run5_editorial_gates.json --run-id gemini_run5_editorial_gates
python -m benchmark_v2.private.scorer.cli --gold-dir benchmark_v2/private/gold --outputs benchmark_v2/results/engine_outputs_gemini_run5_editorial_gates.json --report benchmark_v2/results/report_gemini_run5_editorial_gates.json
```

## 4. Unit / integration test results

Focused suites: `37 passed` (`test_editorial_gate`, `test_punctuation_gate`, `test_editorial_label_scripts`).  
Full suite with local-safe env: `99 passed, 1 skipped`.

Coverage includes allow/suppress boundaries for R1/R2/R4, numeric pass-through, policy-off behavior, orchestrator reason-code diagnostics, and accepted-correction regressions (si 40 / 47 / 49 / 128 / 129).

## 5. Run5 versus run4 / run3

### Silence set (`silence_v1.jsonl`, 300 articles)

| Metric | run3 | run4 | **run5** | Target |
|--------|-----:|-----:|---------:|-------:|
| Clean editorial FP rate | 0.77 (all cats) | 0.4033 | **0.3133** | ≤0.15 |
| Findings / clean article | 1.9833 | 0.64 | **0.4967** | ≤0.25 |
| Zero-finding clean articles | — | 0.5967 | **0.6867** | ≥0.80 |
| Punctuation findings | 432 | 0 | **0** | unchanged off |

Category / family movement (run4 → run5):

| Family | run4 | run5 | Δ |
|--------|-----:|-----:|--:|
| Attribution | 49 | 26 | −47% |
| Clarity | 34 | 34 | 0% |
| Headline mismatch (category_report) | 35 | 14 | −60% |

Suppression reason-code counts (run5):

| Reason | Count |
|--------|------:|
| `attribution_vague_or_already_attributed` | 17 |
| `headline_supported_compression` | 13 |
| `clarity_generic_no_concrete_defect` | **0** |

Representative suppressions are stored in `data/evaluation/runs/gemini_run5_editorial_gates/report.json` (`editorial_suppression_examples`).

### Critical recall (hidden gold unchanged)

| Run | critical_recall | precision | recall | clean-case FP |
|-----|----------------:|----------:|-------:|--------------:|
| gemini_run1 | 0.4211 | 0.2745 | 0.4667 | 0.1538 |
| gemini_run2 | 0.7368 | 0.3929 | 0.7333 | 0.2308 |
| **run5** | **0.6316** | **0.4318** | **0.6333** | **0.1538** |

Critical-recall delta vs run2: **−10.5 pp** (worse than the ≤5 pp acceptance limit in the gate brief).

## 6. Release recommendation

**`needs_adjustment`**

Evidence:

1. Silence targets missed: FP 31.3% > 15%, findings/article 0.50 > 0.25, zero-finding 68.7% < 80%.
2. R2 did not fire on the live silence set (clarity remained 34/34).
3. R1 helped but under-shot the ≥60% attribution reduction goal (−47%).
4. Critical recall fell 10.5 pp vs run2.
5. Some R4 suppressions look over-broad (certainty language co-occurring with potentially material mismatches).

Recommended next adjustments (separate task):

1. Tighten R4 material keep-path (`يتناقض`, place/role/outcome mismatches) before any additional suppression.
2. Expand R2 generic-marker coverage against live clarity explanations, or require structured clarity subtypes.
3. Re-run silence + critical recall after those fixes only.

## Confirmations

- `gemini_run3` and `gemini_run4_no_punctuation` untouched
- hidden benchmark gold untouched
- Gemini prompts / model choice untouched
- numeric findings not gated
- R3 / R5 not implemented
- punctuation policy for the run remained `off`
- no auto-publish / auto-edit of editorial content
