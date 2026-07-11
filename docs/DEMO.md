# POC Demo

## Quick demo (no server)

```bash
pip install -e ".[dev]"
python scripts/demo_poc.py
```

Runs in-process: health → parse → review → debug → evaluation.

## Against a running API

```bash
uvicorn app.main:app --reload --port 8000
python scripts/demo_poc.py --base-url http://localhost:8000
```

## Live Gemini

1. `pip install -e ".[gemini]"`
2. Copy `.env.example` → `.env`
3. Set:
   - `AI_CLIENT=gemini`
   - `GEMINI_API_KEY=...`
4. Re-run `python scripts/demo_poc.py`

Optional live test:

```bash
# Windows PowerShell
$env:RUN_GEMINI_LIVE=1
pytest tests/test_gemini_optional.py -q
```

## Evaluate golden set

```bash
python -m app.cli.evaluate --dataset data/evaluation/golden.jsonl
```

### AI editorial validation (Compass goldens)

```bash
# mock scorecard (no API key)
python scripts/validate_ai.py

# also Gemini
python scripts/validate_ai.py --with-gemini
```

Writes `data/evaluation/ai_scorecard.json`.  
POC pass: span recall ≥ 0.6 and quote-preserve rate ≥ 0.5.

Current golden set: controlled fixtures + pair-derived mechanical expectations (~15 records).
Editorial set: `data/evaluation/golden_editorial.jsonl` (6 Compass labels).

## Upload DOCX/TXT

```bash
curl -F "file=@article.docx" http://localhost:8000/api/v1/documents/upload
```

## Still optional for POC

- Phase 7 GCP hosting (`docs/PHASE7_START.md`)
- Hand-label editorial categories on pair diffs (beyond mechanical)
- Frontend wiring to editor-compass
