"""Unit tests for Gemini finding gate (no hidden gold)."""

from app.models.schemas import Decision, Finding, FindingSource, Segment, Severity, Zone
from app.postprocess.gemini_gate import gate_gemini_findings, normalize_category


def _seg(text: str, sid: str = "SEG-001") -> Segment:
    return Segment(
        segment_id=sid,
        document_id="DOC",
        zone=Zone.BODY,
        text=text,
        normalized_text=text,
        start_offset=0,
        end_offset=len(text),
        sequence=0,
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


def test_normalize_category():
    assert normalize_category("consistency") == "claim_contradiction"


def test_gate_drops_low_confidence():
    text = "قال المصدر إنه أكد الخبر."
    seg = _seg(text)
    f = _finding(
        original_text="أكد",
        start_offset=text.find("أكد"),
        end_offset=text.find("أكد") + 3,
        confidence=0.4,
        category="attribution",
    )
    kept, rejected = gate_gemini_findings(
        gemini_findings=[f], mechanical_findings=[], segments=[seg]
    )
    assert kept == []
    assert len(rejected) == 1


def test_gate_drops_when_covered_by_mechanical():
    text = "ويؤكد ذلك أن الوزير مستفيد."
    seg = _seg(text)
    mech = _finding(
        finding_id="FND-M-1",
        source=FindingSource.MECHANICAL,
        category="publisher_voice",
        original_text="ويؤكد ذلك",
        start_offset=0,
        end_offset=9,
        confidence=1.0,
        explanation_ar="تحويل قرائن إلى حقيقة.",
    )
    gem = _finding(
        original_text="ويؤكد ذلك",
        start_offset=0,
        end_offset=9,
        category="publisher_voice",
        severity=Severity.HIGH,
        confidence=0.95,
        explanation_ar="صوت الناشر يحول القرائن إلى اتهام.",
    )
    kept, rejected = gate_gemini_findings(
        gemini_findings=[gem], mechanical_findings=[mech], segments=[seg]
    )
    assert kept == []
    assert rejected


def test_gate_keeps_high_confidence_publisher_voice():
    text = "ويؤكد ذلك أن الوزير مستفيد."
    seg = _seg(text)
    gem = _finding(
        original_text="ويؤكد ذلك",
        start_offset=0,
        end_offset=9,
        category="publisher_voice",
        severity=Severity.HIGH,
        confidence=0.9,
        explanation_ar="صوت الناشر يحول القرائن إلى اتهام غير مثبت.",
    )
    kept, rejected = gate_gemini_findings(
        gemini_findings=[gem], mechanical_findings=[], segments=[seg]
    )
    assert len(kept) == 1
    assert rejected == []
