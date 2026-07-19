from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ai.gemini_client import (
    GeminiEditorialAIClient,
    GeminiResponseParseError,
)
from app.config import settings
from app.models.schemas import (
    Decision,
    Finding,
    FindingSource,
    ReviewRequest,
    Segment,
    Severity,
    Zone,
)
from app.orchestration.review import ReviewOrchestrator
from app.rules.repository import JsonRuleRepository
from app.validation.validator import FindingValidator


ROOT = Path(__file__).resolve().parents[1]


def _segment(
    text: str = "فوز الفريق في النهائي",
    *,
    document_id: str = "UI-D05",
    segment_id: str = "SEG-001",
    zone: Zone = Zone.HEADLINE,
) -> Segment:
    return Segment(
        segment_id=segment_id,
        document_id=document_id,
        zone=zone,
        text=text,
        normalized_text=text,
        start_offset=0,
        end_offset=len(text),
        sequence=1,
    )


def _finding_payload(**updates) -> dict[str, object]:
    text = "فوز الفريق في النهائي"
    payload: dict[str, object] = {
        "finding_id": "FND-D05-LIST",
        "document_id": "UI-D05",
        "segment_id": "SEG-001",
        "category": "headline_body_mismatch",
        "decision": "needs_editor_review",
        "severity": "high",
        "original_text": text,
        "suggested_text": None,
        "start_offset": 0,
        "end_offset": len(text),
        "rule_ids": ["CONS-CLAIM"],
        "entity_ids": [],
        "explanation_ar": "العنوان يفيد الفوز بينما المتن يذكر خسارة النهائي والتتويج.",
        "confidence": 1.0,
        "requires_editor_review": True,
    }
    payload.update(updates)
    return payload


def _raw_list(*items: object) -> str:
    return json.dumps(list(items), ensure_ascii=False)


def _set_generated_response(
    monkeypatch: pytest.MonkeyPatch,
    client: GeminiEditorialAIClient,
    raw: str,
) -> None:
    monkeypatch.setattr(client, "_has_credentials", lambda: True)

    def generate(*, system: str, user: str) -> str:
        client.last_call_trace = {
            "system_prompt": system,
            "user_payload": user,
            "raw_response": raw,
        }
        return raw

    monkeypatch.setattr(client, "_generate", generate)


def test_top_level_list_and_object_envelope_parse_valid_finding():
    client = GeminiEditorialAIClient()
    list_findings = client._parse_findings(
        _raw_list(_finding_payload()),
        "UI-D05",
        phase="discover",
    )
    assert [finding.finding_id for finding in list_findings] == ["FND-D05-LIST"]
    assert client.last_parse_diagnostic == {
        "phase": "discover",
        "status": "ok",
        "failure_type": None,
        "safe_reason": "parsed",
        "envelope_type": "top_level_list",
        "valid_item_count": 1,
        "rejected_item_count": 0,
        "rejected_item_indexes": [],
        "rejected_items": [],
        "fallback_used": False,
        "fallback_type": None,
    }

    object_findings = client._parse_findings(
        json.dumps({"findings": [_finding_payload()]}, ensure_ascii=False),
        "UI-D05",
        phase="discover",
    )
    assert len(object_findings) == 1
    assert client.last_parse_diagnostic["envelope_type"] == "object_envelope"


@pytest.mark.parametrize("raw", ["[]", '{"findings": []}'])
def test_empty_envelopes_are_valid_zero_finding_responses(raw):
    client = GeminiEditorialAIClient()
    assert client._parse_findings(raw, "DOC", phase="discover") == []
    assert client.last_parse_diagnostic["status"] == "ok"
    assert client.last_parse_diagnostic["valid_item_count"] == 0


@pytest.mark.parametrize("raw", ["null", "true", "42", '"findings"'])
def test_primitive_top_level_values_raise_typed_diagnostic(raw):
    client = GeminiEditorialAIClient()
    with pytest.raises(GeminiResponseParseError) as error:
        client._parse_findings(raw, "DOC", phase="discover")
    assert error.value.failure_type == "invalid_top_level_type"
    assert client.last_parse_diagnostic["status"] == "degraded"
    assert client.last_parse_diagnostic["failure_type"] == "invalid_top_level_type"


def test_non_list_findings_and_single_finding_object_are_rejected():
    client = GeminiEditorialAIClient()
    with pytest.raises(GeminiResponseParseError) as non_list:
        client._parse_findings(
            '{"findings": {"finding_id": "F1"}}',
            "DOC",
            phase="discover",
        )
    assert non_list.value.failure_type == "invalid_envelope_field_type"

    with pytest.raises(GeminiResponseParseError) as single:
        client._parse_findings(
            json.dumps(_finding_payload(), ensure_ascii=False),
            "UI-D05",
            phase="discover",
        )
    assert single.value.failure_type == "missing_envelope_field"


def test_malformed_items_do_not_discard_valid_siblings_or_leak_payloads():
    client = GeminiEditorialAIClient()
    invalid = _finding_payload(
        finding_id="F-INVALID",
        adjudication_verdict="accepted",
    )
    findings = client._parse_findings(
        _raw_list(
            _finding_payload(finding_id="F-VALID-1"),
            "not-an-object",
            invalid,
            _finding_payload(finding_id="F-VALID-2"),
        ),
        "UI-D05",
        phase="judge",
    )

    assert [finding.finding_id for finding in findings] == [
        "F-VALID-1",
        "F-VALID-2",
    ]
    diagnostic = client.last_parse_diagnostic
    assert diagnostic["status"] == "partial"
    assert diagnostic["valid_item_count"] == 2
    assert diagnostic["rejected_item_count"] == 2
    assert diagnostic["rejected_item_indexes"] == [1, 2]
    serialized = json.dumps(diagnostic)
    assert "not-an-object" not in serialized
    assert "accepted" not in serialized


def test_list_envelope_preserves_reviewed_category_canonicalization():
    client = GeminiEditorialAIClient()
    finding = client._parse_findings(
        _raw_list(
            _finding_payload(
                category="internal_inconsistency",
                rule_ids=["CONS-CLAIM"],
            )
        ),
        "UI-D05",
        phase="repair",
    )[0]
    assert finding.category == "claim_contradiction"
    audit = client.last_call_trace["category_canonicalization"][0]
    assert audit["raw_category"] == "internal_inconsistency"
    assert audit["canonical_category"] == "claim_contradiction"


@pytest.mark.asyncio
async def test_discovery_list_envelope_parses_without_retry(monkeypatch):
    client = GeminiEditorialAIClient()
    _set_generated_response(monkeypatch, client, _raw_list(_finding_payload()))
    findings = await client.discover_candidates(
        document_id="UI-D05",
        segments=[_segment()],
        mechanical_findings=[],
        rules=[],
    )
    assert len(findings) == 1
    assert client.last_parse_diagnostic["phase"] == "discover"
    assert client.last_parse_diagnostic["envelope_type"] == "top_level_list"


@pytest.mark.asyncio
async def test_judgment_and_repair_use_same_list_envelope_parser(monkeypatch):
    candidate = Finding.model_validate(
        {
            **_finding_payload(),
            "source": FindingSource.GEMINI,
        }
    )
    client = GeminiEditorialAIClient()
    _set_generated_response(monkeypatch, client, _raw_list(_finding_payload()))

    judged = await client.judge_candidates(candidates=[candidate])
    assert len(judged) == 1
    assert client.last_parse_diagnostic["phase"] == "judge"
    assert client.last_parse_diagnostic["envelope_type"] == "top_level_list"

    repaired = await client.repair_findings(
        findings=[candidate],
        segments=[_segment()],
        validation_errors={candidate.finding_id: ["test"]},
    )
    assert len(repaired) == 1
    assert client.last_parse_diagnostic["phase"] == "repair"
    assert client.last_parse_diagnostic["envelope_type"] == "top_level_list"


@pytest.mark.asyncio
async def test_empty_judgment_list_is_valid_zero_finding_response(monkeypatch):
    candidate = Finding.model_validate(
        {
            **_finding_payload(),
            "source": FindingSource.GEMINI,
        }
    )
    client = GeminiEditorialAIClient()
    _set_generated_response(monkeypatch, client, "[]")
    assert await client.judge_candidates(candidates=[candidate]) == []
    assert client.last_parse_diagnostic["status"] == "ok"
    assert client.last_parse_diagnostic["fallback_used"] is False


@pytest.mark.asyncio
async def test_discovery_parse_failure_returns_no_editorial_finding(monkeypatch):
    client = GeminiEditorialAIClient()
    _set_generated_response(monkeypatch, client, "42")
    findings = await client.discover_candidates(
        document_id="DOC",
        segments=[_segment(document_id="DOC")],
        mechanical_findings=[],
        rules=[],
    )
    assert findings == []
    assert client.last_parse_diagnostic["failure_type"] == "invalid_top_level_type"
    assert client.last_parse_diagnostic["fallback_used"] is False


@pytest.mark.asyncio
async def test_judgment_parse_failure_records_heuristic_fallback(monkeypatch):
    candidate = Finding.model_validate(
        {
            **_finding_payload(),
            "source": FindingSource.GEMINI,
        }
    )
    client = GeminiEditorialAIClient()
    _set_generated_response(monkeypatch, client, '{"findings": {}}')
    judged = await client.judge_candidates(candidates=[candidate])
    assert [finding.finding_id for finding in judged] == [candidate.finding_id]
    assert client.last_parse_diagnostic["failure_type"] == (
        "invalid_envelope_field_type"
    )
    assert client.last_parse_diagnostic["fallback_used"] is True
    assert client.last_parse_diagnostic["fallback_type"] == "heuristic_judge"


@pytest.mark.asyncio
async def test_repair_parse_failure_preserves_strict_validation(monkeypatch):
    candidate = Finding.model_validate(
        {
            **_finding_payload(category="unknown_alias", rule_ids=[]),
            "source": FindingSource.GEMINI,
        }
    )
    client = GeminiEditorialAIClient()
    _set_generated_response(monkeypatch, client, "null")
    repaired = await client.repair_findings(
        findings=[candidate],
        segments=[_segment()],
        validation_errors={candidate.finding_id: ["unknown category"]},
    )
    repo = JsonRuleRepository(ROOT / "data" / "rules")
    validator = FindingValidator(
        known_rule_ids=repo.known_rule_ids(),
        known_categories=repo.known_categories(),
    )
    valid, rejected = validator.validate(repaired, [_segment()], "UI-D05")
    assert not valid
    assert rejected[0].validation_errors == ["unknown category: unknown_alias"]
    assert client.last_parse_diagnostic["fallback_type"] == "local_repair"


@pytest.mark.asyncio
async def test_d05_list_fixture_surfaces_first_pass_without_public_raw_leak(
    monkeypatch,
):
    monkeypatch.setattr(settings, "editorial_gate_policy", "off")
    monkeypatch.setattr(settings, "punctuation_policy", "off")
    client = GeminiEditorialAIClient()
    raw = _raw_list(_finding_payload())
    _set_generated_response(monkeypatch, client, raw)

    response = await ReviewOrchestrator(ai_client=client).review(
        ReviewRequest(
            document_id="UI-D05",
            headline="فوز الفريق في النهائي",
            body=(
                "خسر فريق المدينة المباراة النهائية بهدفين مقابل هدف، "
                "ليتوج بطلا للبطولة للمرة الثالثة."
            ),
        )
    )

    assert [finding.finding_id for finding in response.findings] == [
        "FND-D05-LIST"
    ]
    assert response.findings[0].suggested_text is None
    assert not any(
        finding.finding_id == "FND-AI-FALLBACK"
        for finding in [*response.findings, *response.rejected_findings]
    )
    public_stages = json.dumps(
        [stage.model_dump(mode="json") for stage in response.stages],
        ensure_ascii=False,
    )
    assert raw not in public_stages
    discover = next(
        step for step in response.pipeline_log if step.step_id == "discover"
    )
    assert discover.output_summary["parser_diagnostic"]["envelope_type"] == (
        "top_level_list"
    )


@pytest.mark.asyncio
async def test_rule_author_accepts_top_level_list_envelope(monkeypatch):
    rule = json.loads((ROOT / "data" / "rules" / "CONS-CLAIM.json").read_text("utf-8"))
    client = GeminiEditorialAIClient()
    _set_generated_response(monkeypatch, client, _raw_list(rule))
    authored = await client.author_rules(text="قاعدة تحريرية جديدة")
    assert [item.rule_id for item in authored] == ["CONS-CLAIM"]
