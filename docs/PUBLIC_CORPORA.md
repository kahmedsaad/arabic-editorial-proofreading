# Public Arabic news corpora (licensed) — not Al Jazeera house style

## Policy

| Allowed | Not allowed (without written AJ permission) |
|---------|-----------------------------------------------|
| SANAD (CC BY 4.0) — AlKhaleej, AlArabiya, Akhbarona | Scraping aljazeera.net / aljazeera.com at scale |
| ANAD (CC BY 4.0) — multi-site 2021 news | Proxy rotation / ban-evasion scrapers for AJ |
| Other **licensed** public corpora you verify | Claiming public corpora are AJ editorial policy |

Al Jazeera articles for demos: use a **small approved pack** from AJ, or live view without redistributing a corpus.

## Pull SANAD (full or capped)

```powershell
pip install datasets pyarrow
python scripts/pull_public_corpora.py --corpus sanad --upload-gcs
# smoke:
python scripts/pull_public_corpora.py --corpus sanad --max-records 2000
```

Output: `data/local/public_corpora/sanad_clean_v1.jsonl`  
GCS: `gs://arabic-proofreading-data-ooredoo-499510/public/clean/sanad_clean_v1/`

On Windows, prefer zip over git clone (paths with `:` fail checkout):

```powershell
# download zip then convert (reads zip in-memory; skips Al Jazeera paths)
Invoke-WebRequest -Uri "https://github.com/alaybaa/ArabicArticlesDataset/archive/refs/heads/main.zip" -OutFile data\local\anad_main.zip
python scripts/pull_public_corpora.py --corpus anad --anad-zip data/local/anad_main.zip --upload-gcs
```

## Why no AJ proxy scraper

Project rule + AJ site terms: mass collection/redistribution needs clearance. Proxies to bypass limits are not something we implement. If AJ authorizes a pack, store it under `gs://…/private/` with a manifest — no scraper required.

## Use of public data

Silence eval, structure, entities, FP hunting — **subsample** for daily benchmarks; keep full dumps in GCS.

Sprint 2 workflow (silence sample → FP labels → contrastives → `gemini_run3`): see [SPRINT2.md](SPRINT2.md).

Punctuation noise dominated run3 — analysis + run4 policy: [RUN3_PUNCTUATION_ANALYSIS.md](RUN3_PUNCTUATION_ANALYSIS.md), [RUN4_NO_PUNCTUATION.md](RUN4_NO_PUNCTUATION.md).
