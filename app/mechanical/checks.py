import json
from pathlib import Path

import regex as re

from app.models.schemas import Decision, Finding, FindingSource, Segment, Severity

_WORD_RE = re.compile(r"\S+")
_AR_PUNCT = r".,:;!?،؛؟"
_SPACE_BEFORE_PUNCT = re.compile(rf"\s+([{_AR_PUNCT}])")
_MISSING_SPACE_AFTER_PUNCT = re.compile(rf"([{_AR_PUNCT}])(?=[^\s{_AR_PUNCT}\d])")
_REPEATED_PUNCT = re.compile(rf"([{_AR_PUNCT}])\1+")
_REPEATED_WS = re.compile(r"[^\S\n]{2,}|\n{3,}")
_LETTER_VARIANTS = [
    ("أ", "ا"),
    ("إ", "ا"),
    ("آ", "ا"),
]
_QUOTE_CHARS = "\"'«»“”‘’"
_MIXED_DIGITS = re.compile(r"[0-9٠-٩۰-۹]")
_ARABIC_DIGITS = re.compile(r"[٠-٩۰-۹]")
_LATIN_DIGITS = re.compile(r"[0-9]")


def _finding(
    *,
    finding_id: str,
    segment: Segment,
    category: str,
    original_text: str,
    start: int,
    end: int,
    explanation_ar: str,
    suggested_text: str | None,
    rule_ids: list[str],
    severity: Severity = Severity.MEDIUM,
    decision: Decision = Decision.REPLACE,
) -> Finding:
    return Finding(
        finding_id=finding_id,
        document_id=segment.document_id,
        segment_id=segment.segment_id,
        source=FindingSource.MECHANICAL,
        category=category,
        decision=decision,
        severity=severity,
        original_text=original_text,
        suggested_text=suggested_text,
        start_offset=start,
        end_offset=end,
        rule_ids=rule_ids,
        explanation_ar=explanation_ar,
        confidence=1.0,
        requires_editor_review=severity in {Severity.HIGH, Severity.CRITICAL},
    )


def load_spelling_replacements(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in data.items()}


def check_duplicate_adjacent_words(segment: Segment, counter: list[int]) -> list[Finding]:
    findings: list[Finding] = []
    matches = list(_WORD_RE.finditer(segment.text))
    for prev, curr in zip(matches, matches[1:], strict=False):
        if prev.group() == curr.group():
            counter[0] += 1
            findings.append(
                _finding(
                    finding_id=f"FND-M-{counter[0]:04d}",
                    segment=segment,
                    category="repetition",
                    original_text=f"{prev.group()} {curr.group()}",
                    start=prev.start(),
                    end=curr.end(),
                    explanation_ar="تكرار كلمة متجاورة.",
                    suggested_text=prev.group(),
                    rule_ids=["MECH-DUP-WORD"],
                )
            )
    return findings


def check_repeated_whitespace(segment: Segment, counter: list[int]) -> list[Finding]:
    findings: list[Finding] = []
    for match in _REPEATED_WS.finditer(segment.text):
        counter[0] += 1
        findings.append(
            _finding(
                finding_id=f"FND-M-{counter[0]:04d}",
                segment=segment,
                category="punctuation",
                original_text=match.group(),
                start=match.start(),
                end=match.end(),
                explanation_ar="مسافات بيضاء مكررة.",
                suggested_text=" " if "\n" not in match.group() else "\n\n",
                rule_ids=["MECH-WS"],
                severity=Severity.LOW,
                decision=Decision.SUGGEST,
            )
        )
    return findings


def check_spacing_before_punctuation(segment: Segment, counter: list[int]) -> list[Finding]:
    findings: list[Finding] = []
    for match in _SPACE_BEFORE_PUNCT.finditer(segment.text):
        counter[0] += 1
        punct = match.group(1)
        findings.append(
            _finding(
                finding_id=f"FND-M-{counter[0]:04d}",
                segment=segment,
                category="punctuation",
                original_text=match.group(),
                start=match.start(),
                end=match.end(),
                explanation_ar="مسافة غير صحيحة قبل علامة الترقيم.",
                suggested_text=punct,
                rule_ids=["MECH-PUNCT-SPACE"],
                severity=Severity.LOW,
                decision=Decision.REPLACE,
            )
        )
    return findings


def check_repeated_punctuation(segment: Segment, counter: list[int]) -> list[Finding]:
    findings: list[Finding] = []
    for match in _REPEATED_PUNCT.finditer(segment.text):
        counter[0] += 1
        findings.append(
            _finding(
                finding_id=f"FND-M-{counter[0]:04d}",
                segment=segment,
                category="punctuation",
                original_text=match.group(),
                start=match.start(),
                end=match.end(),
                explanation_ar="تكرار غير ضروري لعلامة الترقيم.",
                suggested_text=match.group(1),
                rule_ids=["MECH-PUNCT-DUP"],
                severity=Severity.LOW,
                decision=Decision.REPLACE,
            )
        )
    return findings


def check_spelling_replacements(
    segment: Segment,
    counter: list[int],
    replacements: dict[str, str],
) -> list[Finding]:
    findings: list[Finding] = []
    if not replacements:
        return findings

    # Longer keys first to prefer specific phrases
    for wrong in sorted(replacements.keys(), key=len, reverse=True):
        start = 0
        while True:
            idx = segment.text.find(wrong, start)
            if idx < 0:
                break
            end = idx + len(wrong)
            counter[0] += 1
            findings.append(
                _finding(
                    finding_id=f"FND-M-{counter[0]:04d}",
                    segment=segment,
                    category="spelling",
                    original_text=wrong,
                    start=idx,
                    end=end,
                    explanation_ar="استبدال إملائي معروف.",
                    suggested_text=replacements[wrong],
                    rule_ids=["MECH-SPELL"],
                )
            )
            start = end
    return findings


def check_missing_space_after_punctuation(segment: Segment, counter: list[int]) -> list[Finding]:
    findings: list[Finding] = []
    for match in _MISSING_SPACE_AFTER_PUNCT.finditer(segment.text):
        counter[0] += 1
        punct = match.group(1)
        findings.append(
            _finding(
                finding_id=f"FND-M-{counter[0]:04d}",
                segment=segment,
                category="punctuation",
                original_text=punct,
                start=match.start(),
                end=match.end(),
                explanation_ar="تنقص مسافة بعد علامة الترقيم.",
                suggested_text=f"{punct} ",
                rule_ids=["MECH-PUNCT-AFTER"],
                severity=Severity.LOW,
                decision=Decision.SUGGEST,
            )
        )
    return findings


def check_common_letter_variants(segment: Segment, counter: list[int]) -> list[Finding]:
    """Soft warnings for Alef variants mixed with bare Alef in the same segment."""
    has_bare = "ا" in segment.text
    if not has_bare:
        return []
    for variant, _canonical in _LETTER_VARIANTS:
        match = re.search(re.escape(variant), segment.text)
        if match:
            counter[0] += 1
            return [
                _finding(
                    finding_id=f"FND-M-{counter[0]:04d}",
                    segment=segment,
                    category="spelling",
                    original_text=variant,
                    start=match.start(),
                    end=match.end(),
                    explanation_ar="اختلاف أشكال الألف داخل المقطع؛ للمطابقة فقط.",
                    suggested_text=None,
                    rule_ids=["MECH-LETTER-VAR"],
                    severity=Severity.LOW,
                    decision=Decision.SOFT_WARNING,
                )
            ]
    return []


def check_quotation_consistency(segment: Segment, counter: list[int]) -> list[Finding]:
    """Validate quote pairs; do not flag correctly paired «...» or curly quotes.

    A finding is emitted only when an opener is missing its closer, a closer
    appears without an opener, or a closer mismatches the open pair type.
    """
    open_to_close = {
        "«": "»",
        "“": "”",
        "‘": "’",
        '"': '"',
        "'": "'",
    }
    close_to_open = {v: k for k, v in open_to_close.items() if k != v}
    # Ambiguous ASCII quotes toggle.
    ascii_toggle = {'"', "'"}

    stack: list[tuple[str, int]] = []
    problem_idx: int | None = None
    problem_ch: str | None = None
    reason = ""

    for i, ch in enumerate(segment.text):
        if ch in open_to_close and ch not in ascii_toggle:
            stack.append((ch, i))
            continue
        if ch in close_to_open:
            if not stack:
                problem_idx, problem_ch, reason = i, ch, "علامة إغلاق اقتباس دون فتح مطابق."
                break
            opener, _ = stack.pop()
            if open_to_close.get(opener) != ch:
                problem_idx, problem_ch, reason = i, ch, "عدم تطابق زوج علامات الاقتباس."
                break
            continue
        if ch in ascii_toggle:
            if stack and stack[-1][0] == ch:
                stack.pop()
            else:
                stack.append((ch, i))

    if problem_idx is None and stack:
        opener, idx = stack[-1]
        problem_idx, problem_ch, reason = idx, opener, "علامة فتح اقتباس دون إغلاق مطابق."

    if problem_idx is None or problem_ch is None:
        return []

    counter[0] += 1
    return [
        _finding(
            finding_id=f"FND-M-{counter[0]:04d}",
            segment=segment,
            category="punctuation",
            original_text=problem_ch,
            start=problem_idx,
            end=problem_idx + 1,
            explanation_ar=reason or "خلل في أزواج علامات الاقتباس.",
            suggested_text=None,
            rule_ids=["MECH-QUOTE"],
            severity=Severity.LOW,
            decision=Decision.SOFT_WARNING,
        )
    ]


def check_digit_script_consistency(segment: Segment, counter: list[int]) -> list[Finding]:
    if _ARABIC_DIGITS.search(segment.text) and _LATIN_DIGITS.search(segment.text):
        match = _MIXED_DIGITS.search(segment.text)
        if not match:
            return []
        counter[0] += 1
        return [
            _finding(
                finding_id=f"FND-M-{counter[0]:04d}",
                segment=segment,
                category="clarity",
                original_text=match.group(),
                start=match.start(),
                end=match.end(),
                explanation_ar="خلط بين الأرقام العربية واللاتينية في المقطع.",
                suggested_text=None,
                rule_ids=["MECH-DIGITS"],
                severity=Severity.LOW,
                decision=Decision.SOFT_WARNING,
            )
        ]
    return []


def check_malformed_segment(segment: Segment, counter: list[int]) -> list[Finding]:
    text = segment.text.strip()
    if not text:
        return []
    if len(text) > 2000:
        counter[0] += 1
        return [
            _finding(
                finding_id=f"FND-M-{counter[0]:04d}",
                segment=segment,
                category="clarity",
                original_text=text[:20],
                start=0,
                end=20,
                explanation_ar="مقطع طويل جداً قد يحتاج إعادة تقسيم.",
                suggested_text=None,
                rule_ids=["MECH-MALFORMED"],
                severity=Severity.LOW,
                decision=Decision.SOFT_WARNING,
            )
        ]
    return []


def check_entity_spellings(
    segment: Segment,
    counter: list[int],
    entity_aliases: dict[str, tuple[str, str]],
) -> list[Finding]:
    """entity_aliases maps alias -> (canonical, entity_id)."""
    findings: list[Finding] = []
    for alias, (canonical, entity_id) in sorted(
        entity_aliases.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if alias == canonical:
            continue
        start = 0
        while True:
            idx = segment.text.find(alias, start)
            if idx < 0:
                break
            end = idx + len(alias)
            counter[0] += 1
            finding = _finding(
                finding_id=f"FND-M-{counter[0]:04d}",
                segment=segment,
                category="entity_name",
                original_text=alias,
                start=idx,
                end=end,
                explanation_ar="صيغة غير معتمدة لاسم الكيان.",
                suggested_text=canonical,
                rule_ids=["MECH-ENTITY"],
            )
            finding.entity_ids = [entity_id]
            findings.append(finding)
            start = end
    return findings


def check_inconsistent_entity_spelling(
    segments: list[Segment],
    counter: list[int],
    entity_forms: dict[str, list[str]],
) -> list[Finding]:
    """Flag when multiple aliases for same entity appear in one article."""
    findings: list[Finding] = []
    joined = "\n".join(s.text for s in segments)
    for entity_id, forms in entity_forms.items():
        present = [form for form in forms if form in joined]
        unique = list(dict.fromkeys(present))
        if len(unique) < 2:
            continue
        # Point at first occurrence of the non-canonical (second) form
        form = unique[1]
        for segment in segments:
            idx = segment.text.find(form)
            if idx < 0:
                continue
            counter[0] += 1
            finding = _finding(
                finding_id=f"FND-M-{counter[0]:04d}",
                segment=segment,
                category="entity_name",
                original_text=form,
                start=idx,
                end=idx + len(form),
                explanation_ar="تهجئة غير متسقة لنفس الكيان داخل المقال.",
                suggested_text=unique[0],
                rule_ids=["MECH-ENTITY-INCONSISTENT"],
                severity=Severity.MEDIUM,
                decision=Decision.SOFT_WARNING,
            )
            finding.entity_ids = [entity_id]
            findings.append(finding)
            break
    return findings


def run_mechanical_checks(
    segments: list[Segment],
    spelling_replacements: dict[str, str] | None = None,
    *,
    entity_aliases: dict[str, tuple[str, str]] | None = None,
    entity_forms: dict[str, list[str]] | None = None,
    enable_letter_variant_warnings: bool = False,
) -> list[Finding]:
    replacements = spelling_replacements or {}
    aliases = entity_aliases or {}
    forms = entity_forms or {}
    counter = [0]
    findings: list[Finding] = []
    for segment in segments:
        findings.extend(check_duplicate_adjacent_words(segment, counter))
        findings.extend(check_repeated_whitespace(segment, counter))
        findings.extend(check_spacing_before_punctuation(segment, counter))
        findings.extend(check_missing_space_after_punctuation(segment, counter))
        findings.extend(check_repeated_punctuation(segment, counter))
        findings.extend(check_spelling_replacements(segment, counter, replacements))
        if enable_letter_variant_warnings:
            findings.extend(check_common_letter_variants(segment, counter))
        findings.extend(check_quotation_consistency(segment, counter))
        findings.extend(check_digit_script_consistency(segment, counter))
        findings.extend(check_malformed_segment(segment, counter))
        findings.extend(check_entity_spellings(segment, counter, aliases))
    findings.extend(check_inconsistent_entity_spelling(segments, counter, forms))
    return findings
