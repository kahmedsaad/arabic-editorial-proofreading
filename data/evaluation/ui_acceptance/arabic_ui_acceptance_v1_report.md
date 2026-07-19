# Arabic UI Acceptance Test — v1

## Environment and timestamp

- **Live UI:** `https://arabic-proofreading-web-2tqtjdoq3q-uc.a.run.app`
- **API:** `https://arabic-proofreading-api-2tqtjdoq3q-uc.a.run.app`
- **Account:** `user` (editor role). Admin account not required.
- **Execution:** Chrome MCP (Chrome DevTools), real web interface, sequential submissions.
- **Date/time:** 2026-07-19, ~07:00–07:15 UTC (10:00–10:15 local, UTC+3).
- **Method:** Each article created via `/new-article` (headline section = title, lead section = body), analyzed with the live engine, and read from the review screen after the pipeline reached "الحكم النهائي / النتائج النهائية". No suggestion was accepted, rejected, edited, or published. No publish/approve action was ever taken.

## Policy / version visible during testing

- Run mode: **محرك حي (Live)**, engine badge **MVP engine**, model id **`mvp-engine`** (server-side Gemini via Vertex).
- Relevant rules loaded per article (visible in "القواعد والكيانات ذات الصلة"): `CONS-CLAIM, CONS-DATE, CONS-NAME, MECH-GRAMMAR, PUNCT-001, SPELL-001, CONS-NUMBER`.
- **Punctuation policy: off** (no punctuation finding appeared on any article, including clean controls).
- **Editorial gate policy: off** in production (per deployment configuration; `run5b` not enabled in prod). Pipeline stage "بوابة الدقة التحريرية" is present and completes but no gate policy was toggled during this test.
- No standard `/health` or `/version` endpoint was reachable from the browser (404), so version metadata is limited to the UI-visible values above.

## Results for every article

| ID | Difficulty | Expected | Candidates→Judg.→Final (rej. after valid.) | Observed surfaced finding | Class | Time (s) |
|----|-----------|----------|-------------------------------------------|---------------------------|-------|----------|
| E01 | easy | افتتح البلدية→افتتحت البلدية | 3→3→0 (0) | — | FN | 18.7 |
| E02 | easy | حضر الموظفين→حضر الموظفون | 1→1→0 (0) | — | FN | 25.0 |
| E03 | easy | هذا المبادرة→هذه المبادرة | 1→1→0 (0) | — | FN | 15.1 |
| E04 | easy | مسؤلية→مسؤولية | 1→1→1 (0) | spelling مسؤلية→مسؤولية (MECH-SPELL, passed) | **TP** | 15.5 |
| E05 | easy | فاز الطالبتان→فازت الطالبتان | 1→1→0 (0) | — | FN | 19.8 |
| E06 | easy clean | (none) | 0→0→0 (0) | — | clean ✓ | 4.1 |
| M01 | medium | كان الخطة→كانت الخطة | 2→2→0 (0) | — | FN | 13.9 |
| M02 | medium | ثلاثة عشر موظفة→ثلاث عشرة موظفة | 1→1→0 (0) | — | FN | 18.8 |
| M03 | medium | تقريره→تقاريرهم | 1→1→1 (0) | relational تقريره→تقاريرهم (CONS-CLAIM, MECH-GRAMMAR, passed) | **TP** | 24.7 |
| M04 | medium | بإن→بأن | 2→1→1 (0) | relational بإن→بأن (MECH-GRAMMAR, passed) | **TP** | 19.2 |
| M05 | medium | flag unclear pronoun ترميمها | 2→2→0 (0) | — | FN | 10.8 |
| M06 | medium | flag ambiguous ref أنهى كلمته | 1→1→0 (0) | — | FN | 16.7 |
| M07 | medium clean | (none) | 0→0→0 (0) | — | clean ✓ | 5.3 |
| D01 | difficult | تراجعا→ارتفاعا | 1→1→0 (**1 rejected**) | — | FN (critical) | 20.0 |
| D02 | difficult | flag 105% total | 1→1→0 (0) | — | FN (critical) | 17.1 |
| D03 | difficult | flag wrong % (15%, not 25%) | 1→1→0 (0) | — | FN (critical) | 13.6 |
| D04 | difficult | flag number inconsistency 3 vs 2 | 1→1→1 (0) | relational hard_warning المركزين→المراكز الثلاثة (CONS-NUMBER, passed) | **TP** | 21.2 |
| D05 | difficult | flag lost-final vs champion | 2→2→1 (1 rejected) | relational hard_warning headline↔body (CONS-CLAIM, passed) | **TP** | 19.9 |
| D06 | difficult | flag contradictory timeline | 2→1→0 (**1 rejected**) | — | FN (critical) | 27.2 |
| D07 | difficult clean | (none) | 0→0→0 (0) | — | clean ✓ | 6.5 |

## Expected versus observed findings

- **Surfaced findings (5 total), all correct:** E04 (spelling), M03 (pronoun ownership), M04 (بإن→بأن), D04 (numeric inconsistency, warning), D05 (win/loss contradiction, warning).
- **Missed (12 FN):** all pure morphological agreement/case/number/demonstrative errors (E01, E02, E03, E05, M01, M02), both clarity/ambiguity cases (M05, M06), and four hard contradictions (D01, D02, D03, D06).
- Pattern: the engine surfaces **mechanical spelling** and **relational/semantic corrections that carry a concrete replacement or hard-warning** (pronoun ownership, hamza-after-verb, number/claim inconsistency). It does **not** surface morphological agreement fixes (verb–subject gender, case endings, demonstrative agreement, number-noun agreement), and it drops several contradiction candidates either at judgment or at the validation stage.

## Metrics

**Denominators:** 17 issue articles (one expected finding each), 3 clean controls, 20 total.

| Metric | Value |
|--------|-------|
| Expected-issue recall (overall) | 5/17 = **29.4%** |
| — recall, easy | 1/5 = **20.0%** |
| — recall, medium | 2/6 = **33.3%** |
| — recall, difficult | 2/6 = **33.3%** |
| Finding precision (relevant surfaced / total surfaced) | 5/5 = **100%** |
| False positives (total) | **0** |
| False positives per article | **0.00** |
| Duplicate false positives | **0** |
| Punctuation findings | **0** |
| Wrong-fix count | **0** |
| Zero-finding accuracy on clean controls | 3/3 = **100%** |
| FP-free article rate | 20/20 = **100%** |
| Zero-finding rate (all articles) | 15/20 = **75%** |
| Submission failures | **0/20** |
| Average processing time | **16.6 s** (min 4.1 s, max 27.2 s) |

## False-positive examples

None. No article — issue or clean control — produced an unsupported, duplicate, or punctuation-only finding. All 5 surfaced findings were relevant and correct.

## Missed critical contradictions (critical failures)

Per the task definition, missed contradictions and incorrect numeric handling are critical. Four critical misses:

- **D01** — "ارتفعت … من 10 … إلى 12 …، وهو ما يمثل **تراجعا**" (a rise labeled a decline). Detected internally (1 candidate, 1 judgment) but **rejected by the validator**; 0 surfaced.
- **D02** — percentages 62 + 28 + 15 = **105%** while claiming all participants. Dropped after judgment; 0 surfaced.
- **D03** — 500k→425k stated as **25%** (actual 15%). Dropped after judgment; 0 surfaced.
- **D06** — timeline contradiction (starts September / actually started July / will not start before approval). Detected internally (2 candidates, 1 judgment) but **rejected by the validator**; 0 surfaced.

Positive: D04 and D05 contradictions were surfaced correctly as `hard_warning` items for editor decision.

## Unsafe or meaning-changing corrections

None observed.
- No number was silently changed. On D03 (wrong percentage) the tool made **no** edit — safe, though it also failed to flag.
- D04 proposed `المركزين → المراكز الثلاثة`, which leans toward "three", but it is presented as a `hard_warning` (not a silent replacement) and left for the editor.
- D05 was a `hard_warning` with the **Accept button disabled**, so no meaning-changing text edit is offered.

## UI defects, timeouts, authentication problems

- **No** submission failures, timeouts, auth failures, or automation blocks across all 20 runs.
- The locked original text ("النص الأصلي مُقفل / لا يُعدَّل أبداً") behaved correctly; no suggestion was auto-applied. No publish/approve control was invoked.
- Persistent behavior consistent with prior validation (autorun via `?autorun=1`, live MVP engine, session stable throughout).
- Minor tooling note (not an app defect): `navigate_page` intermittently reports a 10 s navigation timeout even though the page loads; worked around by client-side navigation. Does not affect the product.

## Screenshot paths

The Chrome MCP (DevTools) server sandbox **rejected all workspace file-write paths** (`Access denied … not within any of the configured workspace roots`) for every attempted location, so PNG files could not be written into `data/evaluation/ui_acceptance/screenshots/`. Required screenshots were instead captured **inline** in the agent transcript (viewport images) as evidence:

- First case: **E01** filled new-article form (live/MVP badges, headline + lead sections).
- One medium case: **M01** review result (candidates 2 → final 0).
- One difficult case: **D01** review result showing "التحقق والتصحيح: مرفوض بعد التحقق: 1 · النتائج النهائية: 0" (validator rejecting a detected contradiction).
- Clean control 1: **E06** review result (0 candidates, 0 findings, no punctuation FP).
- Clean control 2: **D07** review result (0 candidates, 0 findings).

See `screenshots/README.md` for the mapping and the sandbox limitation.

## Verdict

**needs_adjustment**

Rationale:
- **Strengths:** precision is excellent (100%, zero FPs, zero punctuation FPs), all three clean controls returned zero findings, no unsafe/meaning-changing edits, no publishing, no cross-user content exposure, and stable UI with no submission failures.
- **Blocking weakness:** expected-issue recall is only **29%**, and the system **missed 4 of 6 hard contradictions (D01, D02, D03, D06)** — exactly the critical-failure category defined for this test. It also misses the entire class of morphological agreement errors (E01–E03, E05, M01, M02).
- Two contradiction misses (D01, D06) were **detected then dropped by the validation stage**, indicating the recall loss is partly a suppression/validation-tuning issue rather than pure non-detection.

Not `pass` (critical contradictions missed). Not `blocked` (the platform is fully functional, safe, and returned evidence for all 20 cases).

## Recommended next action

1. Investigate why the **validator rejects detected contradictions** (D01, D06 were caught internally then dropped). Re-check validator rules against the numeric/temporal contradiction cases before touching prompts.
2. Investigate the **judgment-stage suppression** of numeric contradictions D02/D03 (candidates generated, 0 surfaced) — these are high-value newsroom checks.
3. Decide whether **morphological agreement** (verb–subject gender, case endings, demonstratives, number-noun) is in scope for surfacing; if yes, it is a systematic recall gap. Do **not** change frozen runs/gold/prompts or enable `run5b` in prod as part of this — treat as a separate, evidence-first tuning task.
