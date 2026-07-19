# Run5b implementation and validation report

Release recommendation: **`needs_adjustment`**

Critical recall is the hard safety gate. Run5b recovered the known Run5 gate-safety defects in deterministic replay and made R2 effective on the silence set, but the live critical-recall score fell to `0.4211`, below the `0.6868` acceptance floor. Silence also remains above the editorial FP / findings-per-article targets.

## 1. Root-cause analysis

Diagnostics: `run5b_gate_diagnostics.md`  
Recall attribution: `run5_recall_regression_attribution.md`, `run5b_recall_regression_vs_run2.md`, `run5b_recall_regression_vs_run5.md`

### Run5 regression causes

| Source | Lost critical vs Run2 | Assessment |
|--------|----------------------:|------------|
| R1 over-suppression of attribution-strength / certainty findings | 2 | Harmful; corrected in `run5b` |
| R2 | 0 | Did not fire |
| R4 | 0 demonstrated critical losses | Unsafe on silence set: 13/13 suppressions contained material semantic risk |
| Model / match variance | 1 | Outside post-model gate scope |

R2 zero-fire root cause: Run5 applied the editorial gate to `ai_kept` only. Of 34 Run5 clarity findings, 33 were mechanical long-paragraph / digit-mix findings and never reached R2, even though 29 explanations exactly matched the generic marker.

### Run5b live critical-recall result

| Run | critical_recall |
|-----|----------------:|
| gemini_run2 | 0.7368 |
| gemini_run5_editorial_gates | 0.6316 |
| **gemini_run5b_editorial_gates** | **0.4211** |
| Acceptance floor | ≥0.6868 |

Recovered relative to Run5:

- `case-0006` majority / numeric critical restored (`0 → 1`)

Still missing the two known Run5 R1 criticals:

- `case-0005` gold_index=1
- `case-0038` gold_index=0

Deterministic replay of the Run2 matched findings under `run5b` keeps both. Live Run5b engine outputs simply did not re-emit those `attribution_strength` findings; benchmark diagnostics show **zero** editorial-gate suppressions on the critical suite.

New losses vs Run5 (5 items) have no gate-suppressible baseline replay:

- 3 emitted but below match threshold / wrong span
- 2 model or pipeline non-emits (`case-0033`, `case-0035`)

Conclusion: the large live recall drop is dominated by Gemini emission / matching variance, not by a Run5b over-suppression bug. The policy still fails the hard recall gate on this frozen evaluation.

## 2. Exact code changes

Policy versions remain distinct:

- `off`: unchanged
- `run5`: frozen AI-only R1/R2/R4 behavior
- `run5b`: revised rules + mechanical+AI input scope + structured diagnostics

Key files:

- `app/postprocess/editorial_gate.py`
- `app/orchestration/review.py`
- `app/cli/run_benchmark.py`
- `app/config.py`
- `.env.example`
- `scripts/run_silence_eval.py`
- `scripts/replay_editorial_gates.py`
- `scripts/attribute_run5_recall_regression.py`
- `tests/test_editorial_gate.py`

### R1 (`run5b`)

- Keep vague-source / already-attributed suppression.
- Fail open for `attribution_strength` and certainty-escalation evidence.
- Require attribution cues **before** the cited span, not inside it.
- Do not broaden suppression.

### R2 (`run5b`)

- Apply after mechanical+AI merge.
- Suppress only demonstrated generic clarity / readability advice.
- Keep concrete referent, numeric/date, contradiction, entity/role/place, certainty, attribution, quotation, and meaning-changing suggestions.
- Arabic normalization used for matching only.

### R4 (`run5b`)

- Suppress only when positive safe-compression evidence exists and body support is present.
- Fail open on material semantic difference markers and structured changed content / numbers / dates / quotation meaning.

### Diagnostics

Every Run5b keep/suppress decision records:

- policy version
- rule ID
- decision
- reason code
- matched evidence

Silence eval writes `editorial_gate_diagnostics.jsonl`. Benchmark outputs now persist `editorial_gate_diagnostics` and `editorial_gate_rejected_findings`.

## 3. Test results

```powershell
$env:DEMO_AUTH_REQUIRED="false"; $env:AI_CLIENT="mock"; $env:USE_GCP="false"; $env:ADMIN_PASSWORD="admin"
python -m pytest tests/test_editorial_gate.py tests/test_punctuation_gate.py tests/test_editorial_label_scripts.py -q
python -m pytest -q --tb=short
```

- Focused gate suites: **56 passed** (later +1 frozen-run5 orchestrator regression: **35 passed** in `test_editorial_gate.py` alone)
- Full local-safe suite: **123 passed, 1 skipped**

Coverage includes:

- Run5 critical-loss keep paths
- R4 material mismatch keep paths
- Generic R2 suppressions and concrete R2 keeps
- Arabic normalization
- Numeric/date and punctuation preservation
- Distinct `off` / `run5` / `run5b` behavior
- Frozen `run5` mechanical-clarity bypass preserved
- Structured reason-code diagnostics

## 4. Frozen evaluation comparison

Commands:

```powershell
$env:PYTHONIOENCODING="utf-8"
$env:AI_CLIENT="gemini"; $env:USE_GCP="true"
$env:PUNCTUATION_POLICY="off"; $env:EDITORIAL_GATE_POLICY="run5b"
python scripts/run_silence_eval.py --dataset data/local/sprint2/silence_v1.jsonl --run-id gemini_run5b_editorial_gates
python -m benchmark_v2.public.run_engine --out benchmark_v2/results/engine_outputs_gemini_run5b_editorial_gates.json --run-id gemini_run5b_editorial_gates
python -m benchmark_v2.private.scorer.cli --gold-dir benchmark_v2/private/gold --outputs benchmark_v2/results/engine_outputs_gemini_run5b_editorial_gates.json --report benchmark_v2/results/report_gemini_run5b_editorial_gates.json
```

### Silence set (300 articles, punctuation off)

| Metric | run4 | run5 | **run5b** | Target |
|--------|-----:|-----:|----------:|-------:|
| Clean editorial FP | 0.4033 | 0.3133 | **0.3000** | ≤0.15 |
| Findings / article | 0.64 | 0.4967 | **0.4700** | ≤0.25 |
| Zero-finding rate | 0.5967 | 0.6867 | **0.7000** | ≥0.80 |

Category / family movement (run5 → run5b):

| Family | run5 | run5b | Notes |
|--------|-----:|------:|-------|
| Clarity | 34 | 5 | R2 now effective |
| Attribution | 26 | 31 | R1 not broadened |
| Headline mismatch | 14 | 23 | Safer R4 keeps material findings |

### Per-rule suppression counts (silence)

| Reason | run5 | run5b |
|--------|-----:|------:|
| `attribution_vague_or_already_attributed` | 17 | 18 |
| `clarity_generic_no_concrete_defect` | 0 | **28** |
| `headline_supported_compression` | 13 | **0** |

Representative correct suppressions: mechanical long-paragraph clarity (`مقطع طويل جداً قد يحتاج إعادة تقسيم.`) and ordinary vague-source attribution.  
Representative correct keeps: digit-mix clarity, concrete pronoun/referent clarity, and material headline contradictions that Run5 had suppressed.

### Critical recall

| Run | critical_recall | precision | recall | clean-case FP |
|-----|----------------:|----------:|-------:|--------------:|
| gemini_run2 | 0.7368 | 0.3929 | 0.7333 | 0.2308 |
| run5 | 0.6316 | 0.4318 | 0.6333 | 0.1538 |
| **run5b** | **0.4211** | **0.3721** | **0.5333** | **0.1538** |

Hard-gate delta vs Run2: **−31.6 pp** (fails `≥0.6868`).

## 5. Threshold verdict

| Gate | Result |
|------|--------|
| Critical recall ≥ 0.6868 | **FAIL** (`0.4211`) |
| Clean editorial FP ≤ 15% | FAIL (`30.0%`) |
| Findings/article ≤ 0.25 | FAIL (`0.47`) |
| Zero-finding rate ≥ 80% | FAIL (`70.0%`) |

Because critical recall failed, the release recommendation is **`needs_adjustment`**, not `proceed` and not the silence-only `needs_model_or_schema_change` path.

Important nuance for the next decision:

1. Run5b gate logic itself recovered the known R1 critical suppressions in deterministic replay and produced **no** editorial-gate suppressions on the live critical suite.
2. The live recall collapse is therefore not evidence that Run5b should broaden suppression further.
3. Silence improved only marginally after R2 started working; remaining FP mass is attribution / loaded framing / headline / entity / spelling. Further broad post-model keyword growth is the wrong next experiment.

## 6. Recommendation

**`needs_adjustment`**

Recommended next action for ChatGPT review:

1. Treat critical recall as still blocked on this frozen Run5b artifact.
2. Authorize a variance-controlled critical-benchmark re-run under the same frozen `run5b` policy before changing rules again, because current losses are dominated by non-emission / match variance.
3. If a controlled re-run clears the recall floor but silence remains above target, switch the next experiment to structured clarity / attribution subtypes or prompt/schema changes (`needs_model_or_schema_change`), not more post-model suppressions.

## 7. Confirmations

Frozen artifacts remained unchanged:

- `gemini_run3` report sha256 prefix `afe5363c7d14b753`
- `gemini_run4_no_punctuation` report sha256 prefix `88a3f60b0c01875e`
- `gemini_run5_editorial_gates` report sha256 prefix `33a8a2ba372bf3cc`

Also confirmed:

- original gold / expert-label files untouched
- prompts / model choice untouched
- numeric/date handling not suppressed
- punctuation-off preserved
- no auto-publish / auto-edit
- `run5` policy behavior preserved as a separate frozen path
- no commit, push, deploy, or GCP modification beyond the authorized evaluation calls
