# Run3 punctuation analysis (immutable diagnostics)

**Run3 location (do not modify):** `data/evaluation/runs/gemini_run3/`  
**Derived analysis:** `data/evaluation/analysis/gemini_run3_precision/`

## Headline result

| Metric | Value |
|--------|-------|
| Clean-article FP rate | **77%** (231/300) |
| Total findings | 595 |
| Punctuation | **432** (~73% of all FPs) |
| Attribution | 40 |
| Clarity | 34 |
| Headline mismatch | 20 |

**Root cause:** punctuation noise is overwhelmingly **deterministic mechanical** checks, not Gemini. Sample labels are mostly `FND-M-*` with explanations like “تنقص مسافة بعد علامة الترقيم” (`MECH-PUNCT-AFTER`).

## Modules that emit punctuation findings

| Source | Module | Rule IDs | Notes |
|--------|--------|----------|-------|
| Deterministic | `app/mechanical/checks.py` | `MECH-PUNCT-SPACE`, `MECH-PUNCT-AFTER`, `MECH-PUNCT-DUP`, `MECH-WS`, `MECH-QUOTE`, `MECH-PAREN`, `MECH-BRACK` | Primary generator of run3 punctuation FPs |
| Rule metadata | `data/rules/PUNCT-001.json` | `PUNCT-001` | Lexical rule card; not the main emitter |
| Gemini | `app/ai/gemini_client.py` | varies | Can emit `category=punctuation`; minority vs mechanical |
| Gate (new) | `app/postprocess/punctuation_gate.py` | — | Filters before aggregation |
| Policy (new) | `app/postprocess/punctuation_policy.py` | — | `off` / `strict` / `full` + thresholds |

## Behavior before run4 gate

- **Confidence:** mechanical punctuation findings use `confidence=1.0`
- **Severity:** typically `low`
- **Headline:** same detectors ran on headline segments (no special case) → style noise
- **Quotes:** quote-pair checker (`MECH-QUOTE`) exists; spacing checkers did **not** skip quote interiors
- **Dedupe:** generic `dedupe_findings` keyed by `(segment_id, original_text)` — not punct-subtype/offset aware; Gemini vs mechanical duplicates possible

## Dominant rule family (noise)

1. `MECH-PUNCT-AFTER` — missing space after `.` `،` `:` — often stylistic on published Arabic
2. `MECH-PUNCT-SPACE` — space before punctuation
3. `MECH-WS` — repeated whitespace (categorized as `punctuation`)
4. `MECH-PUNCT-DUP` — genuine high-value (`،،`, `..`) — **keep in strict**
5. `MECH-QUOTE` — unbalanced quotes — **keep in strict**

## Policy response (run4 prep)

`PUNCTUATION_POLICY=strict` (default):

- Allow only objective subtypes: repeated marks, unbalanced delimiters, broken sentence boundaries
- Suppress optional commas/periods, headline style, quote-internal style, low-impact spacing
- Deduplicate by `(document_id, segment_id, start, end, subtype)`; prefer mechanical over Gemini

See also: `docs/SPRINT2.md`, `docs/RUN4_NO_PUNCTUATION.md`

## Intermediate targets (documentation only)

```text
Clean FP rate, all: <=25% for run4 intermediate target
Clean FP rate, editorial-only: <=15%
Punctuation findings: <=30 in strict mode
Findings per clean article: <=0.3
Zero-finding clean articles: >=75%
```
