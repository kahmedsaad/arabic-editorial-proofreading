# Label consistency audit (all 163 AI labels)

> Labels remain unchanged. This audit records flags and proposed corrections only.

## Aggregate

- Total labels audited: **163**
- Exact duplicate groups: **12**
- Exact duplicate groups with inconsistent decisions: **0**
- Strong findings: **12**
- Review flags: **6**
- Info notes: **1**
- Proposed corrections (not applied): **13**

## Strong findings

- `gemini_run3:ANAD-168551:FND-M-0004` (source_index=117, decision=drop): Rationale cites طهران/إيران metonym, but span/explanation are unrelated.
- `gemini_run3:ANAD-185945:FND-M-0003` (source_index=118, decision=drop): Rationale cites طهران/إيران metonym, but span/explanation are unrelated.
- `gemini_run3:ANAD-189478:FND-M-0003` (source_index=119, decision=drop): Rationale cites طهران/إيران metonym, but span/explanation are unrelated.
- `gemini_run3:ANAD-205601:FND-M-0002` (source_index=120, decision=drop): Rationale cites طهران/إيران metonym, but span/explanation are unrelated.
- `gemini_run3:ANAD-207095:FND-M-0004` (source_index=121, decision=drop): Rationale cites طهران/إيران metonym, but span/explanation are unrelated.
- `gemini_run3:ANAD-443448:FND-M-0003` (source_index=123, decision=drop): Rationale cites طهران/إيران metonym, but span/explanation are unrelated.
- `gemini_run3:SANAD-106974:FND-M-0005` (source_index=126, decision=drop): Rationale cites طهران/إيران metonym, but span/explanation are unrelated.
- `gemini_run3:SANAD-110453:FND-M-0002` (source_index=127, decision=drop): Rationale cites طهران/إيران metonym, but span/explanation are unrelated.
- `gemini_run3:ANAD-015348:FND-AI-0001` (source_index=40, decision=keep): Keep treats invite-gated availability as a material contradiction; closer to certainty escalation.
- `gemini_run3:ANAD-392361:FND-AI-1` (source_index=128, decision=keep): Numeric keep likely false: 3 remaining wins vs 8 achieved streak.
- `gemini_run3:ANAD-392361:FND-AI-4` (source_index=129, decision=keep): Numeric keep likely false: 3 remaining wins vs 8 achieved streak.
- `gemini_run3:ANAD-439722:FND-AI-0002` (source_index=60, decision=drop): Dropped as compression, but explanation alleges misleading full vs partial scope.

## Review flags

- `gemini_run3:SANAD-083088:FND-AI-0003` (source_index=50, decision=keep): Keep with suggestion that may alter certainty/attribution/meaning: ويرى مراقبون أن التمديد للأمير بندر جاء لإسكات الشائعات التي أطلقتها الصحافة الغربية مؤخرا عن السفير السعودي السابق لدى 
- `gemini_run3:ANAD-370725:FND-AI-0001` (source_index=146, decision=keep): Keep with suggestion that may alter certainty/attribution/meaning: ستاندرد آند بورز تتوقع تجاوز صافي أصول أبوظبي 200 % من الناتج المحلي حتى 2020
- `gemini_run3:SANAD-122948:FND-AI-0001` (source_index=104, decision=drop): Publisher-voice evaluative language ('فظاعة' / 'آلة الحرب') may be a real neutrality issue on some desks.
- `gemini_run3:ANAD-081530:FND-M-0001` (source_index=69, decision=drop): Arabic/Latin numeral mixing dropped as style; usually acceptable, keep as drop.
- `gemini_run3:ANAD-139392:FND-M-0002` (source_index=71, decision=drop): Arabic/Latin numeral mixing dropped as style; usually acceptable, keep as drop.
- `gemini_run3:ANAD-147096:FND-M-0001` (source_index=72, decision=drop): Arabic/Latin numeral mixing dropped as style; usually acceptable, keep as drop.

## Duplicate inventory

All exact duplicate groups currently share the same decision within each group (no inconsistent duplicate labeling detected).

- indices `10, 11` · `SANAD-036358` / `attribution` / `وسائل إعلام` · decisions=['drop']
- indices `12, 13` · `SANAD-042391` / `attribution` / `وسائل إعلام` · decisions=['drop']
- indices `27, 28` · `SANAD-025580` / `attribution` / `مصادر مطلعة` · decisions=['drop']
- indices `29, 30` · `SANAD-040837` / `attribution` / `مصادر مطلعة` · decisions=['drop']
- indices `31, 32` · `SANAD-068491` / `attribution` / `مصادر مطلعة` · decisions=['drop']
- indices `34, 35` · `SANAD-071296` / `attribution` / `مصادر مطلعة` · decisions=['drop']
- indices `36, 37` · `SANAD-080601` / `attribution` / `مصادر مطلعة` · decisions=['drop']
- indices `38, 39` · `SANAD-089298` / `attribution_strength` / `أكد أن` · decisions=['drop']
- indices `149, 150` · `SANAD-074502` / `spelling` / `مليشيات` · decisions=['drop']
- indices `154, 157` · `SANAD-122948` / `spelling` / `الاسرائيلية` · decisions=['drop']
- indices `155, 158` · `SANAD-122948` / `spelling` / `الاسرائيلي` · decisions=['drop']
- indices `156, 159` · `SANAD-122948` / `spelling` / `اسرائيل` · decisions=['drop']

## Keep suggestions that alter certainty/attribution/meaning

- `gemini_run3:SANAD-083088:FND-AI-0003` keep suggestion `ويرى مراقبون أن التمديد للأمير بندر جاء لإسكات الشائعات التي أطلقتها الصحافة الغربية مؤخرا عن السفير السعودي السابق لدى واشنطن.` (category=publisher_voice)
- `gemini_run3:ANAD-370725:FND-AI-0001` keep suggestion `ستاندرد آند بورز تتوقع تجاوز صافي أصول أبوظبي 200 % من الناتج المحلي حتى 2020` (category=unsupported_certainty)

## Proposed corrections

See `proposed_label_corrections.jsonl`. These rows are proposals for human review; they do **not** modify `expert_labels.jsonl` or scored precision.

## Method notes

- Checked all 163 rows for rationale/template mismatch, quote rewrite risk, duplicate consistency, suspicious keep numeric/headline cases, and drops that may hide overstatement.
- Distinguishes `strong` proposed corrections from `review` flags.
- AI suggests; editors decide.

## Deep-audit merge

Additional strong proposals merged from independent deep audit (si 47, 49, 50, 59); si 40 confidence raised. Labels still unchanged.
