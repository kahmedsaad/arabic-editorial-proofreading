# Sprint 2 — Silence subsample, FP labels, contrastives, run3 freeze

**Goal:** raise editor trust (precision) using clean public corpora + human keep/drop labels.  
Public corpora are **not** Al Jazeera house style.

## Targets (unchanged)

| Metric | Target |
|--------|--------|
| Overall precision | ≥55% |
| Critical-category recall | ≥80% |
| Clean-article FP rate | ≤10% |
| Quotation preservation | ≥98% |

## Steps

### 1. Build silence subsample (200–500)

```powershell
python scripts/sample_silence_set.py --n 300 --seed 20260714
```

Writes:

- `data/local/sprint2/silence_v1.jsonl` — full local sample (gitignored)
- `data/evaluation/sprint2/silence_seed.jsonl` — tiny smoke slice (tracked)

Stratifies by corpus × length × risk tags (`has_quote`, `has_attribution`, `has_masadir`, `headline_attribution`, `plain`).

### 2. Freeze Gemini run3 on silence set

Requires Vertex/Gemini credentials (or mock client for smoke).

```powershell
# full local sample
python scripts/run_silence_eval.py --run-id gemini_run3

# smoke on seed slice
python scripts/run_silence_eval.py --dataset data/evaluation/sprint2/silence_seed.jsonl --run-id smoke_silence
```

Outputs under `data/evaluation/runs/<run-id>/`:

| File | Purpose |
|------|---------|
| `report.json` | clean FP rate, findings/article, FP by family |
| `articles.jsonl` | per-article finding counts |
| `fp_labels_todo.jsonl` | rows for editor keep/drop |

Compare `clean_article_fp_rate` to run2 (~0.23 baseline) and target ≤0.10.

### 3. Label keep / drop

Open `fp_labels_todo.jsonl`. For each finding set:

- `annotator_decision`: `keep` | `drop` | `modify`
- `drop_reason`: short code (`headline_ok_with_body`, `named_source`, `quote_must_preserve`, …)
- `notes`: optional

Focus FP families first: **attribution**, **headline compression**, **quote_voice**, **vague مصادر**.

Schema example: `data/evaluation/sprint2/fp_labels_template.jsonl`.

### 4. Contrastives (prompt / gate regression)

`data/evaluation/sprint2/contrastives_v1.jsonl` — paired SHOW vs SILENCE cases for the four FP families.

Extend with real editor examples after labeling; keep synthetic mutations marked `source_type=synthetic_contrastive`.

### 5. After labels

Use drop-heavy patterns to tighten adjudicator / category thresholds (Sprint 1 levers). Re-freeze as `gemini_run3b` only after changes; never overwrite frozen `report.json` in place — copy to a new run-id.

## Out of scope this sprint

- Fine-tuning
- Al Jazeera scraping
- Phase 7 production adapters
