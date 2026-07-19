"""Deterministic run5 editorial precision gates (R1, R2, R4 only)."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Any

from app.models.schemas import ArticleContext, Finding, FindingSource, Segment, Zone

POLICY_OFF = "off"
POLICY_RUN5 = "run5"
POLICY_RUN5B = "run5b"

ATTRIBUTION_REASON = "attribution_vague_or_already_attributed"
CLARITY_REASON = "clarity_generic_no_concrete_defect"
HEADLINE_REASON = "headline_supported_compression"

_ATTRIBUTION_CATEGORIES = {"attribution", "attribution_strength", "source_quality"}
_HEADLINE_CATEGORIES = {
    "headline_body_mismatch",
    "headline_framing",
    "unsupported_certainty",
    "publisher_voice",
}

# Frozen Run5 constants. Do not change: run5b has separate safety logic below.
_RUN5_VAGUE_SOURCE_MARKERS = (
    "مصدر مبهم",
    "مصدر غامض",
    "مصدر غير محدد",
    "مصدر غير مسمى",
    "مصدر غير مسمّى",
    "إسناد مبهم",
    "إسناد غامض",
    "مصادر مبهمة",
    "مصادر غير محددة",
    "مصادر غير مسماة",
    "مصادر غير مسمّاة",
)
_RUN5_VAGUE_SOURCE_SPANS = (
    "مصادر",
    "المصادر",
    "وسائل إعلام",
    "وسائل الاعلام",
    "وكالات",
    "مراقبون",
    "تقارير صحفية",
)
_RUN5_MATERIAL_UNATTRIBUTED_MARKERS = (
    "دون مصدر",
    "دون ذكر مصدر",
    "دون إسناد",
    "بلا مصدر",
    "غير منسوب",
    "غير مسند",
    "لم يُنسب",
    "لم ينسب",
    "لا ينسب",
    "صوت الناشر",
    "يفتقر إلى مصدر",
    "ادعاء غير مسند",
)
_RUN5_GENERIC_CLARITY_MARKERS = (
    "مقطع طويل",
    "فقرة طويلة",
    "إعادة تقسيم",
    "تقسيم الفقرة",
    "تبسيط الصياغة",
    "تحسين الوضوح",
    "يفضل توضيح",
    "يُفضل توضيح",
    "يفضّل توضيح",
    "بحاجة إلى توضيح",
    "قد يحتاج توضيح",
    "عنوان غير وصفي",
    "يفتقر إلى المعلومات الأساسية",
)
_RUN5_CONCRETE_CLARITY_MARKERS = (
    "مرجع الضمير",
    "مرجع الإشارة",
    "مرجع واضح",
    "ضمير غامض",
    "يعود الضمير",
    "المقصود بـ",
    "من المقصود",
    "التباس بين",
    "ملتبس بين",
    "يتناقض",
    "تناقض",
    "تعارض",
    "غير مكتمل",
    "جملة ناقصة",
    "مفقود",
)
_RUN5_HEADLINE_STYLE_MARKERS = (
    "مستوى اليقين",
    "تصعيد في اليقين",
    "تصعيدًا في اليقين",
    "تصعيدا في اليقين",
    "حقيقة مؤكدة",
    "بصوت الناشر",
    "نسبة القول",
    "الحفاظ على نسبة",
    "مستند إلى مصدر",
    "بشكل قاطع",
    "ليس إعلاناً رسمياً",
    "مصادر",
    "ربما",
    "توقع",
    "تتوقع",
    "قد ",
)
_RUN5_HEADLINE_MATERIAL_MARKERS = (
    "تناقض عددي",
    "يتعارض العدد",
    "عدد ",
    "رقم ",
    "نسبة ",
    "تاريخ",
    "مكان",
    "موقع جغرافي",
    "هولندا",
    "النمسا",
    "إطلاق سراح",
    "محتجز",
    "توقف",
    "نفى",
    "نفي",
    "انتهت",
    "لم تحدث",
    "خسار",
    "فوز",
    "قتل",
    "وفاة",
    "كامل",
    "جزئي",
    "استثناء",
    "غير مدعوم",
    "لا يدعم",
    "لا يحتوي",
    "ادعاء غير",
    "مبالغة جوهرية",
)

_VAGUE_SOURCE_MARKERS = (
    "مصدر مبهم",
    "مصدر غامض",
    "مصدر غير محدد",
    "مصدر غير مسمى",
    "مصدر غير مسمّى",
    "إسناد مبهم",
    "إسناد غامض",
    "مصادر مبهمة",
    "مصادر غير محددة",
    "مصادر غير مسماة",
    "مصادر غير مسمّاة",
)
_VAGUE_SOURCE_SPANS = (
    "مصادر",
    "المصادر",
    "وسائل إعلام",
    "وسائل الاعلام",
    "وكالات",
    "مراقبون",
    "تقارير صحفية",
)
_MATERIAL_UNATTRIBUTED_MARKERS = (
    "دون مصدر",
    "دون ذكر مصدر",
    "دون إسناد",
    "بلا مصدر",
    "غير منسوب",
    "غير مسند",
    "لم يُنسب",
    "لم ينسب",
    "لا ينسب",
    "صوت الناشر",
    "يفتقر إلى مصدر",
    "ادعاء غير مسند",
)
_ATTRIBUTION_CERTAINTY_MARKERS = (
    "أكد",
    "تأكيد",
    "مؤكد",
    "يقين",
    "يبالغ في قوة",
    "قوة الادعاء",
    "درجة من اليقين",
    "حوّل احتمال",
    "يحول احتمال",
    "تصعيد",
)
_ATTRIBUTION_VERBS = re.compile(
    r"(?:قال|قالت|أفاد|أفادت|ذكر|ذكرت|بحسب|وفق|نقلت|أوضح|أوضحت|"
    r"أعلن|أعلنت|صرح|صرحت|مصادر|وكالة|تقرير)"
)

_GENERIC_CLARITY_MARKERS = (
    "مقطع طويل",
    "فقرة طويلة",
    "إعادة تقسيم",
    "تقسيم الفقرة",
    "تبسيط الصياغة",
    "تحسين الوضوح",
    "يفضل توضيح",
    "يُفضل توضيح",
    "يفضّل توضيح",
    "بحاجة إلى توضيح",
    "قد يحتاج توضيح",
    "عنوان غير وصفي",
    "يفتقر إلى المعلومات الأساسية",
)
_CONCRETE_CLARITY_MARKERS = (
    "مرجع الضمير",
    "مرجع الإشارة",
    "مرجع واضح",
    "ضمير غامض",
    "يعود الضمير",
    "المقصود بـ",
    "من المقصود",
    "التباس بين",
    "ملتبس بين",
    "يتناقض",
    "تناقض",
    "تعارض",
    "غير مكتمل",
    "جملة ناقصة",
    "مفقود",
    "خلط بين الأرقام",
    "غامض",
)

_HEADLINE_STYLE_MARKERS = (
    "مستوى اليقين",
    "تصعيد في اليقين",
    "تصعيدًا في اليقين",
    "تصعيدا في اليقين",
    "حقيقة مؤكدة",
    "بصوت الناشر",
    "نسبة القول",
    "الحفاظ على نسبة",
    "مستند إلى مصدر",
    "بشكل قاطع",
    "ليس إعلاناً رسمياً",
)
_HEADLINE_MATERIAL_MARKERS = (
    "يتناقض",
    "تناقض",
    "تعارض",
    "تضارب",
    "تناقض عددي",
    "يتعارض العدد",
    "عدد ",
    "رقم ",
    "تاريخ",
    "مكان",
    "موقع جغرافي",
    "هولندا",
    "النمسا",
    "إطلاق سراح",
    "محتجز",
    "توقف",
    "نفى",
    "نفي",
    "انتهت",
    "لم تحدث",
    "خسار",
    "فوز",
    "قتل",
    "وفاة",
    "كامل",
    "جزئي",
    "استثناء",
    "غير مدعوم",
    "لا يدعم",
    "لا يحتوي",
    "ادعاء غير",
    "مبالغة جوهرية",
    "يضلل",
)
_HEADLINE_ESCALATION_MARKERS = (
    "احتمال",
    "ربما",
    "قد ",
    "متوقع",
    "توقع",
    "يبدو",
    "غير مؤكد",
    "غير رسمي",
    "إعلاناً رسمياً",
    "اعلانا رسميا",
    "رسمي",
    "مصادر",
)
_ARABIC_WORD = re.compile(r"[\u0600-\u06FF]+|[A-Za-z0-9]+")
_STOPWORDS = {
    "في",
    "من",
    "إلى",
    "على",
    "عن",
    "أن",
    "إن",
    "هو",
    "هي",
    "هذا",
    "هذه",
    "التي",
    "الذي",
    "مع",
    "بعد",
    "قبل",
}


def normalize_editorial_gate_policy(policy: str | None) -> str:
    value = (policy or POLICY_OFF).strip().lower()
    if value in {POLICY_RUN5, POLICY_RUN5B}:
        return value
    return POLICY_OFF


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    return any(marker in text for marker in markers)


def _normalize_arabic(text: str | None) -> str:
    """Normalize Arabic for gate matching without changing displayed content."""
    value = unicodedata.normalize("NFKC", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("ـ", "")
    value = value.translate(
        str.maketrans(
            {
                "أ": "ا",
                "إ": "ا",
                "آ": "ا",
                "ٱ": "ا",
                "ى": "ي",
                "ؤ": "و",
                "ئ": "ي",
            }
        )
    )
    return " ".join(value.lower().split())


def _token_set(text: str) -> set[str]:
    return {
        token.lower()
        for token in _ARABIC_WORD.findall(text or "")
        if len(token) >= 3 and token not in _STOPWORDS
    }


def _span_overlap(left: str, right: str) -> float:
    left_tokens = _token_set(left)
    right_tokens = _token_set(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens)


def _segment_window(finding: Finding, segments: list[Segment]) -> str:
    current = next((segment for segment in segments if segment.segment_id == finding.segment_id), None)
    if current is None:
        return ""
    nearby = [
        segment.text
        for segment in segments
        if segment.document_id == current.document_id
        and abs(segment.sequence - current.sequence) <= 1
    ]
    return " ".join(nearby)


def _run5_context_explicitly_attributes(
    finding: Finding,
    context: ArticleContext | None,
    segments: list[Segment],
) -> bool:
    """Frozen Run5 nearby-attribution behavior."""
    claim = finding.original_text or ""
    if context is not None:
        for link in context.attribution_links:
            if _span_overlap(claim, link.claim_span) >= 0.5 and (
                link.speaker or link.source_org or link.attribution_verb
            ):
                return True
    window = _segment_window(finding, segments)
    if not claim or not window:
        return False
    index = window.find(claim)
    if index < 0:
        return False
    local = window[max(0, index - 180) : min(len(window), index + len(claim) + 100)]
    return bool(_ATTRIBUTION_VERBS.search(local))


def _run5_r1_suppresses(
    finding: Finding,
    *,
    context: ArticleContext | None,
    segments: list[Segment],
) -> bool:
    explanation = finding.explanation_ar or ""
    original = finding.original_text or ""
    if _contains_any(explanation, _RUN5_MATERIAL_UNATTRIBUTED_MARKERS):
        return False
    vague_request = _contains_any(
        explanation, _RUN5_VAGUE_SOURCE_MARKERS
    ) or _contains_any(original, _RUN5_VAGUE_SOURCE_SPANS)
    return vague_request or _run5_context_explicitly_attributes(
        finding, context, segments
    )


def _run5_r2_suppresses(finding: Finding) -> bool:
    explanation = finding.explanation_ar or ""
    if _contains_any(explanation, _RUN5_CONCRETE_CLARITY_MARKERS):
        return False
    return _contains_any(explanation, _RUN5_GENERIC_CLARITY_MARKERS)


def _run5_r4_suppresses(finding: Finding, *, segments: list[Segment]) -> bool:
    explanation = finding.explanation_ar or ""
    if _contains_any(explanation, _RUN5_HEADLINE_MATERIAL_MARKERS):
        return False
    if not _contains_any(explanation, _RUN5_HEADLINE_STYLE_MARKERS):
        return False
    body = _headline_body_text(segments)
    if not body:
        return False
    core_supported = _span_overlap(finding.original_text, body) >= 0.25
    source_supported = _contains_any(
        explanation,
        ("المتن", "النص", "مصدر", "تقرير", "توقع", "ربما", "بحسب"),
    ) and bool(_ATTRIBUTION_VERBS.search(body))
    return core_supported or source_supported


def _run5b_context_explicitly_attributes(
    finding: Finding,
    context: ArticleContext | None,
    segments: list[Segment],
) -> bool:
    """True only when a claim already has attribution beyond the finding span itself."""
    claim = (finding.original_text or "").strip()
    if not claim:
        return False
    # Confirmation/attribution verbs under review are not themselves proof of prior attribution.
    if _contains_any(claim, _ATTRIBUTION_CERTAINTY_MARKERS) or _ATTRIBUTION_VERBS.fullmatch(claim):
        return False
    if context is not None:
        for link in context.attribution_links:
            if _span_overlap(claim, link.claim_span) >= 0.5 and (
                link.speaker or link.source_org or link.attribution_verb
            ):
                return True
    window = _segment_window(finding, segments)
    if not window:
        return False
    index = window.find(claim)
    if index < 0:
        return False
    before = window[max(0, index - 180) : index]
    # Require an attribution cue before the claim, not inside the claim span.
    return bool(_ATTRIBUTION_VERBS.search(before))


def _run5b_r1_suppresses(
    finding: Finding,
    *,
    context: ArticleContext | None,
    segments: list[Segment],
) -> bool:
    explanation = finding.explanation_ar or ""
    original = finding.original_text or ""
    category = (finding.category or "").strip().lower()

    # Fail open: material unattributed publisher claims stay visible.
    if _contains_any(explanation, _MATERIAL_UNATTRIBUTED_MARKERS):
        return False
    # Fail open: attribution-strength / certainty-escalation findings stay visible.
    if category == "attribution_strength" or _contains_any(
        explanation, _ATTRIBUTION_CERTAINTY_MARKERS
    ):
        return False

    vague_request = _contains_any(explanation, _VAGUE_SOURCE_MARKERS) or _contains_any(
        original, _VAGUE_SOURCE_SPANS
    )
    if vague_request:
        return True
    return _run5b_context_explicitly_attributes(finding, context, segments)


def _run5b_r2_suppresses(finding: Finding) -> bool:
    explanation = _normalize_arabic(finding.explanation_ar)
    concrete_markers = tuple(_normalize_arabic(m) for m in _CONCRETE_CLARITY_MARKERS) + (
        "مرجع",
        "ضمير",
        "كيان",
        "اسم شخص",
        "اسم منظمه",
        "مكان",
        "مدينه",
        "دوله",
        "دور",
        "صفه",
        "فاعل",
        "مفعول",
        "نفي",
        "يقين",
        "احتمال",
        "اسناد",
        "نسبه القول",
        "اقتباس",
        "قول مباشر",
        "معني",
        "رقم",
        "عدد",
        "تاريخ",
        "موعد",
        "نسبه ميويه",
    )
    if _contains_any(explanation, concrete_markers):
        return False
    if any(ch.isdigit() for ch in (finding.original_text or "") + explanation):
        return False
    if finding.suggested_text and _normalize_arabic(
        finding.suggested_text
    ) != _normalize_arabic(finding.original_text):
        return False
    generic_markers = tuple(_normalize_arabic(m) for m in _GENERIC_CLARITY_MARKERS) + (
        "الجمله طويله",
        "العباره طويله",
        "النص طويل",
        "صياغه اوضح",
        "يمكن توضيح الصياغه",
        "صعب القراءه",
        "صعوبه القراءه",
        "تسهيل القراءه",
        "يفضل التبسيط",
        "يمكن تبسيط",
        "صياغه معقده",
    )
    return _contains_any(explanation, generic_markers)


def _headline_body_text(segments: list[Segment]) -> str:
    return " ".join(segment.text for segment in segments if segment.zone != Zone.HEADLINE)


def _run5b_r4_suppresses(finding: Finding, *, segments: list[Segment]) -> bool:
    """Suppress only positively identified, semantically safe compression."""
    explanation = _normalize_arabic(finding.explanation_ar)
    original = finding.original_text or ""
    suggested = finding.suggested_text or ""

    # Structured fail-open paths: changed content, numbers/dates, and quotation meaning.
    if suggested and _normalize_arabic(suggested) != _normalize_arabic(original):
        return False
    if any(ch.isdigit() for ch in original + suggested + explanation):
        return False
    if finding.quotation_status is not None and suggested:
        return False

    safe_compression_markers = tuple(
        _normalize_arabic(marker)
        for marker in (
            "اختصار أسلوبي",
            "اختصار العنوان",
            "ضغط العنوان",
            "العنوان يختصر صياغة المتن",
            "يختصر صياغة المتن",
            "حذف نسبة القول فقط",
            "الحفاظ على نسبة القول فقط",
            "فرق أسلوبي فقط",
            "لا يغير المعنى",
        )
    )
    matched_safe = [marker for marker in safe_compression_markers if marker in explanation]
    material_text = explanation
    for marker in matched_safe:
        material_text = material_text.replace(marker, " ")

    material_markers = tuple(
        _normalize_arabic(marker)
        for marker in (
            *_HEADLINE_MATERIAL_MARKERS,
            *_HEADLINE_ESCALATION_MARKERS,
            "يتناقض",
            "تناقض",
            "تعارض",
            "تضارب",
            "اختلاف",
            "كيان",
            "شخص",
            "منظمة",
            "منظمه",
            "شركة",
            "شركه",
            "نادي",
            "دولة",
            "دوله",
            "مدينة",
            "مدينه",
            "مكان",
            "موقع",
            "دور",
            "صفة",
            "صفه",
            "فاعل",
            "مفعول",
            "عكس",
            "قلب",
            "نتيجة",
            "نتيجه",
            "حدث",
            "نفي",
            "ليس",
            "لم ",
            "لن ",
            "يقين",
            "مؤكد",
            "قاطع",
            "احتمال",
            "اسناد",
            "مصدر",
            "نسبة القول",
            "نسبه القول",
            "اقتباس",
            "قول مباشر",
            "معنى",
            "معني",
            "عدد",
            "رقم",
            "تاريخ",
            "موعد",
            "وقت",
            "نسبة",
            "نسبه",
            "كمية",
            "كميه",
            "نطاق",
            "جمع",
            "مفرد",
        )
    )
    if _contains_any(material_text, material_markers):
        return False

    if not matched_safe:
        return False
    body = _headline_body_text(segments)
    if not body:
        return False
    if _span_overlap(original, body) < 0.4:
        return False
    return True


def _matched_normalized(text: str, markers: Iterable[str]) -> list[str]:
    normalized = _normalize_arabic(text)
    return [marker for marker in markers if _normalize_arabic(marker) in normalized]


def editorial_gate_decision(
    finding: Finding,
    *,
    policy: str | None,
    context: ArticleContext | None,
    segments: list[Segment],
) -> dict[str, Any]:
    """Return a structured, auditable decision for one finding."""
    normalized_policy = normalize_editorial_gate_policy(policy)
    category = (finding.category or "").strip().lower()
    source = finding.source
    base = {
        "policy_version": normalized_policy,
        "finding_id": finding.finding_id,
        "category": finding.category,
        "source": source.value if hasattr(source, "value") else source,
        "decision": "keep",
        "rule_id": "PASS",
        "reason_code": "not_targeted",
        "matched_evidence": [],
    }
    if normalized_policy == POLICY_OFF:
        return {**base, "reason_code": "policy_off"}

    # Numeric/date behavior is immutable even if a model uses a target category.
    if category in {
        "numeric_contradiction",
        "numeric_consistency",
        "temporal_contradiction",
        "date",
    }:
        return {
            **base,
            "reason_code": "numeric_or_date_protected",
            "matched_evidence": [category],
        }

    if normalized_policy == POLICY_RUN5:
        reason: str | None = None
        if source in {FindingSource.GEMINI, FindingSource.MOCK}:
            if category in _ATTRIBUTION_CATEGORIES and _run5_r1_suppresses(
                finding, context=context, segments=segments
            ):
                reason = ATTRIBUTION_REASON
            elif category == "clarity" and _run5_r2_suppresses(finding):
                reason = CLARITY_REASON
            elif category in _HEADLINE_CATEGORIES:
                segment = next(
                    (s for s in segments if s.segment_id == finding.segment_id), None
                )
                if not (
                    category == "publisher_voice"
                    and (segment is None or segment.zone != Zone.HEADLINE)
                ) and _run5_r4_suppresses(finding, segments=segments):
                    reason = HEADLINE_REASON
        if reason is None:
            return base
        rule_id = {
            ATTRIBUTION_REASON: "R1",
            CLARITY_REASON: "R2",
            HEADLINE_REASON: "R4",
        }[reason]
        return {
            **base,
            "decision": "suppress",
            "rule_id": rule_id,
            "reason_code": reason,
            "matched_evidence": [reason],
        }

    # Run5b: R2 sees mechanical + AI findings after merge.
    if category == "clarity" and source in {
        FindingSource.GEMINI,
        FindingSource.MOCK,
        FindingSource.MECHANICAL,
    }:
        if _run5b_r2_suppresses(finding):
            evidence = _matched_normalized(
                finding.explanation_ar, _GENERIC_CLARITY_MARKERS
            )
            return {
                **base,
                "decision": "suppress",
                "rule_id": "R2",
                "reason_code": CLARITY_REASON,
                "matched_evidence": evidence or ["normalized_generic_clarity_pattern"],
            }
        return {
            **base,
            "rule_id": "R2",
            "reason_code": "clarity_concrete_or_not_generic",
            "matched_evidence": _matched_normalized(
                finding.explanation_ar, _CONCRETE_CLARITY_MARKERS
            )
            or ["no_safe_generic_pattern"],
        }

    if source not in {FindingSource.GEMINI, FindingSource.MOCK}:
        return base

    if category in _ATTRIBUTION_CATEGORIES:
        if _run5b_r1_suppresses(finding, context=context, segments=segments):
            evidence = _matched_normalized(
                f"{finding.original_text} {finding.explanation_ar}",
                (*_VAGUE_SOURCE_SPANS, *_VAGUE_SOURCE_MARKERS),
            )
            return {
                **base,
                "decision": "suppress",
                "rule_id": "R1",
                "reason_code": ATTRIBUTION_REASON,
                "matched_evidence": evidence or ["nearby_explicit_attribution"],
            }
        return {
            **base,
            "rule_id": "R1",
            "reason_code": "attribution_material_or_strength_preserved",
            "matched_evidence": _matched_normalized(
                finding.explanation_ar,
                (*_MATERIAL_UNATTRIBUTED_MARKERS, *_ATTRIBUTION_CERTAINTY_MARKERS),
            )
            or [category],
        }

    if category in _HEADLINE_CATEGORIES:
        segment = next((s for s in segments if s.segment_id == finding.segment_id), None)
        if category == "publisher_voice" and (segment is None or segment.zone != Zone.HEADLINE):
            return {
                **base,
                "rule_id": "R4",
                "reason_code": "publisher_voice_not_headline",
            }
        if _run5b_r4_suppresses(finding, segments=segments):
            return {
                **base,
                "decision": "suppress",
                "rule_id": "R4",
                "reason_code": HEADLINE_REASON,
                "matched_evidence": ["safe_compression", "body_lexical_support>=0.4"],
            }
        material = _matched_normalized(
            finding.explanation_ar,
            (
                *_HEADLINE_MATERIAL_MARKERS,
                *_HEADLINE_ESCALATION_MARKERS,
                "يتناقض",
                "تناقض",
                "تعارض",
                "تضارب",
                "كيان",
                "دور",
                "نفي",
                "يقين",
                "إسناد",
                "اقتباس",
            ),
        )
        return {
            **base,
            "rule_id": "R4",
            "reason_code": "headline_material_or_not_proven_safe",
            "matched_evidence": material or ["no_positive_safe_compression_evidence"],
        }

    return base


def suppression_reason(
    finding: Finding,
    *,
    context: ArticleContext | None,
    segments: list[Segment],
    policy: str | None = POLICY_RUN5,
) -> str | None:
    """Return a reason code only when the selected policy suppresses."""
    decision = editorial_gate_decision(
        finding, policy=policy, context=context, segments=segments
    )
    return decision["reason_code"] if decision["decision"] == "suppress" else None


def gate_editorial_findings(
    findings: list[Finding],
    *,
    policy: str | None,
    context: ArticleContext | None,
    segments: list[Segment],
) -> tuple[list[Finding], list[Finding], list[dict[str, Any]]]:
    """Apply a versioned editorial policy and retain suppressions for audit."""
    normalized_policy = normalize_editorial_gate_policy(policy)
    if normalized_policy == POLICY_OFF:
        return list(findings), [], []

    kept: list[Finding] = []
    suppressed: list[Finding] = []
    audit: list[dict[str, Any]] = []
    for finding in findings:
        event = editorial_gate_decision(
            finding,
            policy=normalized_policy,
            context=context,
            segments=segments,
        )
        reason = event["reason_code"]
        if event["decision"] != "suppress":
            kept.append(finding)
            if normalized_policy == POLICY_RUN5B:
                audit.append(event)
            continue
        gated = finding.model_copy(
            update={
                "validation_errors": [
                    *(finding.validation_errors or []),
                    f"editorial_gate:{reason}",
                ]
            }
        )
        suppressed.append(gated)
        if normalized_policy == POLICY_RUN5:
            audit.append(
                {
                    "finding_id": finding.finding_id,
                    "action": "suppress",
                    "reason_code": reason,
                    "category": finding.category,
                    "source": (
                        finding.source.value
                        if hasattr(finding.source, "value")
                        else finding.source
                    ),
                }
            )
        else:
            audit.append(event)
    return kept, suppressed, audit
