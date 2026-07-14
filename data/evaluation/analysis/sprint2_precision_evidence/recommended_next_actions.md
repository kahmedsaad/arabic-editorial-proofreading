# Recommended next actions (evidence package)

Status:
- run4 no-punctuation ready: **False**
- human labels scored: **False**

Do **not** implement `gemini_run5_editorial_gates` until both are true.

- Wait for `gemini_run4_no_punctuation` to finish, then re-run this script.
- Label `data/local/sprint2/non_punctuation_priority_to_label.jsonl` (or the working copy).
- Score with `python scripts/score_editorial_labels.py`.
