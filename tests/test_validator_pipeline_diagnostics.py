from __future__ import annotations

import pytest

from app.config import settings
from app.models.schemas import (
    Decision,
    Finding,
    FindingSource,
    ReviewRequest,
    Severity,
)
from app.orchestration.review import ReviewOrchestrator


class _UnknownCategoryRepairClient:
    last_call_trace = {
        "system_prompt": "test",
        "user_payload": "{}",
        "raw_response": '{"findings":[]}',
    }

    async def discover_candidates(self, **kwargs):
        segment = kwargs["segments"][-1]
        original = segment.text
        return [
            Finding(
                finding_id="F-D06",
                document_id=kwargs["document_id"],
                segment_id=segment.segment_id,
                source=FindingSource.MOCK,
                category="internal_inconsistency",
                decision=Decision.NEEDS_EDITOR_REVIEW,
                severity=Severity.HIGH,
                original_text=original,
                suggested_text=None,
                start_offset=0,
                end_offset=len(original),
                rule_ids=[],
                explanation_ar="يوجد تناقض داخلي يحتاج تحقق المحرر.",
                confidence=1.0,
                requires_editor_review=True,
            )
        ]

    async def judge_candidates(self, **kwargs):
        return kwargs["candidates"]

    async def repair_findings(self, **kwargs):
        return [
            finding.model_copy(
                update={
                    "category": "contradiction",
                    "validation_errors": [],
                }
            )
            for finding in kwargs["findings"]
        ]


@pytest.mark.asyncio
async def test_pipeline_audits_both_unknown_category_validation_failures(
    monkeypatch,
):
    monkeypatch.setattr(settings, "editorial_gate_policy", "off")
    monkeypatch.setattr(settings, "punctuation_policy", "off")
    response = await ReviewOrchestrator(
        ai_client=_UnknownCategoryRepairClient()
    ).review(
        ReviewRequest(
            document_id="UI-D06-DIAGNOSTIC",
            headline="بدء المشروع في سبتمبر",
            body=(
                "أكدت الشركة أن تنفيذ المشروع سيبدأ في سبتمبر المقبل. "
                "وأضافت أن الأعمال انطلقت فعليا في يوليو ولن تبدأ قبل "
                "الحصول على الموافقة النهائية."
            ),
        )
    )

    assert response.findings == []
    assert len(response.rejected_findings) == 1
    assert response.rejected_findings[0].validation_errors == [
        "unknown category: contradiction"
    ]

    validate_step = next(
        step for step in response.pipeline_log if step.step_id == "validate"
    )
    first = validate_step.output_summary["first_pass"][0]
    second = validate_step.output_summary["second_pass"][0]
    assert first["validation_errors"] == [
        "unknown category: internal_inconsistency"
    ]
    assert second["validation_errors"] == ["unknown category: contradiction"]
    assert first["offset_realign_ran"] is False
    assert second["offset_realign_ran"] is False

    repair_step = next(
        step for step in response.pipeline_log if step.step_id == "repair"
    )
    assert repair_step.output_summary["repaired_ids"] == ["F-D06"]
    assert repair_step.output_summary["repaired_findings"][0]["category"] == (
        "contradiction"
    )

    final_step = next(
        step for step in response.pipeline_log if step.step_id == "final"
    )
    assert final_step.output_summary["findings"] == []
    assert final_step.output_summary["rejected_findings"][0][
        "validation_errors"
    ] == ["unknown category: contradiction"]
