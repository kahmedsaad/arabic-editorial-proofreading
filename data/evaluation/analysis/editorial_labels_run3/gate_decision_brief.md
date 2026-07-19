# Gate decision brief: calibration before run5

Status: **recommendations only**. No gate, prompt, model run, or source label is changed by this brief.

Evidence base: 163 AI-labeled non-punctuation findings from the frozen run3 silence set. These labels are calibration evidence pending human review, not editorial truth.

## Decision and order

For a future, separate `gemini_run5_editorial_gates` implementation task:

1. R1 — narrow attribution gate
2. R2 — narrow generic-clarity gate
3. R4 — narrow headline certainty-escalation gate

R3 entity/militia and R5 optional spelling are **deferred**.

## R1 — Attribution: recommend narrowly

**Observed evidence:** 40 attribution-family findings were labeled drop and none keep. Most concern vague sources such as `مصادر محلية`, `مصادر مطلعة`, `وسائل إعلام`, or claims that are already attributed nearby.

**Recommended class to suppress:** a finding whose only complaint is that a factual claim uses a vague source, or whose requested attribution is already present in the nearby article context.

**Must remain eligible:** a material factual assertion made in publisher voice with no attribution in the available article context; a suggestion that correctly restores lost attribution or factual modality.

**Expected benefit:** remove the largest measured false-positive cluster, potentially up to 40 run3-like findings before overlap with other rules.

**Recall risk:** a lexical rule for `مصادر` could hide genuinely unsupported high-impact claims. The gate therefore requires both pattern classification and nearby-context evidence; it must not suppress based on a source token alone.

**Acceptance criteria:**

- On the same 300-article silence set, attribution findings fall by at least 60% from the run3 editorial count.
- A fresh human review of at least 20 remaining attribution findings reaches precision ≥0.55.
- Every current material-unattributed fixture still surfaces.
- Attribution-related critical recall on the issue-containing benchmark is no more than 5 percentage points below the pre-gate baseline.

## R2 — Clarity: recommend narrowly

**Observed evidence:** all 34 clarity findings were labeled drop. The dominant patterns are generic “clarify,” long-paragraph splitting, and rewrite preferences without a named comprehension failure.

**Recommended class to suppress:** generic clarity or long-paragraph advice that does not identify a specific ambiguity, contradiction, missing referent, incomplete construction, or concrete comprehension failure.

**Must remain eligible:** findings that quote the ambiguous span and identify the unresolved referent or contradiction; incomplete or malformed text that prevents comprehension.

**Expected benefit:** remove up to 34 run3-like low-impact findings and materially reduce findings per clean article.

**Recall risk:** a model may describe a real ambiguity too vaguely. Require stronger structured evidence rather than suppressing every `clarity` category result.

**Acceptance criteria:**

- Generic clarity findings on the silence set fall by at least 70%.
- Remaining clarity findings identify a concrete span and defect.
- A fresh human review of at least 15 remaining clarity findings reaches precision ≥0.60.
- Critical clarity/completeness recall on the issue benchmark is no more than 5 percentage points below baseline.

## R4 — Headline: recommend certainty-escalation only

**Observed evidence:** the headline family is mixed: 10 keep, 12 drop, and 1 uncertain. Keeps include material place, outcome, and status conflicts. Drops are concentrated in ordinary headline compression and differences in hedging or attribution.

**Recommended class to suppress or demote:** a headline finding whose only evidence is that an assertive headline compresses a hedged or sourced body statement, with no numeric, geographic, temporal, outcome, denial, or other material conflict.

**Must remain eligible:** material headline/body contradictions; unsupported overstatement; changed event status; explicit denial in the body; numeric, date, place, actor, or outcome mismatch.

**Expected benefit:** remove a smaller but visible false-positive cluster while retaining editor-facing headline conflicts.

**Recall risk:** certainty escalation can itself mislead. Ambiguous cases should be demoted to low severity or left for review rather than hard-suppressed.

**Acceptance criteria:**

- All currently labeled material headline conflicts remain visible in regression fixtures.
- Remaining headline precision is ≥0.65 in a fresh human review.
- Silence-set headline findings fall without reducing issue-benchmark headline critical recall by more than 5 percentage points.
- Unsupported-overstatement fixtures remain visible even when no number or place is involved.

## R3 — Entity/militia: defer

The current silence-set labels suggest house-style mismatch, but they do not establish the intended Al Jazeera policy or performance on representative AJ copy.

Evidence required before consideration:

- an editor-approved, versioned lexicon/policy for terms such as `مقاتل`, `عناصر`, `ميليشيا`, and named entities;
- a publisher-profile design proving that a non-AJ suppression cannot leak into AJ behavior;
- at least 30 human-reviewed positive and 30 negative examples across conflict and non-conflict contexts;
- regression fixtures for quotations, attributed characterization, organization names, and neutral publisher voice;
- issue-benchmark recall showing no loss for material entity confusion or loaded framing.

Decision: **no R3 gate in the next implementation pass**.

## R5 — Optional spelling: defer

Thirteen spelling findings are too small a base for a production suppression, and the category mixes optional variants with real typos.

Evidence required before consideration:

- a newsroom-approved Arabic orthography/style lexicon distinguishing required corrections from accepted variants;
- corpus evidence for each candidate pair, including `مليشيات/ميليشيات`;
- at least 50 human-reviewed spelling findings, stratified by dictionary rule and quote status;
- explicit quote protection and meaning-preservation tests;
- recall fixtures for non-words, adjacent duplication, malformed tokens, and demonstrable grammar/spelling errors.

Decision: **no R5 gate in the next implementation pass**.

## Measurement requirements for the future run

Run R1, then R2, then R4 as isolated changes where practical. For each step, record:

- silence-set articles with at least one editorial finding;
- findings per article and zero-finding rate;
- precision overall and by affected category on a fresh human-reviewed sample;
- exact removed/retained finding IDs relative to run4;
- critical recall overall and for attribution, clarity, and headline subsets on the issue-containing benchmark.

Do not accept a precision gain that violates quote safety, changes editorial text automatically, or reduces critical recall beyond the stated limits.
