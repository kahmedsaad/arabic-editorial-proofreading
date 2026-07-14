"""Post-process Gemini findings: gates, dedupe, quote preserve, category normalize."""

from __future__ import annotations

from app.models.schemas import Decision, Finding, FindingSource, Segment, Severity

_QUOTE_CHARS = "«»\"“”‘’'"

# Category-specific show thresholds (Sprint 1 — calibrate on tuning set)
_CATEGORY_THRESHOLDS: dict[str, float] = {
    "numeric_contradiction": 0.70,
    "temporal_contradiction": 0.70,
    "entity_confusion": 0.75,
    "spelling": 0.90,
    "grammar": 0.90,
    "headline_body_mismatch": 0.80,
    "loaded_framing": 0.90,
    "publisher_voice": 0.88,
    "unsupported_certainty": 0.88,
    "attribution": 0.92,
    "attribution_strength": 0.92,
    "source_quality": 0.92,
    "quote_voice": 0.95,
    "claim_contradiction": 0.85,
    "cross_paragraph_contradiction": 0.85,
    "legal_contradiction": 0.80,
    "defamation": 0.88,
    "implicit_blame": 0.88,
}

_CONF_HIGH = 0.75
_CONF_MEDIUM = 0.85
_CONF_LOW = 0.92

_HIGH_RISK = {
    "publisher_voice",
    "unsupported_certainty",
    "loaded_framing",
    "headline_body_mismatch",
    "numeric_contradiction",
    "legal_contradiction",
    "source_misrepresentation",
    "defamation",
    "implicit_blame",
}
_MEDIUM_RISK = {
    "attribution",
    "attribution_strength",
    "source_quality",
    "entity_confusion",
    "pronoun_ambiguity",
    "majority_precision",
    "claim_contradiction",
    "temporal_contradiction",
    "cross_paragraph_contradiction",
}

_CATEGORY_NORMALIZE = {
    "consistency": "claim_contradiction",
    "numbers": "numeric_contradiction",
    "date": "temporal_contradiction",
    "name": "entity_confusion",
}


def normalize_category(category: str) -> str:
    key = (category or "").strip().lower()
    return _CATEGORY_NORMALIZE.get(key, category)


def _inside_quotes(text: str, start: int, end: int) -> bool:
    before = text[:start]
    toggles = sum(1 for ch in before if ch in _QUOTE_CHARS)
    if toggles % 2 == 1:
        return True
    left = max((before.rfind(ch) for ch in "«\"“‘"), default=-1)
    if left < 0:
        return False
    after = text[end:]
    return any(ch in after for ch in "»\"”’")


def _span_overlap(a: str, b: str) -> float:
    sa = set((a or "").strip().lower().split())
    sb = set((b or "").strip().lower().split())
    if not sa or not sb:
        na, nb = (a or "").strip().lower(), (b or "").strip().lower()
        if not na or not nb:
            return 0.0
        if na in nb or nb in na:
            return 0.8
        return 0.0
    return len(sa & sb) / len(sa | sb)


def confidence_threshold_for_category(category: str, severity: Severity) -> float:
    """Category-specific floors; severity can only raise the bar."""
    cat = normalize_category(category or "").lower()
    base = _CATEGORY_THRESHOLDS.get(cat)
    if base is None:
        if cat in _HIGH_RISK or severity in {Severity.HIGH, Severity.CRITICAL}:
            base = _CONF_HIGH
        elif cat in _MEDIUM_RISK or severity == Severity.MEDIUM:
            base = _CONF_MEDIUM
        else:
            base = _CONF_LOW
    if severity in {Severity.HIGH, Severity.CRITICAL}:
        return max(base, 0.70)
    if severity == Severity.LOW and cat in {
        "attribution",
        "quote_voice",
        "source_quality",
    }:
        return max(base, 0.94)
    return base


def _confidence_threshold(category: str, severity: Severity) -> float:
    return confidence_threshold_for_category(category, severity)


def _has_editorial_risk_language(explanation: str) -> bool:
    text = (explanation or "").strip()
    if len(text) < 12:
        return False
    markers = (
        "تحريض",
        "اتهام",
        "تناقض",
        "تعارض",
        "نسبة",
        "إسناد",
        "اقتباس",
        "عنوان",
        "دليل",
        "غير مثبت",
        "صوت الناشر",
        "مخالفة",
        "خطأ",
        "يحاجة",
        "يحتاج",
        "مراجعة",
    )
    return any(m in text for m in markers) or len(text) >= 24


def validate_gemini_finding(
    finding: Finding,
    *,
    segments_by_id: dict[str, Segment],
    mechanical: list[Finding],
) -> tuple[bool, str]:
    if finding.source != FindingSource.GEMINI:
        return True, "not_gemini"

    finding.category = normalize_category(finding.category)

    span = (finding.original_text or "").strip()
    if not span:
        return False, "missing_span"

    segment = segments_by_id.get(finding.segment_id)
    if segment is None:
        return False, "missing_segment"
    if span not in segment.text:
        return False, "span_not_in_segment"

    # Prefer exact offsets; repair if needed.
    if (
        finding.start_offset < 0
        or finding.end_offset <= finding.start_offset
        or segment.text[finding.start_offset : finding.end_offset] != span
    ):
        idx = segment.text.find(span)
        if idx < 0:
            return False, "span_offset_mismatch"
        finding.start_offset = idx
        finding.end_offset = idx + len(span)

    thr = confidence_threshold_for_category(finding.category, finding.severity)
    if finding.confidence < thr:
        return False, f"confidence_below_{thr}"

    if not _has_editorial_risk_language(finding.explanation_ar):
        return False, "weak_explanation"

    # Covered by mechanical/editorial deterministic finding?
    for prior in mechanical:
        if _span_overlap(prior.original_text, span) >= 0.6:
            return False, "covered_by_mechanical"

    # Properly attributed quote: do not rewrite / hard-flag quote-only style.
    if _inside_quotes(segment.text, finding.start_offset, finding.end_offset):
        # Allow soft review only for terror/loaded labels; drop replace/ban.
        if finding.decision in {Decision.REPLACE, Decision.BAN}:
            finding.decision = Decision.NEEDS_EDITOR_REVIEW
            finding.suggested_text = None
        # Drop low-value attribution nags inside quotes.
        if finding.category in {"attribution", "quote_voice"} and finding.confidence < 0.95:
            return False, "attributed_quote_low_value"
        if finding.suggested_text:
            finding.suggested_text = None

    return True, "ok"


def gate_gemini_findings(
    *,
    gemini_findings: list[Finding],
    mechanical_findings: list[Finding],
    segments: list[Segment],
) -> tuple[list[Finding], list[Finding]]:
    """Return (kept, rejected_by_gate). Structural + confidence gate before adjudicator."""
    by_id = {s.segment_id: s for s in segments}
    kept: list[Finding] = []
    rejected: list[Finding] = []
    for finding in gemini_findings:
        ok, _reason = validate_gemini_finding(
            finding, segments_by_id=by_id, mechanical=mechanical_findings
        )
        if ok:
            kept.append(finding)
        else:
            rejected.append(
                finding.model_copy(
                    update={
                        "validation_errors": list(finding.validation_errors)
                        + [f"gemini_gate:{_reason}"]
                    }
                )
            )
    return kept, rejected


def segments_for_gemini(segments: list[Segment], prior_findings: list[Finding]) -> list[Segment]:
    """Router: send headline + semantic/editorial body; skip plain deterministic-only lines."""
    semantic_markers = (
        "قال",
        "قالت",
        "أكد",
        "بحسب",
        "مصادر",
        "يبدو",
        "ويؤكد",
        "رغم",
        "بينما",
        "من جانبه",
        "«",
        "»",
        "أعلن",
        "أضافت",
        "نفى",
        "اتهم",
    )
    prior_seg_ids = {f.segment_id for f in prior_findings}
    selected: list[Segment] = []
    for segment in segments:
        if segment.zone.value == "headline":
            selected.append(segment)
            continue
        text = segment.text
        if segment.segment_id in prior_seg_ids:
            selected.append(segment)
            continue
        if any(m in text for m in semantic_markers):
            selected.append(segment)
            continue
        # Skip short purely numeric/status lines without speech/attribution cues.
        if len(text) < 80 and not any(ch.isdigit() for ch in text):
            continue
        if any(ch.isdigit() for ch in text) and any(
            k in text for k in ("%", "مليون", "ألف", "أغلبية", "من أصل")
        ):
            selected.append(segment)
    if len(selected) < 2:
        return segments[: min(3, len(segments))] or segments
    return selected
