# Wire Editorial Compass UI ↔ Proofreading MVP

Frontend lives in [`frontend/`](../frontend/) (Editorial Compass).  
Backend MVP lives in [`app/`](../app/) (FastAPI).

Dev UI (running): `http://127.0.0.1:5173/`  
API: `http://127.0.0.1:8000/api/v1`

## What the UI is today

From browser inspection + code:

| Area | Behavior now |
|------|----------------|
| Home | Demo/Live toggle; lists seed articles |
| Review | Locked article text + suggestion cards (accept/edit/reject) |
| Phases / Graph / Semantic / LLM packet / Validator / Eval / Preview | Pipeline views around seed + optional OpenAI-compatible Live calls |
| Rules / Entities / Lexical / Golden / Audit | Seed repositories (local) |
| Settings | Live LLM `baseUrl` + `apiKey` + `model` (OpenAI-compatible) |
| Data | `localStorage` store — **not** our FastAPI |

Live Mode currently calls OpenAI-style `/chat/completions` via `src/lib/llm.functions.ts`, **not** our engine.

## Target wiring (MVP)

```
UI (Demo Mode)  → seed suggestions (keep for offline demo)
UI (Live Mode)  → POST http://localhost:8000/api/v1/reviews
                ← map ReviewResponse.findings → Suggestion[]
UI Rules/Entities → GET/POST /api/v1/rules|entities (optional phase 2)
UI Evaluation   → POST /api/v1/evaluations/run (optional)
```

Principle stays: **AI suggests, editors decide**. Accept only updates preview, never original text.

## 1. Field mapping (critical)

### Article → ReviewRequest

| UI `Article` | MVP |
|--------------|-----|
| `sections[surface=headline].text` | `headline` |
| join `lead` + `paragraph` texts | `body` |
| `article_id` | `document_id` |
| captions/metadata | `metadata` (or extra body segments later) |

MVP today segments **headline + body paragraphs** only. Captions/metadata should go in `metadata` or be concatenated into body with markers until zones are expanded.

### Finding → Suggestion

| MVP `Finding` | UI `Suggestion` |
|---------------|-----------------|
| `finding_id` | `suggestion_id` |
| `source` (`mechanical`/`mock`/`gemini`) | `phase` (e.g. `mechanical` / `llm_response`) |
| `category` | `type` (map: spelling→spelling, entity_name→entity_name, attribution*→relational, punctuation→punctuation, …) |
| `decision` | `severity` (align enums; add `acceptable_with_note` on MVP or map → `soft_warning` + note) |
| `original_text` | `anchor.original_text` |
| `start_offset`/`end_offset` | `anchor.start_char`/`end_char` (**section-local** — need `segment_id` → `section_id`) |
| `segment_id` | `anchor.section_id` (map `SEG-001`↔`headline`, body paras↔`lead`/`pN`) |
| `suggested_text` | `suggested_text` |
| `explanation_ar` | `reason` |
| `rule_ids` | `rule_ids` |
| `validation_status=valid` | `validator_status=passed` |
| rejected findings | omit from editor list (or show under Validator tab via `/reviews/{id}/debug`) |
| — | `status=pending_human_review` |
| `requires_editor_review` | `requires_editor_approval` |

Add a small adapter module in the frontend:

`frontend/src/lib/api/mvp.ts` → `reviewArticle()` + `findingsToSuggestions()`.

## 2. Minimal code changes (recommended order)

### A. Frontend API client (1–2 hours)

1. Add `VITE_API_BASE_URL=http://127.0.0.1:8000` in `frontend/.env`.
2. Create `src/lib/api/client.ts` with `fetch` helpers.
3. Implement:
   - `createReview(article) → ReviewResponse`
   - `getReview(id)`, `getReviewDebug(id)`
   - optional: `listRules()`, `listEntities()`

### B. Replace Live pipeline entry (core)

In `src/lib/pipeline/orchestrator.ts`:

- **Demo Mode:** keep current seed path.
- **Live Mode:** instead of multi-phase OpenAI loops, call **one** `POST /api/v1/reviews`, then set store suggestions via mapped findings.

Button label can stay “تشغيل المراحل (Live)” but it runs the MVP engine once (mechanical + mock/Gemini + validator).

### C. CORS on backend

In `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### D. Settings page

Repurpose Live settings:

| Old | New |
|-----|-----|
| OpenAI base URL | MVP API base URL |
| API key | unused for local MVP (or Gemini key only if calling Gemini from UI — prefer server-side) |
| Model | `AI_CLIENT` is server env (`mock`/`gemini`) |

### E. Seed enrichment (validation)

Import Compass `GOLDEN` + Hezbollah article into `data/evaluation/` so backend eval matches what the UI demos.

## 3. What not to wire yet

- Full multi-phase Live LLM graph/semantic/search duplication (backend already orchestrates)
- Auth
- Persisting accept/reject to Firestore (Phase 7)
- Replacing Demo Mode seed (keep for zero-backend demos)

## 4. Run both locally

```bash
# terminal 1 — API
cd ai-proofreading
uvicorn app.main:app --reload --port 8000

# terminal 2 — UI
cd ai-proofreading/frontend
npm run dev -- --port 5173 --host 127.0.0.1
```

Then: open UI → Live Mode → open article → “تشغيل المراحل (Live)” → suggestions from MVP.

## 5. Success criteria for wired MVP

1. Live review returns real MVP findings (mechanical + mock/Gemini).
2. Highlights align with section text (offsets correct).
3. Accept/reject still only affect preview.
4. `/reviews/{id}/debug` can power Validator tab.
5. Demo Mode still works offline with seed.

## Observed UI routes (for wiring priority)

1. `/` home  
2. `/review/:id` **primary**  
3. `/review/:id/validator` ← debug findings  
4. `/review/:id/evaluation` ← evaluations/run  
5. `/rules`, `/entities` ← CRUD APIs  
6. `/settings` ← API base URL  
7. `/new-article` ← parse/upload then review  
