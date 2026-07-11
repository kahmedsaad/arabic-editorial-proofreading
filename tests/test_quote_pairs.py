from app.mechanical.checks import check_quotation_consistency
from app.models.schemas import Document, Segment, Zone


def _seg(text: str) -> Segment:
    return Segment(
        segment_id="SEG-001",
        document_id="DOC-Q",
        zone=Zone.BODY,
        text=text,
        normalized_text=text,
        start_offset=0,
        end_offset=len(text),
        sequence=0,
    )


def test_paired_guillemets_are_not_flagged():
    findings = check_quotation_consistency(_seg("قال إن «الوضع مستقر» اليوم."), [0])
    assert findings == []


def test_paired_curly_quotes_are_not_flagged():
    findings = check_quotation_consistency(_seg("He said “hello” then left."), [0])
    assert findings == []


def test_unclosed_guillemet_is_flagged():
    findings = check_quotation_consistency(_seg("قال إن «الوضع مستقر اليوم."), [0])
    assert len(findings) == 1
    assert findings[0].rule_ids == ["MECH-QUOTE"]
