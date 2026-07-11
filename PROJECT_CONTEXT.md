# Project: Arabic Editorial Proofreading Engine Prototype

## Purpose
Build a simple but credible backend prototype for an Arabic editorial proofreading and review engine.

Existing UI reference:
https://editor-compass-00.lovable.app

For this stage, focus only on the engine, processing pipeline, API contracts, dataset handling, testing, and Gemini integration. Do not spend time building a frontend.

The prototype must demonstrate that an Arabic news article can be:
1. accepted as text;
2. divided into stable editorial segments;
3. checked using deterministic mechanical rules;
4. checked against a small editorial rule repository;
5. analyzed by Gemini using retrieved rules and examples;
6. returned as structured findings;
7. validated before being shown to an editor;
8. evaluated against original/corrected article pairs.

This is a prototype, not a production platform.

## Core principle
AI suggests. Editors decide.

The engine must never:
- publish content;
- approve content;
- add unsupported facts;
- silently rewrite complete articles;
- change editorial stance;
- remove attribution;
- invent editorial rules;
- claim synthetic rules are Al Jazeera rules.

When uncertain, return `needs_editor_review`.

## Scope
Supported now:
- Arabic pasted text
- TXT and DOCX
- optional HTML
- headline and body
- deterministic Arabic checks
- editorial rule retrieval
- Gemini structured review
- structured JSON findings
- evaluation using before/after pairs
- local storage initially
- optional GCP adapters later

Out of scope now:
- authentication
- user management
- WordPress integration
- Google Docs integration
- dashboards
- Kubernetes
- graph database
- model training or fine-tuning
- background queues
- production security
- automatic publishing
- full fact-checking

## Recommended stack
- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2 + SQLite
- Alembic
- pytest
- uvicorn
- python-docx
- BeautifulSoup4
- rapidfuzz
- regex
- Google Gen AI SDK or Vertex AI SDK
- Docker
- Ruff

## Core modules
1. Document intake
2. Article parser
3. Arabic normalization
4. Segmentation
5. Mechanical checker
6. Entity and terminology matcher
7. Rule repository
8. Rule retriever
9. Gemini candidate discovery
10. Gemini judgment
11. Deterministic validator
12. Result aggregator
13. Evaluation engine
14. API layer
15. Persistence layer

## High-level flow
Input article
-> Parse
-> Build stable segments
-> Normalize for matching
-> Run mechanical checks
-> Detect entities and terminology
-> Retrieve relevant editorial rules
-> Call Gemini
-> Validate Gemini findings
-> Aggregate findings
-> Return structured review

## Article and segment model
Preserve original text at all times.

Example article:
```json
{
  "document_id": "DOC-001",
  "language": "ar",
  "source": "manual",
  "headline": "...",
  "body": "...",
  "metadata": {}
}
```

Example segment:
```json
{
  "segment_id": "SEG-001",
  "document_id": "DOC-001",
  "zone": "headline",
  "text": "...",
  "normalized_text": "...",
  "start_offset": 0,
  "end_offset": 60,
  "sequence": 1
}
```

Allowed zones:
- headline
- subheadline
- body
- quote
- caption
- source_attribution
- unknown

## Arabic normalization
Normalization is only for matching and retrieval.
Implement configurable normalization for:
- diacritics removal
- tatweel removal
- Alef variants to ا
- ى to ي for matching
- whitespace normalization
- punctuation normalization where useful
- optional ة/ه equivalence only for fuzzy matching
- Arabic/Persian digit normalization

Never destructively normalize source text.

## Mechanical checks
Implement deterministic checks for:
1. duplicate adjacent words
2. repeated whitespace
3. whitespace before punctuation
4. missing whitespace after punctuation
5. repeated punctuation
6. known spelling replacements
7. approved entity spelling
8. inconsistent entity spelling in one article
9. common Arabic letter variants
10. date and number formatting
11. quotation-mark consistency
12. malformed segments

Mechanical checks must not use Gemini.

## Editorial rules
Initial categories:
- spelling
- punctuation
- terminology
- entity_name
- attribution
- attribution_strength
- unsupported_certainty
- loaded_framing
- implicit_blame
- quote_voice
- publisher_voice
- headline_framing
- caption_framing
- unsupported_causality
- stance_drift
- clarity
- repetition

Example rule:
```json
{
  "rule_id": "ATTR-001",
  "version": "1.0",
  "title_ar": "الحفاظ على نسبة القول إلى المصدر",
  "category": "attribution",
  "rule_type": "relational",
  "description_ar": "يجب ألا يتحول قول منسوب إلى مصدر إلى حقيقة مقررة بصوت الناشر.",
  "applies_to_zones": ["headline", "body", "quote", "source_attribution"],
  "severity": "high",
  "keywords": ["قال", "ذكر", "أفاد", "زعم", "ادعى", "أكد", "بحسب"],
  "examples": [
    {
      "input": "الحكومة مسؤولة عن الأزمة.",
      "preferred": "وحمّل المصدر الحكومة مسؤولية الأزمة.",
      "reason": "الحفاظ على نسبة الادعاء إلى مصدره."
    }
  ],
  "active": true
}
```

## Rule retrieval
Do not use a vector database in v1.
Retrieve using:
- article zone
- normalized keywords
- detected entities
- terminology matches
- category hints
- fuzzy matching
- lightweight scoring

Default limits:
- 5 rules per normal segment
- 8 for headline/caption
- 10 for ambiguous/high-risk segments

## Gemini interface
Create:
```python
class EditorialAIClient(Protocol):
    async def discover_candidates(...): ...
    async def judge_candidates(...): ...
```

Implement:
1. MockEditorialAIClient
2. GeminiEditorialAIClient

The full app and tests must run without GCP credentials using the mock implementation.

## Gemini behavior
Use Gemini only after parsing, segmentation, normalization, mechanical checks, entity matching, and rule retrieval.

Send:
- document metadata
- article segments
- mechanical findings
- retrieved rule cards
- detected entities
- allowed decisions/categories
- safety constraints
- JSON schema

Do not ask Gemini to rewrite the full article.
Use structured output only.

## Finding schema
```json
{
  "finding_id": "FND-001",
  "document_id": "DOC-001",
  "segment_id": "SEG-001",
  "source": "mechanical | gemini",
  "category": "attribution_strength",
  "decision": "acceptable | suggest | replace | soft_warning | hard_warning | ban | needs_editor_review",
  "severity": "low | medium | high | critical",
  "original_text": "...",
  "suggested_text": "...",
  "start_offset": 0,
  "end_offset": 20,
  "rule_ids": ["ATTR-001"],
  "entity_ids": [],
  "explanation_ar": "...",
  "confidence": 0.85,
  "requires_editor_review": true,
  "validation_status": "pending | valid | invalid",
  "validation_errors": []
}
```

Rules:
- suggested_text may be null for warnings
- every finding references an existing segment
- original_text must exist in the segment
- offsets must match exact original text
- unknown rule IDs/categories/decisions are invalid
- high-risk findings always require editor review

## Deterministic validation
Validate:
- schema
- document and segment IDs
- exact source span
- offsets
- category/decision/severity
- rule and entity IDs
- suggestion identity/length
- explanation presence
- duplicates/overlap
- segment boundaries

Invalid findings must be stored for debug but excluded from editor results.
Do not use an LLM repair pass in v1.

## Dataset handling
Use:
- `data/pairs.zip`
- public Arabic GEC datasets later
- synthetic rule examples

Create importer that:
1. discovers before/after files
2. reads Arabic content
3. optionally strips irrelevant HTML
4. preserves originals
5. aligns paragraphs
6. outputs JSONL
7. marks insert/delete/replace/unchanged spans
8. does not label every change as proofreading
9. adds `requires_human_classification=true`

## Evaluation
Provide CLI:
```bash
python -m app.cli.evaluate --dataset data/evaluation/golden.jsonl
```

Metrics:
- expected issues
- detected issues
- exact match
- partial span match
- category match
- suggestion match
- false positives
- missed findings
- precision/recall/F1
- processing time
- Gemini calls
- token usage where available

## API endpoints
- POST /api/v1/documents/parse
- POST /api/v1/reviews
- GET /api/v1/reviews/{review_id}
- GET /api/v1/reviews/{review_id}/debug
- POST /api/v1/rules
- GET /api/v1/rules
- GET /api/v1/rules/{rule_id}
- POST /api/v1/entities
- GET /api/v1/entities
- POST /api/v1/evaluations/run
- GET /api/v1/health

## GCP
Build local first, then optional adapters for:
- Gemini through Vertex AI
- Cloud Storage
- Firestore
- Cloud Run

Environment variables:
```env
GCP_PROJECT_ID=
GCP_LOCATION=
GEMINI_MODEL=
GOOGLE_APPLICATION_CREDENTIALS=
STORAGE_BUCKET=
USE_GCP=false
AI_CLIENT=mock
```

Unit tests must not require GCP.
