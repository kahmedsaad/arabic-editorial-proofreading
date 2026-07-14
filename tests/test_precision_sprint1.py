"""Sprint 1 precision foundation — FP family regression tests."""

from app.context.article_context import extract_article_context
from app.models.schemas import (
    AdjudicationVerdict,
    Decision,
    Document,
    EditorialHarm,
    Finding,
    FindingSource,
    Segment,
    Severity,
    Zone,
)
from app.postprocess.adjudicator import adjudicate_findings
from app.postprocess.gemini_gate import confidence_threshold_for_category, gate_gemini_findings


def _seg(
    text: str,
    *,
    sid: str = "SEG-001",
    zone: Zone = Zone.BODY,
    seq: int = 0,
) -> Segment:
    return Segment(
        segment_id=sid,
        document_id="DOC",
        zone=zone,
        text=text,
        normalized_text=text,
        start_offset=0,
        end_offset=len(text),
        sequence=seq,
    )


def _finding(**kwargs) -> Finding:
    defaults = dict(
        finding_id="FND-AI-1",
        document_id="DOC",
        segment_id="SEG-001",
        source=FindingSource.GEMINI,
        category="attribution",
        decision=Decision.SOFT_WARNING,
        severity=Severity.MEDIUM,
        original_text="أكد",
        suggested_text=None,
        start_offset=0,
        end_offset=3,
        rule_ids=[],
        explanation_ar="فعل تأكيد قد يقوي الادعاء دون دليل إضافي.",
        confidence=0.9,
    )
    defaults.update(kwargs)
    return Finding(**defaults)


def test_category_thresholds_raise_attribution_and_quote():
    assert confidence_threshold_for_category("attribution", Severity.MEDIUM) >= 0.92
    assert confidence_threshold_for_category("quote_voice", Severity.MEDIUM) >= 0.95
    assert confidence_threshold_for_category("numeric_contradiction", Severity.HIGH) <= 0.75


def test_headline_attribution_suppressed_when_body_attributes():
    headline = "الجيش يعلن السيطرة على المنطقة"
    body = "قال المتحدث باسم الجيش إن القوات سيطرت على المنطقة."
    h = _seg(headline, sid="SEG-H", zone=Zone.HEADLINE, seq=0)
    b = _seg(body, sid="SEG-B", zone=Zone.BODY, seq=1)
    doc = Document(document_id="DOC", headline=headline, body=body)
    ctx = extract_article_context(doc, [h, b])
    assert ctx.attribution_links

    f = _finding(
        finding_id="FND-AI-HEAD",
        segment_id="SEG-H",
        original_text="يعلن السيطرة",
        start_offset=headline.find("يعلن السيطرة"),
        end_offset=headline.find("يعلن السيطرة") + len("يعلن السيطرة"),
        category="attribution",
        confidence=0.91,
        explanation_ar="العنوان يفتقد فعل إسناد صريح مثل قال.",
    )
    shown, suppressed = adjudicate_findings(
        findings=[f], context=ctx, segments=[h, b], mechanical=[]
    )
    assert shown == []
    assert suppressed
    assert suppressed[0].adjudication_verdict == AdjudicationVerdict.SUPPRESS
    assert any("headline_compression" in e for e in suppressed[0].validation_errors)


def test_direct_quote_strips_rewrite_and_suppresses_attribution_nag():
    text = "قال القائد: «المقاومة لن تسكت على هذا العدوان»."
    seg = _seg(text)
    doc = Document(document_id="DOC", headline="", body=text)
    ctx = extract_article_context(doc, [seg])
    span = "المقاومة لن تسكت على هذا العدوان"
    start = text.find(span)
    f = _finding(
        original_text=span,
        start_offset=start,
        end_offset=start + len(span),
        category="quote_voice",
        decision=Decision.REPLACE,
        suggested_text="عناصر مسلحة",
        confidence=0.99,
        explanation_ar="صياغة داخل الاقتباس قد تكون محملة.",
    )
    shown, suppressed = adjudicate_findings(
        findings=[f], context=ctx, segments=[seg], mechanical=[]
    )
    assert shown == []
    assert suppressed[0].suggested_text is None
    assert suppressed[0].adjudication_verdict == AdjudicationVerdict.SUPPRESS


def test_vague_masadir_routine_suppressed():
    text = "قالت مصادر إن الاجتماع سيعقد غدا في العاصمة."
    seg = _seg(text)
    doc = Document(document_id="DOC", body=text)
    ctx = extract_article_context(doc, [seg])
    span = "مصادر"
    start = text.find(span)
    f = _finding(
        original_text=span,
        start_offset=start,
        end_offset=start + len(span),
        category="source_quality",
        confidence=0.93,
        explanation_ar="إسناد إلى مصادر دون تحديد الجهة.",
    )
    shown, suppressed = adjudicate_findings(
        findings=[f], context=ctx, segments=[seg], mechanical=[]
    )
    assert shown == []
    assert any("vague_source_routine" in e for e in suppressed[0].validation_errors)


def test_silence_fields_suppress_when_harm_none():
    text = "قال الوزير إن الوضع مستقر."
    seg = _seg(text)
    doc = Document(document_id="DOC", body=text)
    ctx = extract_article_context(doc, [seg])
    f = _finding(
        original_text="مستقر",
        start_offset=text.find("مستقر"),
        end_offset=text.find("مستقر") + 5,
        category="attribution",
        confidence=0.99,
        editorial_harm_if_ignored=EditorialHarm.NONE,
        would_interrupt_editor=True,
        explanation_ar="تحسين أسلوبي محتمل دون ضرر تحريري.",
    )
    shown, suppressed = adjudicate_findings(
        findings=[f], context=ctx, segments=[seg], mechanical=[]
    )
    assert shown == []
    assert suppressed[0].adjudication_verdict == AdjudicationVerdict.SUPPRESS


def test_publisher_voice_high_confidence_can_show():
    text = "ويؤكد ذلك أن الوزير مستفيد من الصفقة."
    seg = _seg(text)
    doc = Document(document_id="DOC", body=text)
    ctx = extract_article_context(doc, [seg])
    f = _finding(
        original_text="ويؤكد ذلك",
        start_offset=0,
        end_offset=9,
        category="publisher_voice",
        severity=Severity.HIGH,
        confidence=0.95,
        explanation_ar="صوت الناشر يحول القرائن إلى اتهام غير مثبت.",
        rule_ids=["R_LOADED_FRAME"],
        would_interrupt_editor=True,
    )
    shown, suppressed = adjudicate_findings(
        findings=[f], context=ctx, segments=[seg], mechanical=[]
    )
    assert len(shown) == 1
    assert shown[0].adjudication_verdict in {
        AdjudicationVerdict.SHOW,
        AdjudicationVerdict.NEEDS_CONTEXT,
    }
    assert suppressed == []


def test_gate_still_drops_invalid_span():
    text = "نص بلا المشكلة."
    seg = _seg(text)
    f = _finding(
        original_text="غير موجود",
        start_offset=0,
        end_offset=5,
        category="publisher_voice",
        confidence=0.99,
        explanation_ar="صوت الناشر يحول القرائن إلى اتهام.",
    )
    kept, rejected = gate_gemini_findings(
        gemini_findings=[f], mechanical_findings=[], segments=[seg]
    )
    assert kept == []
    assert rejected
