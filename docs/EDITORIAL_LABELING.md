# Editorial labeling (run3 → run5 path)

## Order (do not skip)

1. `gemini_run3` — frozen (immutable)
2. Punctuation analysis — done
3. **`gemini_run4_no_punctuation`** — diagnostic baseline (punctuation off only)
4. **Label 163** non-punctuation findings
5. Category suppressions (attribution / clarity / headline)
6. **`gemini_run5_editorial_gates`** — next gated editorial run
7. Issue-containing benchmark (critical recall check)

Allowed decisions: `keep` | `drop` | `uncertain`

Priority sorted copy (label this):

```text
data/local/sprint2/non_punctuation_priority_to_label.jsonl
```

Working copy:

```text
data/local/sprint2/non_punctuation_to_label.jsonl
```

Validate:

```powershell
python scripts/validate_editorial_label_file.py --input data/local/sprint2/non_punctuation_to_label.jsonl
```

Score:

```powershell
python scripts/score_editorial_labels.py --input data/local/sprint2/non_punctuation_to_label.jsonl
```

**Precision formula:** `keep / (keep + drop)` — `uncertain` excluded from the denominator.

Outputs: `data/evaluation/analysis/editorial_labels_run3/`


## No-punctuation baseline

See [RUN4_NO_PUNCTUATION.md](RUN4_NO_PUNCTUATION.md). Expect clean FP near ~35% editorial-only; almost no punctuation findings.

## Next engineering run (after labels)

Name it `gemini_run5_editorial_gates` — do **not** reuse `run4`.

Targets:

| Metric | Target |
|--------|--------|
| Clean editorial FP rate | ≤15% |
| Findings per clean article | ≤0.25 |
| Zero-finding clean articles | ≥80% |
| Attribution / clarity / headline FP reduction | ≥50–60% |

Always re-check critical recall on the issue-containing benchmark after suppressions.
