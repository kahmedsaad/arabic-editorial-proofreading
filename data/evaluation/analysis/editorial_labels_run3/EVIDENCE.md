# Editorial labels evidence (run3 non-punctuation)

**Facts measured from labels** (not hypotheses).

| Metric | Value |
|--------|------:|
| Total rows | 163 |
| Labeled | 163 |
| Blank | 0 |
| keep | 23 |
| drop | 128 |
| uncertain | 12 |
| Precision `keep/(keep+drop)` | **0.1523** (15.2%) |
| Near-duplicate groups (same article + span prefix + category) | 14 |

Source: `data/local/sprint2/non_punctuation_priority_to_label.jsonl` (same 163 IDs as working/src copies).  
Artifact: `expert_labels.jsonl` + scorer input `labeled_for_scoring.jsonl`.  
Scorer: `summary.json`, CSVs in this folder.

## Precision by category (uncertain excluded)

| Category | n | keep | drop | unc | precision |
|----------|--:|-----:|-----:|----:|----------:|
| Attribution | 40 | 0 | 40 | 0 | 0.00 |
| Clarity | 34 | 0 | 34 | 0 | 0.00 |
| Headline mismatch | 23 | 10 | 12 | 1 | 0.45 |
| Entity consistency | 17 | 0 | 15 | 2 | 0.00 |
| Loaded framing | 14 | 0 | 14 | 0 | 0.00 |
| Numeric consistency | 14 | 5 | 0 | 9 | 1.00 |
| spelling | 13 | 3 | 10 | 0 | 0.23 |
| unsupported_certainty | 3 | 1 | 2 | 0 | 0.33 |
| repetition | 3 | 2 | 1 | 0 | 0.67 |
| consistency | 1 | 1 | 0 | 0 | 1.00 |
| grammar | 1 | 1 | 0 | 0 | 1.00 |

## Drop reasons

too_low_impact 53 · optional_style 37 · acceptable_arabic 15 · headline_compression 14 · incorrect_rule 9

## Representative FP samples

See `top_false_positive_examples.jsonl` (attribution / clarity / entity / loaded framing / spelling / headline compression).

## Hypotheses for gates (now implemented as opt-in run5)

See `run5_gate_recommendations.md` and `run5_implemented_gate_spec.md`.  
Gate code is opt-in via `EDITORIAL_GATE_POLICY=run5` (default remains off).

## Calibration and decision review

- `calibration_packet.md` — deterministic 30-item packet for human calibration (reviewer fields blank)
- `label_consistency_audit.md` — internal audit of all 163 AI labels
- `proposed_label_corrections.jsonl` — proposed changes; does not alter original labels
- `gate_decision_brief.md` — narrowed R1 → R2 → R4 recommendation; R3/R5 deferred
- `correction_adjudications.jsonl` + `FINAL_ADJUDICATION_EVIDENCE.md` — final AI-expert adjudication
- `final_adjudicated_for_scoring.jsonl` — derived scoring input (precision **0.1208**)
- `run5_implementation_and_validation_report.md` — implementation + validation report
