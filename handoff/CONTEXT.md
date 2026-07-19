# Project context (short)

**Repo:** https://github.com/kahmedsaad/arabic-editorial-proofreading  
**Local:** `C:\Users\khhab\Downloads\ai-proofreading`  
**Principle:** AI suggests; editors decide.

**Live Cloud Run (Demo A):** https://arabic-proofreading-web-2tqtjdoq3q-uc.a.run.app (`user`/`demo`)  
**API:** https://arabic-proofreading-api-2tqtjdoq3q-uc.a.run.app — health reports `ai_client=gemini`, `use_gcp=true`

**Status:**
- Redeployed to Cloud Run after Run5b work (gates remain default `off` in production)
- `gemini_run3` / `gemini_run4_no_punctuation` / `gemini_run5_editorial_gates` frozen
- Run5b evaluated: silence FP ~30%; critical recall 0.4211 → **needs_adjustment**
- UI acceptance v1 (20 articles, prod UI): precision 100%, recall 29.4%, 4 missed critical contradictions → **needs_adjustment**
- Validator autopsy done: D06 fails on unknown category (salvage blocked); D01 not reproducible; diagnostics-only changes shipped
- Next proposed: reviewed category canonicalization at model-output boundary; do not enable run5b in prod
- R3/R5 deferred; no fine-tuning; no Al Jazeera scraping

**Key docs:** `docs/EDITORIAL_LABELING.md`, `docs/RUN4_NO_PUNCTUATION.md`, `docs/SPRINT2.md`  
**Latest packets:** `handoff/to_chatgpt.md`, `data/evaluation/ui_acceptance/validator_autopsy_d01_d06.md`
