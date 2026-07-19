from pathlib import Path

from app.models.schemas import Decision, Finding, FindingSource, Segment, Severity, Zone
from app.rules.repository import JsonRuleRepository
from app.validation.validator import FindingValidator

ROOT = Path(__file__).resolve().parents[1]


def _segment() -> Segment:
    return Segment(
        segment_id="SEG-001",
        document_id="DOC-001",
        zone=Zone.BODY,
        text="حسب مصادر محلية",
        normalized_text="حسب مصادر محلية",
        start_offset=0,
        end_offset=15,
        sequence=1,
    )


def test_validator_accepts_exact_span():
    repo = JsonRuleRepository(ROOT / "data" / "rules")
    validator = FindingValidator(
        known_rule_ids=repo.known_rule_ids(),
        known_categories=repo.known_categories(),
    )
    segment = _segment()
    finding = Finding(
        finding_id="F1",
        document_id="DOC-001",
        segment_id="SEG-001",
        source=FindingSource.MECHANICAL,
        category="attribution",
        decision=Decision.SUGGEST,
        severity=Severity.MEDIUM,
        original_text="حسب مصادر",
        suggested_text="بحسب مصادر",
        start_offset=0,
        end_offset=9,
        rule_ids=["ATTR-001"],
        explanation_ar="مراجعة النسبة.",
        confidence=0.9,
    )
    valid, rejected = validator.validate([finding], [segment], "DOC-001")
    assert len(valid) == 1
    assert not rejected
    assert valid[0].validation_status.value == "valid"


def test_validator_rejects_bad_span():
    repo = JsonRuleRepository(ROOT / "data" / "rules")
    validator = FindingValidator(
        known_rule_ids=repo.known_rule_ids(),
        known_categories=repo.known_categories(),
    )
    segment = _segment()
    finding = Finding(
        finding_id="F2",
        document_id="DOC-001",
        segment_id="SEG-001",
        source=FindingSource.MOCK,
        category="attribution",
        decision=Decision.SUGGEST,
        severity=Severity.MEDIUM,
        original_text="نص خاطئ",
        suggested_text="نص",
        start_offset=0,
        end_offset=4,
        rule_ids=["ATTR-001"],
        explanation_ar="اختبار",
        confidence=0.5,
    )
    valid, rejected = validator.validate([finding], [segment], "DOC-001")
    assert not valid
    assert len(rejected) == 1
    assert rejected[0].validation_status.value == "invalid"


def test_validator_records_offset_realign_diagnostics():
    repo = JsonRuleRepository(ROOT / "data" / "rules")
    validator = FindingValidator(
        known_rule_ids=repo.known_rule_ids(),
        known_categories=repo.known_categories(),
    )
    segment = _segment()
    finding = Finding(
        finding_id="F-REALIGN",
        document_id="DOC-001",
        segment_id="SEG-001",
        source=FindingSource.MOCK,
        category="attribution",
        decision=Decision.HARD_WARNING,
        severity=Severity.HIGH,
        original_text="مصادر",
        suggested_text=None,
        start_offset=0,
        end_offset=5,
        rule_ids=["ATTR-001"],
        explanation_ar="تحذير يحتاج تحقق المحرر.",
        confidence=0.9,
        requires_editor_review=True,
    )

    valid, rejected, diagnostics = validator.validate_with_diagnostics(
        [finding], [segment], "DOC-001"
    )

    assert len(valid) == 1
    assert not rejected
    diagnostic = diagnostics[0]
    assert diagnostic["offset_realign_ran"] is True
    assert diagnostic["before_realign"]["start_offset"] == 0
    assert diagnostic["after_realign"]["start_offset"] == segment.text.index("مصادر")
    assert diagnostic["validation_errors"] == []
    assert diagnostic["outcome"] == "valid"


def test_validator_diagnostics_preserve_non_allowlisted_unknown_category():
    repo = JsonRuleRepository(ROOT / "data" / "rules")
    validator = FindingValidator(
        known_rule_ids=repo.known_rule_ids(),
        known_categories=repo.known_categories(),
    )
    segment = _segment()
    finding = Finding(
        finding_id="F-UNKNOWN-CATEGORY",
        document_id="DOC-001",
        segment_id="SEG-001",
        source=FindingSource.MOCK,
        category="internal_inconsistency",
        decision=Decision.HARD_WARNING,
        severity=Severity.HIGH,
        original_text=segment.text,
        suggested_text=None,
        start_offset=0,
        end_offset=len(segment.text),
        rule_ids=["CONS-CLAIM"],
        explanation_ar="يوجد تناقض داخلي يحتاج تحقق المحرر.",
        confidence=1.0,
        requires_editor_review=True,
    )

    valid, rejected, diagnostics = validator.validate_with_diagnostics(
        [finding], [segment], "DOC-001"
    )

    assert not valid
    assert len(rejected) == 1
    assert rejected[0].validation_errors == [
        "unknown category: internal_inconsistency"
    ]
    diagnostic = diagnostics[0]
    assert diagnostic["offset_realign_ran"] is False
    assert diagnostic["outcome"] == "rejected"
    assert diagnostic["validation_errors"] == [
        "unknown category: internal_inconsistency"
    ]
