# Editorial labeling (run3 → run5 path)

## Order (do not skip)

1. `gemini_run3` — frozen (immutable)
2. Punctuation analysis — done
3. **`gemini_run4_no_punctuation`** — diagnostic baseline (punctuation off only)
4. **Label 163** non-punctuation findings — **done** (separate artifact)
5. Category suppressions (attribution / clarity / headline) — **implemented** as opt-in `EDITORIAL_GATE_POLICY=run5`
6. **`gemini_run5_editorial_gates`** — gated editorial silence run (R1/R2/R4 only)
7. Issue-containing benchmark (critical recall check)

Allowed decisions: `keep` | `drop` | `uncertain`

## Canonical source (do not overwrite with labels)

Priority-sorted template (same 163 IDs as the working copy):

```text
data/local/sprint2/non_punctuation_priority_to_label.jsonl
```

Working copy (identical ID set; leave as unlabeled template unless you deliberately edit it):

```text
data/local/sprint2/non_punctuation_to_label.jsonl
```

Also mirrored at:

```text
data/evaluation/analysis/gemini_run3_precision/non_punctuation_todo.jsonl
```

## Separate label artifact (use this)

```text
data/evaluation/analysis/editorial_labels_run3/expert_labels.jsonl
data/evaluation/analysis/editorial_labels_run3/labeled_for_scoring.jsonl
```

Regenerate labels (expert heuristic pass; does **not** touch run3 or source templates):

```powershell
python scripts/apply_expert_editorial_labels.py
```

Validate:

```powershell
python scripts/validate_editorial_label_file.py --input data/evaluation/analysis/editorial_labels_run3/labeled_for_scoring.jsonl
```

Score:

```powershell
python scripts/score_editorial_labels.py --input data/evaluation/analysis/editorial_labels_run3/labeled_for_scoring.jsonl --out-dir data/evaluation/analysis/editorial_labels_run3
```

**Precision formula:** `keep / (keep + drop)` — `uncertain` excluded from the denominator.

Evidence + gate recommendations (recommendations only):

```text
data/evaluation/analysis/editorial_labels_run3/EVIDENCE.md
data/evaluation/analysis/editorial_labels_run3/run5_gate_recommendations.md
data/evaluation/analysis/editorial_labels_run3/summary.json
```

Calibration / consistency review (labels unchanged):

```powershell
python scripts/build_editorial_calibration_packet.py
python scripts/audit_editorial_labels_consistency.py
```

```text
data/evaluation/analysis/editorial_labels_run3/calibration_packet.md
data/evaluation/analysis/editorial_labels_run3/label_consistency_audit.md
data/evaluation/analysis/editorial_labels_run3/proposed_label_corrections.jsonl
data/evaluation/analysis/editorial_labels_run3/gate_decision_brief.md
```

Adjudication + derived final labels (does **not** overwrite `expert_labels.jsonl`):

```powershell
python scripts/adjudicate_editorial_corrections.py
python scripts/validate_editorial_label_file.py --input data/evaluation/analysis/editorial_labels_run3/final_adjudicated_for_scoring.jsonl
python scripts/score_editorial_labels.py --input data/evaluation/analysis/editorial_labels_run3/final_adjudicated_for_scoring.jsonl --out-dir data/evaluation/analysis/editorial_labels_run3/final_adjudicated
```

```text
data/evaluation/analysis/editorial_labels_run3/correction_adjudications.jsonl
data/evaluation/analysis/editorial_labels_run3/final_adjudicated_for_scoring.jsonl
data/evaluation/analysis/editorial_labels_run3/FINAL_ADJUDICATION_EVIDENCE.md
data/evaluation/analysis/editorial_labels_run3/run5_implemented_gate_spec.md
data/evaluation/analysis/editorial_labels_run3/run5_implementation_and_validation_report.md
```

## No-punctuation baseline

See [RUN4_NO_PUNCTUATION.md](RUN4_NO_PUNCTUATION.md). Expect clean FP near ~35% editorial-only; almost no punctuation findings.

## Run5 editorial gates

Opt-in policy `EDITORIAL_GATE_POLICY=run5` enables only R1/R2/R4 after model parse and before editor exposure. Default remains `off`.

```powershell
$env:PYTHONIOENCODING="utf-8"
$env:AI_CLIENT="gemini"
$env:USE_GCP="true"
$env:PUNCTUATION_POLICY="off"
$env:EDITORIAL_GATE_POLICY="run5"
python scripts/run_silence_eval.py `
  --dataset data/local/sprint2/silence_v1.jsonl `
  --run-id gemini_run5_editorial_gates
```

Critical-recall check (public cases only; hidden gold unchanged):

```powershell
$env:AI_CLIENT="gemini"
$env:USE_GCP="true"
$env:PUNCTUATION_POLICY="off"
$env:EDITORIAL_GATE_POLICY="run5"
python -m benchmark_v2.public.run_engine `
  --out benchmark_v2/results/engine_outputs_gemini_run5_editorial_gates.json `
  --run-id gemini_run5_editorial_gates
python -m benchmark_v2.private.scorer.cli `
  --gold-dir benchmark_v2/private/gold `
  --outputs benchmark_v2/results/engine_outputs_gemini_run5_editorial_gates.json `
  --report benchmark_v2/results/report_gemini_run5_editorial_gates.json
```

Targets:

| Metric | Target |
|--------|--------|
| Clean editorial FP rate | ≤15% |
| Findings per clean article | ≤0.25 |
| Zero-finding clean articles | ≥80% |
| Attribution / clarity / headline FP reduction | ≥50–60% |

Always re-check critical recall on the issue-containing benchmark after suppressions.

## Run5b editorial gates

Separate opt-in policy `EDITORIAL_GATE_POLICY=run5b` revises R1/R2/R4 without changing frozen `run5`. Default remains `off`.

```powershell
$env:PYTHONIOENCODING="utf-8"
$env:AI_CLIENT="gemini"
$env:USE_GCP="true"
$env:PUNCTUATION_POLICY="off"
$env:EDITORIAL_GATE_POLICY="run5b"
python scripts/run_silence_eval.py `
  --dataset data/local/sprint2/silence_v1.jsonl `
  --run-id gemini_run5b_editorial_gates
```

Critical-recall check:

```powershell
$env:AI_CLIENT="gemini"
$env:USE_GCP="true"
$env:PUNCTUATION_POLICY="off"
$env:EDITORIAL_GATE_POLICY="run5b"
python -m benchmark_v2.public.run_engine `
  --out benchmark_v2/results/engine_outputs_gemini_run5b_editorial_gates.json `
  --run-id gemini_run5b_editorial_gates
python -m benchmark_v2.private.scorer.cli `
  --gold-dir benchmark_v2/private/gold `
  --outputs benchmark_v2/results/engine_outputs_gemini_run5b_editorial_gates.json `
  --report benchmark_v2/results/report_gemini_run5b_editorial_gates.json
```

Evidence:

```text
data/evaluation/analysis/editorial_labels_run3/run5b_gate_diagnostics.md
data/evaluation/analysis/editorial_labels_run3/run5b_implementation_and_validation_report.md
```
