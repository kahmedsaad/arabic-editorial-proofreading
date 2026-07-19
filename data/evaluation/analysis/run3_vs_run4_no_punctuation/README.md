# Run comparison

- Baseline: `data\evaluation\runs\gemini_run3`
- Candidate: `data\evaluation\runs\gemini_run4_no_punctuation`

## Headline

| Metric | Baseline | Candidate | Delta |
|--------|----------|-----------|-------|
| Clean FP rate | 0.77 | 0.4033 | 0.3667 |
| Total findings | 595 | 192 | 403 |
| Punctuation findings | 432 | 0 | 432 |
| Zero-finding rate | 0.23 | 0.5967 | 0.3667 |

## Caution

Clean-set FP reduction from disabling punctuation does not equal editorial precision improvement. Human keep/drop labels are required before claiming editorial precision gains.

Articles with editorial finding-count changes (unexpected if only punctuation policy changed): **77**
