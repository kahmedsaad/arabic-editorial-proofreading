# Recommended next actions (evidence package)

Status:
- run4 no-punctuation ready: **True**
- human labels scored: **True**

Do **not** implement `gemini_run5_editorial_gates` until both are true.


When both are ready, fill category rows from `human_label_summary.json`:

| Category | Labeled | Keep rate | Drop rate | Top drop reasons | Example FPs | Recommended action | Recall risk | Regression tests |
|----------|---------|-----------|-----------|------------------|-------------|--------------------|-------------|------------------|
| Attribution | … | … | … | … | … | Pending evidence | Check attribution recall | … |

Only then design targeted suppressions for high drop-rate categories.
