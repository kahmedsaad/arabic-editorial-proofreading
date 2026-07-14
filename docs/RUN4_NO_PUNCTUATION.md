# Run4 baseline: punctuation off

Compare clean-set FP rates with the **same** frozen silence dataset as run3, changing only punctuation policy.

## Prerequisites

- Same articles: `data/local/sprint2/silence_v1.jsonl` (the run3 clean set)
- Same model: `GEMINI_MODEL=gemini-2.5-flash` (or whatever run3 used)
- Gemini credentials as in `.env` (`AI_CLIENT=gemini`, `USE_GCP=true`)

## Command (no punctuation findings)

PowerShell:

```powershell
$env:PYTHONIOENCODING="utf-8"
$env:AI_CLIENT="gemini"
$env:USE_GCP="true"
$env:PUNCTUATION_POLICY="off"
python scripts/run_silence_eval.py `
  --dataset data/local/sprint2/silence_v1.jsonl `
  --run-id gemini_run4_no_punctuation
```

bash:

```bash
PYTHONIOENCODING=utf-8 \
AI_CLIENT=gemini \
USE_GCP=true \
PUNCTUATION_POLICY=off \
python scripts/run_silence_eval.py \
  --dataset data/local/sprint2/silence_v1.jsonl \
  --run-id gemini_run4_no_punctuation
```

Outputs: `data/evaluation/runs/gemini_run4_no_punctuation/`

## Follow-up (strict mode)

```powershell
$env:PUNCTUATION_POLICY="strict"
python scripts/run_silence_eval.py --dataset data/local/sprint2/silence_v1.jsonl --run-id gemini_run4_strict
```

## What must stay fixed vs run3

| Fixed | Changed |
|-------|---------|
| Article set (`silence_v1.jsonl`) | `PUNCTUATION_POLICY` |
| Model / Vertex project | (none) |
| Eval script metrics (legacy keys preserved + split metrics) | Punctuation gate |

Do **not** overwrite `data/evaluation/runs/gemini_run3/`.

## After this baseline

1. Label the 163 editorial findings — see [EDITORIAL_LABELING.md](EDITORIAL_LABELING.md)
2. Score: `python scripts/score_editorial_labels.py --input <labeled.jsonl>`
3. Next gated run name: **`gemini_run5_editorial_gates`** (do not reuse run4)
