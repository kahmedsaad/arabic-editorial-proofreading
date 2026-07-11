# Arabic Editorial Proofreading Engine

Prototype backend for Arabic editorial proofreading and review.

**Principle:** AI suggests. Editors decide.

## Status

Phases **1–6 complete**. Phase **7 (GCP) not started** — stubs + env only.

| Phase | Status |
|-------|--------|
| 1 Initial engine + mock AI | done |
| 2 BEFORE/AFTER importer | done |
| 3 Mechanical/entity enrichment + parse | done |
| 4 Gemini client (optional) | done |
| 5 Evaluation CLI | done |
| 6 Full API + SQLite | done |
| 7 GCP adapters / Cloud Run | **next** |

## Requirements

- Python 3.11+ (3.12 recommended)
- Docker optional

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
# optional Gemini SDK
pip install -e ".[gemini]"
```

Copy `.env.example` to `.env` if needed. Keep `AI_CLIENT=mock` for local/CI.

## Run API

```bash
uvicorn app.main:app --reload --port 8000
```

### Make the UI real (wired to MVP)

**Status: wired.** Live Mode calls `POST /api/v1/reviews` and replaces seed cards with engine findings (`FND-M-*`, `FND-AI-ED-*`).

1. Start API (port **8001** if 8000 is busy):
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

2. Start UI:
```bash
cd frontend
npm run dev -- --port 5173 --host 127.0.0.1
```

3. In the UI:
   - Open **الإعدادات** → API Base URL `http://127.0.0.1:8001`
   - Click **Live / MVP Engine** + **Use MVP Engine**
   - Click **اختبار الاتصال** (health JSON)
   - Open article → **تشغيل المحرك (MVP Live)**

Optional Gemini on the **server** (not in the browser):
```env
AI_CLIENT=gemini
GEMINI_API_KEY=...
```

GCP is optional for this local real loop.

### Endpoints

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/health` | Liveness |
| POST | `/api/v1/documents/parse` | Parse text → segments |
| POST | `/api/v1/documents/upload` | Upload TXT/HTML/DOCX → segments |
| POST | `/api/v1/reviews` | Full review (persisted) |
| GET | `/api/v1/reviews/{id}` | Editor view |
| GET | `/api/v1/reviews/{id}/debug` | Includes rejected findings |
| GET/POST | `/api/v1/rules` | List / upsert rules |
| GET | `/api/v1/rules/{id}` | Rule detail |
| GET/POST | `/api/v1/entities` | List / upsert entities |
| POST | `/api/v1/evaluations/run` | Run golden evaluation |

## CLI

```bash
# Import pairs (directory or zip). Does not modify originals.
python -m app.cli.import_pairs --source data/pairs --output data/imported/pairs.jsonl

# Evaluate against golden set
python -m app.cli.evaluate --dataset data/evaluation/golden.jsonl
```

## Tests and lint

```bash
pytest
ruff check .
# optional live Gemini
set RUN_GEMINI_LIVE=1
pytest tests/test_gemini_optional.py -q
```

## Docker

```bash
docker build -t arabic-proofreading .
docker run --rm -p 8000:8000 arabic-proofreading
```

## Phase 7 start (not implemented)

Env flags are ready in `.env.example`:

- `USE_GCP=false`
- `GCP_PROJECT_ID`, `GCP_LOCATION`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `STORAGE_BUCKET`
- `AI_CLIENT=mock|gemini`

Package `app/gcp` contains stubs that raise until Phase 7 is built. See `prompts/04_GCP_DEPLOYMENT_PROMPT.txt`.

## Project layout

```
app/
  api/             # HTTP layer
  ai/              # mock + Gemini clients
  cli/             # import_pairs, evaluate
  dataset/         # pair importer
  entities/        # entity repository + matcher
  evaluation/      # metrics
  mechanical/      # deterministic checks
  models/          # Pydantic schemas
  normalization/   # Arabic normalize
  orchestration/   # review pipeline
  parsing/         # document parse
  persistence/     # SQLite review store
  rules/           # JSON rules
  segmentation/    # segments
  validation/      # finding validator
  gcp/             # Phase 7 stubs only
data/
  pairs/           # raw BEFORE/AFTER
  imported/        # JSONL output
  evaluation/      # golden.jsonl
  rules/ entities/ spelling/ fixtures/
prompts/           # staged Cursor prompts + gemini/v1
```
