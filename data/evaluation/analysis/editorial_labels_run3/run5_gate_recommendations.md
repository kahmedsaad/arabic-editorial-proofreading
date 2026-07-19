# Run5 gate recommendations (no implementation)

Based only on scored labels in this folder.  
Do **not** implement `gemini_run5_editorial_gates` until these gates are coded as a separate task and critical recall is re-checked on the issue-containing benchmark.

Overall editorial precision on the 163 silence-set non-punctuation findings: **15.2%** (23 keep / 128 drop; 12 uncertain excluded).

---

## R1 — Suppress vague-source attribution nags (strong evidence)

| | |
|--|--|
| **Evidence** | Attribution: 40 findings → 0 keep / 40 drop (precision 0.0). Dominant reasons: `too_low_impact`, `optional_style`. Patterns: مصادر قبلية/محلية/مطلعة، وسائل إعلام، (وكالات). |
| **Suppress** | Findings whose span/explanation is primarily “vague unnamed source” (`R_SOURCE_VAGUE` / مصادر* / وسائل إعلام) **unless** the claim is presented as publisher fact with zero attribution anywhere in article (harder rule; defer to secondary check). |
| **Expected precision benefit** | Remove ~40 FPs from this labeled pool (~25% of all 163). Clean-set FP rate should fall sharply if run3-like attribution volume recurs. |
| **Recall risk** | Medium on AJ house desk if editors want every vague source flagged. On silence/public corpora: low. Mitigate with allowlist for AJ-only policy profile later. |
| **Acceptance** | On a re-run with this gate: attribution findings on the same 300 clean articles ≤20% of run3 attribution count; labeled attribution precision ≥0.50 on a fresh sample of ≥20 remaining attribution hits. |
| **Critical recall** | After run5: score issue-containing benchmark; attribution-related critical issues must not drop >5 pp vs run3/run4 baseline (document delta). |

---

## R2 — Suppress generic clarity / long-paragraph rewrites (strong evidence)

| | |
|--|--|
| **Evidence** | Clarity: 34 → 0 keep / 34 drop (precision 0.0). Reasons: `too_low_impact` (long paragraph), `optional_style`. |
| **Suppress** | Clarity findings whose explanation is “مقطع طويل” / split preference, or rewrite-without naming a concrete ambiguity (missing referent, contradiction, incomplete sentence). |
| **Expected precision benefit** | Remove ~34 FPs (~21% of pool). |
| **Recall risk** | Low–medium: may miss real referent ambiguity if model only says “clarify.” Require keep-path when explanation cites التباس / غامض / غير مكتمل **and** names the referent. |
| **Acceptance** | Clarity findings/article on clean set ≤0.05; ≥80% of remaining clarity labels keep on spot-check n≥15. |
| **Critical recall** | Benchmark critical clarity/completeness issues recall ≥ run4 − 5 pp. |

---

## R3 — Disable AJ house-style entity/framing rules on non-AJ corpora (strong evidence)

| | |
|--|--|
| **Evidence** | Entity consistency: 0 keep / 15 drop (2 unc). Loaded framing: 0 / 14. Reasons: `acceptable_arabic`, `incorrect_rule` (مقاتل→عناصر, ميليشيات). |
| **Suppress** | On SANAD/ANAD/public silence profiles: block `entity_name` replacements مقاتل↔عناصر and militia/loaded lexicon unless `publisher_profile=aj`. |
| **Expected precision benefit** | Remove ~20–25 FPs from this pool. |
| **Recall risk** | High only if the same gate is applied to AJ production copy without a profile switch. Gate must be profile-scoped. |
| **Acceptance** | Zero مقاتل/ميليشيا style findings on silence evaluation set; AJ fixture still emits them when profile=aj. |
| **Critical recall** | AJ issue-benchmark framing/entity criticals unchanged when profile=aj. |

---

## R4 — Headline: keep material conflicts; drop certainty-escalation (mixed → narrow gate)

| | |
|--|--|
| **Evidence** | Headline family: 23 findings → 10 keep / 12 drop / 1 uncertain (precision ~0.45). Drops are mostly certainty/hedging compression; keeps are place/outcome contradictions and clear overstatements. |
| **Suppress / require** | Suppress headline findings whose only claim is “مستوى اليقين” / hedged body vs assertive headline **without** numeric, geographic, outcome, or denial conflict. Keep when explanation cites place/date/outcome contradiction or explicit denial in body. |
| **Expected precision benefit** | Push headline precision toward ≥0.70 on this pool (drop ~8–12 certainty FPs; keep material conflicts). |
| **Recall risk** | Medium: some overstatement is editorial-valuable. Prefer demote-to-low-severity rather than hard drop if uncertain. |
| **Acceptance** | On labeled re-score of remaining headline hits: precision ≥0.65; at least the current keep set (material conflicts) still surfaces. |
| **Critical recall** | Headline-mismatch criticals on issue benchmark ≥ run4 − 5 pp. |

---

## R5 — Spelling: lexicon optional-style demotion (moderate evidence)

| | |
|--|--|
| **Evidence** | spelling: 13 → 3 keep / 10 drop (precision 0.23). Many `optional_style` / `acceptable_arabic` (مليشيات/ميليشيات, known replacements). |
| **Suppress** | Demote or suppress “استبدال إملائي معروف” hits and attested orthographic doublets unless confidence high **and** suggestion is uniquely correct. |
| **Expected precision benefit** | Modest (~7–10 FPs). |
| **Recall risk** | Medium for real typos. Keep adjacent-duplicate and clear non-word errors. |
| **Acceptance** | Spelling precision ≥0.50 on next labeled sample; dup-word / incomplete-token keeps retained. |
| **Critical recall** | Spelling/grammar criticals on issue benchmark ≥ run4 − 5 pp. |

---

## No gate (weak or protective)

| Category | Why |
|----------|-----|
| **Numeric consistency** | 5 keep / 0 drop / 9 uncertain — do not suppress; improve verification instead. |
| **repetition / grammar / consistency** | Tiny n; keeps look objective — no suppress. |
| **unsupported_certainty** | n=3 only — fold into R4 if needed; no standalone gate. |

---

## Suggested run5 order

1. R1 + R2 (largest FP mass)  
2. R3 (profile-scoped)  
3. R4 (narrow headline)  
4. R5 (optional)  
5. Re-run evaluation → compare to run4 → issue-benchmark critical recall  

**This document is recommendations only. No production gate code was added in this task.**
