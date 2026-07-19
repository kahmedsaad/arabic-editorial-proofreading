# Final AI-expert adjudication evidence

This is the final AI-expert adjudication artifact for the 17 proposed corrections.
Original `expert_labels.jsonl` and `proposed_label_corrections.jsonl` were **not** overwritten.

## Adjudication totals

| Outcome | Count |
|---------|------:|
| accept | 13 |
| reject | 0 |
| uncertain | 4 |

Accepted proposals update only the derived files:

- `correction_adjudications.jsonl`
- `final_adjudicated_labels.jsonl`
- `final_adjudicated_for_scoring.jsonl`
- `final_adjudicated/` scorer outputs

## Before / after label metrics

| Metric | Original expert labels | Final adjudicated |
|--------|-----------------------:|------------------:|
| keep | 23 | 18 |
| drop | 128 | 131 |
| uncertain | 12 | 14 |
| Precision `keep/(keep+drop)` | 0.1523 | **0.1208** |

Category precision after adjudication (uncertain excluded):

| Category | Precision |
|----------|----------:|
| Attribution | 0.00 |
| Clarity | 0.00 |
| Headline mismatch | 0.35 |
| Entity consistency | 0.00 |
| Loaded framing | 0.00 |
| Numeric consistency | 0.60 |
| spelling | 0.23 |
| unsupported_certainty | 0.33 |
| repetition | 0.67 |
| consistency | 1.00 |
| grammar | 1.00 |

## Accepted corrections

Rationale-only (decision unchanged as `drop`): source_index `117, 118, 119, 120, 121, 123, 126, 127`.

Decision changes:

| source_index | From → To | Why accepted |
|-------------:|-----------|--------------|
| 40 | keep → drop | Invite-gated availability is misread as a material contradiction |
| 128 | keep → drop | Remaining wins vs achieved streak are different quantities |
| 129 | keep → drop | Same numeric ambiguity as 128 |
| 47 | keep → uncertain | Cited denial absent from supplied excerpt |
| 49 | keep → uncertain | Cited deportation-stop claim absent from supplied excerpt |

## Uncertain adjudications (original label retained)

| source_index | Why uncertain |
|-------------:|---------------|
| 50 | Cited span absent from excerpt; may exist in truncated article |
| 59 | Europe/world aggregates do not prove a country ranking contradiction |
| 60 | Alleged earlier exceptions not present in supplied excerpt |
| 104 | Publisher-voice load requires house-style policy not available here |

## Commands

```powershell
python scripts/adjudicate_editorial_corrections.py
python scripts/validate_editorial_label_file.py --input data/evaluation/analysis/editorial_labels_run3/final_adjudicated_for_scoring.jsonl
python scripts/score_editorial_labels.py --input data/evaluation/analysis/editorial_labels_run3/final_adjudicated_for_scoring.jsonl --out-dir data/evaluation/analysis/editorial_labels_run3/final_adjudicated
```
