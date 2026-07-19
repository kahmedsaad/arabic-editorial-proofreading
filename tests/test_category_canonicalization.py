from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ai.gemini_client import GeminiEditorialAIClient
from app.category_canonicalization import canonicalize_category
from app.models.schemas import Segment, Zone
from app.rules.repository import JsonRuleRepository
from app.validation.validator import FindingValidator


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("category", "rule_ids", "expected"),
    [
        ("internal_inconsistency", ["CONS-CLAIM"], "claim_contradiction"),
        ("contradiction", ["CONS-CLAIM"], "claim_contradiction"),
        ("contradiction", ["CONS-DATE"], "temporal_contradiction"),
        ("internal inconsistency", ["CONS-NUMBER"], "numeric_contradiction"),
        ("numbers", ["CONS-NUMBER"], "numeric_contradiction"),
        ("date", ["CONS-DATE"], "temporal_contradiction"),
        ("name", ["CONS-NAME"], "entity_confusion"),
    ],
)
def test_reviewed_category_aliases_require_structured_rules(
    category,
    rule_ids,
    expected,
):
    result = canonicalize_category(category, rule_ids)
    assert result.canonical_category == expected
    assert result.alias_mapping_occurred is True


def test_generic_alias_rule_precedence_is_deterministic():
    result = canonicalize_category(
        "contradiction",
        ["CONS-CLAIM", "CONS-NAME", "CONS-NUMBER", "CONS-DATE"],
    )
    assert result.canonical_category == "temporal_contradiction"
    assert result.reason_code == "category_canonicalization:cons-date"


def test_canonical_and_unknown_categories_are_not_semantically_rewritten():
    canonical = canonicalize_category("numeric_contradiction", ["CONS-CLAIM"])
    assert canonical.canonical_category == "numeric_contradiction"
    assert canonical.mapping_occurred is False

    unsupported = canonicalize_category("internal_inconsistency", [])
    assert unsupported.canonical_category == "internal_inconsistency"
    assert unsupported.alias_mapping_occurred is False

    no_fuzzy_match = canonicalize_category(
        "internal_inconsistency_extra",
        ["CONS-CLAIM"],
    )
    assert no_fuzzy_match.canonical_category == "internal_inconsistency_extra"
    assert no_fuzzy_match.alias_mapping_occurred is False


def test_category_syntax_normalization_is_exact_not_fuzzy():
    result = canonicalize_category(
        "  Internal-Inconsistency  ",
        ["CONS-CLAIM"],
    )
    assert result.normalized_category == "internal_inconsistency"
    assert result.canonical_category == "claim_contradiction"


def _raw_finding(
    *,
    category: str = "internal_inconsistency",
    rule_ids: list[str] | None = None,
    **overrides,
) -> str:
    original_text = "الأعمال انطلقت فعليا في يوليو"
    item = {
        "finding_id": "F-D06",
        "document_id": "UI-D06",
        "segment_id": "SEG-002",
        "category": category,
        "decision": "needs_editor_review",
        "severity": "high",
        "original_text": original_text,
        "suggested_text": None,
        "start_offset": 0,
        "end_offset": len(original_text),
        "rule_ids": rule_ids if rule_ids is not None else ["CONS-CLAIM"],
        "entity_ids": [],
        "explanation_ar": "يوجد تناقض داخلي في تاريخ بدء المشروع ويجب على المحرر التحقق منه.",
        "confidence": 1.0,
        "requires_editor_review": True,
    }
    item.update(overrides)
    return json.dumps({"findings": [item]}, ensure_ascii=False)


@pytest.mark.parametrize("phase", ["discover", "judge", "repair"])
def test_gemini_parser_canonicalizes_every_finding_phase(phase):
    client = GeminiEditorialAIClient()
    client.last_call_trace = {}

    findings = client._parse_findings(_raw_finding(), "UI-D06", phase=phase)

    assert len(findings) == 1
    assert findings[0].category == "claim_contradiction"
    audit = client.last_call_trace["category_canonicalization"][0]
    assert audit == {
        "phase": phase,
        "finding_id": "F-D06",
        "raw_category": "internal_inconsistency",
        "normalized_category": "internal_inconsistency",
        "canonical_category": "claim_contradiction",
        "rule_ids": ["CONS-CLAIM"],
        "mapping_occurred": True,
        "alias_mapping_occurred": True,
        "reason_code": "category_canonicalization:cons-claim",
    }


def _d06_segment() -> Segment:
    text = "الأعمال انطلقت فعليا في يوليو"
    return Segment(
        segment_id="SEG-002",
        document_id="UI-D06",
        zone=Zone.BODY,
        text=text,
        normalized_text=text,
        start_offset=0,
        end_offset=len(text),
        sequence=2,
    )


def _validator() -> FindingValidator:
    repo = JsonRuleRepository(ROOT / "data" / "rules")
    return FindingValidator(
        known_rule_ids=repo.known_rule_ids(),
        known_categories=repo.known_categories(),
    )


def test_d06_category_passes_strict_validation_as_suggest_only_warning():
    client = GeminiEditorialAIClient()
    finding = client._parse_findings(
        _raw_finding(),
        "UI-D06",
        phase="discover",
    )[0]

    valid, rejected = _validator().validate(
        [finding],
        [_d06_segment()],
        "UI-D06",
    )

    assert not rejected
    assert len(valid) == 1
    assert valid[0].category == "claim_contradiction"
    assert valid[0].suggested_text is None
    assert valid[0].requires_editor_review is True


def test_historical_d06_payload_maps_then_passes_normal_offset_realignment():
    body = (
        "أكدت الشركة أن تنفيذ المشروع سيبدأ في سبتمبر المقبل. وأضافت أن الأعمال "
        "انطلقت فعليا في يوليو ولن تبدأ قبل الحصول على الموافقة النهائية."
    )
    original = (
        "تنفيذ المشروع سيبدأ في سبتمبر المقبل. وأضافت أن الأعمال انطلقت فعليا "
        "في يوليو"
    )
    segment = Segment(
        segment_id="SEG-002",
        document_id="UI-D06",
        zone=Zone.BODY,
        text=body,
        normalized_text=body,
        start_offset=0,
        end_offset=len(body),
        sequence=2,
    )
    client = GeminiEditorialAIClient()
    finding = client._parse_findings(
        _raw_finding(
            original_text=original,
            start_offset=13,
            end_offset=88,
        ),
        "UI-D06",
        phase="discover",
    )[0]

    valid, rejected, diagnostics = _validator().validate_with_diagnostics(
        [finding],
        [segment],
        "UI-D06",
    )

    assert not rejected
    assert valid[0].category == "claim_contradiction"
    assert valid[0].start_offset == 15
    assert valid[0].end_offset == 92
    assert valid[0].suggested_text is None
    assert diagnostics[0]["offset_realign_ran"] is True
    assert diagnostics[0]["validation_errors"] == []


def test_uncorroborated_alias_remains_rejected_by_strict_validator():
    client = GeminiEditorialAIClient()
    finding = client._parse_findings(
        _raw_finding(rule_ids=[]),
        "UI-D06",
        phase="discover",
    )[0]

    valid, rejected = _validator().validate(
        [finding],
        [_d06_segment()],
        "UI-D06",
    )

    assert not valid
    assert rejected[0].validation_errors == [
        "unknown category: internal_inconsistency"
    ]


@pytest.mark.parametrize(
    ("updates", "expected_error"),
    [
        ({"document_id": "OTHER"}, "document_id mismatch"),
        ({"segment_id": "SEG-UNKNOWN"}, "unknown segment_id"),
        ({"rule_ids": ["CONS-CLAIM", "CONS-UNKNOWN"]}, "unknown rule_id: CONS-UNKNOWN"),
        ({"entity_ids": ["ENT-UNKNOWN"]}, "unknown entity_id: ENT-UNKNOWN"),
        (
            {
                "original_text": "نص غير موجود",
                "start_offset": 0,
                "end_offset": 12,
            },
            "original_text not found in segment",
        ),
        ({"explanation_ar": ""}, "missing explanation_ar"),
    ],
)
def test_canonicalization_does_not_bypass_other_validator_checks(
    updates,
    expected_error,
):
    client = GeminiEditorialAIClient()
    finding = client._parse_findings(
        _raw_finding(),
        "UI-D06",
        phase="discover",
    )[0].model_copy(update=updates)

    valid, rejected = _validator().validate(
        [finding],
        [_d06_segment()],
        "UI-D06",
    )

    assert not valid
    assert expected_error in rejected[0].validation_errors
