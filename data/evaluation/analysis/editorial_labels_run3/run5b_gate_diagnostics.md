# Run5b gate diagnostics

Evidence sources: frozen Run2/Run5 benchmark reports and engine outputs, the
Run5 silence report and label dump, and deterministic replay through the frozen
Run5 rule behavior. Hidden gold was accessed only by the existing scorer and
attribution script; it was not manually inspected or edited.

## Critical findings matched in Run2 and missed in Run5

Run5 benchmark output did not persist rejected finding payloads or pre-gate
candidate lists. The “Run5 candidate before gating” column therefore reports
the strongest persisted Run5 candidate and explicitly marks unavailable
pre-gate data. Gate attribution is based on deterministic replay of the Run2
matched finding. This limitation prevents claiming a live suppression where
only replay evidence exists.

| Case / gold | Gold category and text | Run2 matched finding | Run5 candidate before gating | Cause / exact condition | Assessment | Run5b correction |
|---|---|---|---|---|---|---|
| `case-0005` / 1 | `pronoun_ambiguity`; `وأكد أنه وافق` | `FND-AI-0002`; `attribution_strength`; `وأكد` | Not persisted. Best exposed: `FND-E-0001`, `attribution`, `أكد أنه وافق`, score 2.5 | R1 replay suppressed because the Run5 nearby-attribution check counted the attribution cue under review as evidence that the issue was already resolved | Harmful: the finding concerns pronoun ambiguity / strength, not a vague-source nag | In `run5b`, fail open for `attribution_strength` and require an attribution cue before—not inside—the finding span |
| `case-0006` / 0 | `majority_precision`; `بأغلبية أعضائه` | `FND-AI-0001`; `numeric_contradiction`; full headline | Exposed `FND-AI-0001`, `headline_body_mismatch`, same headline, score 3.7 | No editorial gate matched. Candidate was below scorer match threshold / wrong category detail | Not a gate loss; model/matching variance | Numeric/date remain unconditional pass-through; no broader post-model rule |
| `case-0038` / 0 | `attribution_strength`; `وشيكًا ومؤكدًا` | `FND-AI-0005`; `attribution_strength`; `مؤكدًا` | Not persisted. Best exposed: headline mismatch on `المصدر يؤكد أن الاتفاق وشيك`, score 3.0 | R1 replay treated existing attribution as resolving a finding about possibility→certainty escalation | Harmful: attribution/certainty change is material | In `run5b`, fail open for attribution-strength and certainty-escalation evidence |

Aggregate: three lost critical items; two are R1-replay losses and one is
non-gate variance. R2 and R4 account for no demonstrated critical loss in this
comparison, although the silence evidence below shows R4 was unsafe.

## Run5 R4 suppressions (13/13 inspected)

All thirteen contain a potentially material semantic difference. Under the
Run5b safety contract they must remain visible, even where a later editor may
decide the finding is low value.

| Article / finding | Material evidence in Run5 finding | Run5 action | Run5b assessment |
|---|---|---|---|
| `ANAD-015348:FND-AI-0001` | Explicit contradiction and certainty change | suppress | Keep |
| `ANAD-029457:FND-AI-0001` | No official statement vs certain headline | suppress | Keep |
| `ANAD-049216:FND-AI-0001` | “new” scope/category mismatch | suppress | Keep |
| `ANAD-079803:FND-AI-0001` | Attribution and certainty change | suppress | Keep |
| `ANAD-087719:FND-AI-0001` | Preliminary vs confirmed injury status | suppress | Keep |
| `ANAD-100434:FND-AI-ANAD-100434-001` | Future announcement vs current acquittal | suppress | Keep |
| `ANAD-112857:FND-AI-0001` | Refusal outcome vs rejection of current terms | suppress | Keep |
| `ANAD-119726:FND-AI-0001` | Organization / decision-maker role mismatch | suppress | Keep |
| `ANAD-132909:FND-AI-2` | Date plus attribution/certainty difference | suppress | Keep |
| `ANAD-134141:FND-AI-0001` | Player-role mismatch | suppress | Keep |
| `ANAD-148889:FND-AI-0002` | Singular/plural legal-scope quantity mismatch | suppress | Keep |
| `ANAD-347449:FND-AI-0002` | Time window and certainty mismatch | suppress | Keep |
| `ANAD-418136:FND-AI-0001` | Forecast/possibility turned into fact | suppress | Keep |

Root cause: Run5 allowed lexical body overlap and style/certainty markers to
outweigh explicit semantic-risk language. The short material-marker list did
not reliably model entities, roles, event status, polarity, attribution, or
certainty. Run5b therefore requires positive evidence of generic compression
and fails open on structured or textual semantic differences.

## Run5 R1 suppressions (17/17 inspected)

The 17 recorded silence suppressions were ordinary vague-source findings and
remain valid R1 targets:

`ANAD-056373:FND-AI-1`; `ANAD-132203:FND-AI-4`;
`ANAD-132203:FND-AI-18`; `ANAD-132909:FND-AI-3`;
`ANAD-166538:FND-AI-1`; `ANAD-213771:FND-AI-0001`;
`ANAD-347449:FND-AI-0003`; `ANAD-443448:FND-AI-0001`;
`SANAD-000032:FND-AI-0001`; `SANAD-000032:FND-AI-0003`;
`SANAD-036358:FND-AI-0001`; `SANAD-071811:FND-AI-0001`;
`SANAD-073231:FND-AI-0001`; `SANAD-073231:FND-AI-0003`;
`SANAD-074502:FND-AI-0002`; `SANAD-102133:FND-AI-0001`;
`SANAD-110441:FND-AI-0001`.

Run5b does not broaden R1. Its only correction is the narrow critical-safety
exception for attribution-strength / certainty-escalation findings and the
requirement that “already attributed” evidence occur outside the cited span.

## All 34 Run5 clarity findings

| Pattern | Count | Source | Run5b decision |
|---|---:|---|---|
| `مقطع طويل جداً قد يحتاج إعادة تقسيم.` | 29 | mechanical | Suppress 28; keep one whose cited span contains a numeric claim |
| `خلط بين الأرقام العربية واللاتينية في المقطع.` | 4 | mechanical | Keep: numeric handling is immutable |
| Ambiguous `الذي` with two named possible referents and contradiction explanation | 1 | Gemini | Keep: concrete referent ambiguity |

The 29 generic IDs are:

`ANAD-000848:FND-M-0010`, `ANAD-029457:FND-M-0005`,
`ANAD-032468:FND-M-0012`, `ANAD-038468:FND-M-0007`,
`ANAD-050751:FND-M-0006`, `ANAD-109931:FND-M-0002`,
`ANAD-201791:FND-M-0002`, `ANAD-225223:FND-M-0008`,
`ANAD-233963:FND-M-0002`, `ANAD-432114:FND-M-0007`,
`ANAD-439722:FND-M-0019`, `ANAD-495164:FND-M-0016`,
`SANAD-023844:FND-M-0005`, `SANAD-026275:FND-M-0006`,
`SANAD-028226:FND-M-0002`, `SANAD-031354:FND-M-0008`,
`SANAD-036942:FND-M-0004`, `SANAD-049430:FND-M-0013`,
`SANAD-049492:FND-M-0012`, `SANAD-050127:FND-M-0072`,
`SANAD-050127:FND-M-0140`, `SANAD-050198:FND-M-0016`,
`SANAD-060349:FND-M-0006`, `SANAD-081131:FND-M-0007`,
`SANAD-083623:FND-M-0024`, `SANAD-115667:FND-M-0020`,
`SANAD-121407:FND-M-0069`, `SANAD-122151:FND-M-0045`,
`SANAD-129081:FND-M-0007`.

`SANAD-031354:FND-M-0008` is the protected exception because its cited span
contains the concrete numeric claim `4 ملايين`; Run5b preserves numeric/date
content unconditionally even when the explanation is generic.

The numeric-mix IDs are `ANAD-081530:FND-M-0001`,
`ANAD-139392:FND-M-0002`, `ANAD-147096:FND-M-0001`, and
`ANAD-491461:FND-M-0001`. The concrete Gemini finding is
`SANAD-008976:FND-AI-6`.

### Why R2 fired zero times

- Category normalization: not the cause; all 34 persisted as `clarity`.
- Arabic normalization: not the cause; the 29 generic explanations exactly
  contain the configured long-passage marker.
- Wrong field: not the cause; `explanation_ar` contains the discriminating text.
- Missing markers: not the cause for the dominant cluster.
- **Enforcement input mismatch: root cause.** Run5 called the editorial gate on
  `ai_kept` only. Thirty-three of 34 clarity findings were mechanical and never
  reached R2.

Run5b applies R2 after the mechanical+AI merge, normalizes Arabic for robust
matching, suppresses only demonstrated generic patterns, and fails open on
numeric/date, referent, contradiction, entity/role/place, certainty,
attribution, quotation, and meaning-changing suggestions.
