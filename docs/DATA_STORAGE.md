# Dataset storage (local + GCS)

**Principle:** Tiny safe samples in GitHub. Temporary datasets &lt;100 MB on the laptop. Shared, private, evaluation, or larger datasets in **GCS**. External Arabic news corpora are for silence/structure testing — **not** Al Jazeera house-style policy.

## Where data lives

| Location | When |
|----------|------|
| `data/samples/` (GitHub) | Tiny synthetic/anonymized samples for onboarding & unit tests |
| `data/local/` (gitignored) | Solo experiments &lt;100 MB |
| `gs://arabic-proofreading-data-ooredoo-499510/` | Shared / private / large / Cloud Run |

## Environment

```env
DATA_BACKEND=local          # or gcs
LOCAL_DATA_DIR=./data/local
GCP_PROJECT_ID=ooredoo-499510
GCS_DATA_BUCKET=arabic-proofreading-data-ooredoo-499510
GCS_DATA_PREFIX=
DATA_CACHE_DIR=./data/cache
DATA_CACHE_ENABLED=true
```

Local mode and unit tests **must not** require GCP credentials.

## Create the bucket (once)

```bash
gcloud config set project ooredoo-499510

gcloud storage buckets create \
  gs://arabic-proofreading-data-ooredoo-499510 \
  --project=ooredoo-499510 \
  --location=us-central1 \
  --uniform-bucket-level-access

gcloud storage buckets update \
  gs://arabic-proofreading-data-ooredoo-499510 \
  --versioning
```

Do **not** make the bucket public.

### Prefix layout

```
gs://arabic-proofreading-data-ooredoo-499510/
  public/clean|synthetic|samples/
  private/tuning|editor_feedback|before_after/
  benchmarks/public|private/
  derived/...
  manifests/
```

Keep `private/` and `benchmarks/private/` restricted.

### IAM (least privilege)

| Who | Role |
|-----|------|
| Developers uploading | `roles/storage.objectUser` |
| Read-only eval | `roles/storage.objectViewer` |
| Cloud Run SA | `roles/storage.objectViewer` (not `storage.admin`) |

## Upload / download

```powershell
# GCS (PowerShell)
.\scripts\upload_dataset_gcp.ps1 `
  -Source ".\data\samples\sample_clean_articles.jsonl" `
  -Destination "public/samples/sample_clean_articles.jsonl" `
  -DatasetId "sample_clean_articles" `
  -Yes -Overwrite

.\scripts\download_dataset_gcp.ps1 `
  -Source "public/samples/sample_clean_articles.jsonl" `
  -Destination ".\data\downloads\sample_clean_articles.jsonl" `
  -Overwrite
```

```bash
# Cross-platform
python scripts/upload_dataset.py \
  --source ./data/samples/sample_clean_articles.jsonl \
  --destination public/samples/sample_clean_articles.jsonl \
  --dataset-id sample_clean_articles \
  --source-type synthetic \
  --license internal-demo \
  --backend gcs --yes --overwrite

python scripts/download_dataset.py \
  --source public/samples/sample_clean_articles.jsonl \
  --destination ./data/downloads/sample_clean_articles.jsonl \
  --backend gcs --overwrite
```

Install GCS client: `pip install -e ".[gcs]"`.

For the Python GCS client (upload/download scripts), also set Application Default Credentials once:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project ooredoo-499510
```

Until ADC is set, you can still move files with `gcloud storage cp` (uses your gcloud user login).

## Evaluate

```bash
# Local sample / golden
python -m app.cli.evaluate --dataset ./data/samples/sample_clean_articles.jsonl

# GCS
python -m app.cli.evaluate \
  --dataset gs://arabic-proofreading-data-ooredoo-499510/public/samples/sample_clean_articles.jsonl
```

## Legal / safety

- Do not claim external SANAD/ANAD/etc. data is Al Jazeera policy
- Do not scrape AJ at scale without permission; prefer a small approved pack
- Do not commit private gold, secrets, or full copyrighted corpora to GitHub
- Synthetic / AI-drafted labels ≠ editor-approved until reviewed
- Upload CLI refuses secrets and private gold under `public/`

## Do we need model training?

**Not for the POC.** Use data for: silence eval, synthetic gold, prompt contrastives, threshold calibration, editor keep/drop. Fine-tune only after thousands of consistent reviewed findings.
