# Sprint 2 precision evidence (assemble after run4 + human labels)

This folder holds the evidence package for deciding `gemini_run5_editorial_gates`.

## Required inputs

1. Completed `data/evaluation/runs/gemini_run4_no_punctuation/`
2. Completed human labels in `data/local/sprint2/non_punctuation_to_label.jsonl`

## Assemble

```powershell
python scripts/build_sprint2_evidence_package.py
```

Until both inputs exist, the package remains partial — do **not** implement editorial gates.

## Files (when complete)

| File | Source |
|------|--------|
| `run4_baseline_summary.json` | run4 report + split metrics |
| `run3_vs_run4_summary.json` | compare_evaluation_runs |
| `human_label_summary.json` | score_editorial_labels |
| `category_precision.csv` | label scores |
| `drop_reasons.csv` | label scores |
| `top_false_positive_examples.jsonl` | labeled drops |
| `recommended_next_actions.md` | evidence-based, no implementation |
