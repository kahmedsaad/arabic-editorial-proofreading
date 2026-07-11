from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import (
    Decision,
    EditorialRule,
    Finding,
    FindingSource,
    Segment,
    Severity,
)


@dataclass(frozen=True)
class _EditorialFixture:
    span: str
    category: str
    decision: Decision
    severity: Severity
    rule_ids: list[str]
    suggested_text: str | None
    explanation_ar: str
    finding_id: str


_EDITORIAL_FIXTURES: tuple[_EditorialFixture, ...] = (
    _EditorialFixture(
        span="مقاتليه",
        category="entity_name",
        decision=Decision.HARD_WARNING,
        severity=Severity.HIGH,
        rule_ids=["R_DESC_NONSTATE"],
        suggested_text="عناصره",
        explanation_ar="وصف مقاتل في العنوان بصوت الناشر يحتاج مراجعة.",
        finding_id="FND-AI-ED-001",
    ),
    _EditorialFixture(
        span="وسائل إعلام لبنانية",
        category="attribution",
        decision=Decision.HARD_WARNING,
        severity=Severity.HIGH,
        rule_ids=["R_SOURCE_VAGUE"],
        suggested_text=None,
        explanation_ar="إسناد إعلامي مبهم.",
        finding_id="FND-AI-ED-002",
    ),
    _EditorialFixture(
        span="تأكيده",
        category="attribution_strength",
        decision=Decision.SOFT_WARNING,
        severity=Severity.MEDIUM,
        rule_ids=["R_ATTR_CONFIRMATION"],
        suggested_text="قوله",
        explanation_ar="فعل تأكيد مع مصدر واحد.",
        finding_id="FND-AI-ED-003",
    ),
    _EditorialFixture(
        span="المقاومة لن تسكت على هذا العدوان",
        category="loaded_framing",
        decision=Decision.NEEDS_EDITOR_REVIEW,
        severity=Severity.MEDIUM,
        rule_ids=["R_LOADED_FRAME"],
        suggested_text=None,
        explanation_ar="اقتباس مباشر — تُحفظ الصياغة.",
        finding_id="FND-AI-ED-004",
    ),
    _EditorialFixture(
        span="منظمة إرهابية",
        category="loaded_framing",
        decision=Decision.NEEDS_EDITOR_REVIEW,
        severity=Severity.HIGH,
        rule_ids=["R_TERROR_LABEL"],
        suggested_text=None,
        explanation_ar="وصف داخل اقتباس — لا يُستبدل تلقائياً.",
        finding_id="FND-AI-ED-005",
    ),
    _EditorialFixture(
        span="للميليشيا المدعومة من الخارج لترهيب الحدود",
        category="loaded_framing",
        decision=Decision.HARD_WARNING,
        severity=Severity.HIGH,
        rule_ids=["R03", "R04", "R07"],
        suggested_text=None,
        explanation_ar="تأطير محمل في تعليق الصورة/النص.",
        finding_id="FND-AI-ED-006",
    ),
)


class MockEditorialAIClient:
    """Deterministic AI client for local tests. No network."""

    async def discover_candidates(
        self,
        *,
        document_id: str,
        segments: list[Segment],
        mechanical_findings: list[Finding],
        rules: list[EditorialRule],
        entities: list | None = None,
    ) -> list[Finding]:
        del mechanical_findings, rules, entities
        findings: list[Finding] = []
        if not segments:
            return findings

        # Editorial Compass fixtures (Hezbollah article and similar text).
        for fixture in _EDITORIAL_FIXTURES:
            for segment in segments:
                idx = segment.text.find(fixture.span)
                if idx < 0:
                    continue
                findings.append(
                    Finding(
                        finding_id=fixture.finding_id,
                        document_id=document_id,
                        segment_id=segment.segment_id,
                        source=FindingSource.MOCK,
                        category=fixture.category,
                        decision=fixture.decision,
                        severity=fixture.severity,
                        original_text=fixture.span,
                        suggested_text=fixture.suggested_text,
                        start_offset=idx,
                        end_offset=idx + len(fixture.span),
                        rule_ids=list(fixture.rule_ids),
                        explanation_ar=fixture.explanation_ar,
                        confidence=0.9,
                        requires_editor_review=True,
                    )
                )
                break

        first = segments[0]
        marker = "حسب مصادر"
        idx = first.text.find(marker)
        if idx >= 0:
            findings.append(
                Finding(
                    finding_id="FND-AI-0001",
                    document_id=document_id,
                    segment_id=first.segment_id,
                    source=FindingSource.MOCK,
                    category="attribution_strength",
                    decision=Decision.NEEDS_EDITOR_REVIEW,
                    severity=Severity.HIGH,
                    original_text=marker,
                    suggested_text="بحسب مصادر",
                    start_offset=idx,
                    end_offset=idx + len(marker),
                    rule_ids=["ATTR-001"],
                    explanation_ar="صياغة نسبة تحتاج مراجعة تحريرية.",
                    confidence=0.8,
                    requires_editor_review=True,
                )
            )

        # Intentionally invalid finding so the validator path is exercised.
        findings.append(
            Finding(
                finding_id="FND-AI-INVALID",
                document_id=document_id,
                segment_id=first.segment_id,
                source=FindingSource.MOCK,
                category="attribution",
                decision=Decision.SUGGEST,
                severity=Severity.MEDIUM,
                original_text="نص غير موجود في المقطع",
                suggested_text="نص بديل",
                start_offset=0,
                end_offset=5,
                rule_ids=["ATTR-001"],
                explanation_ar="اقتراح وهمي للاختبار.",
                confidence=0.5,
                requires_editor_review=False,
            )
        )
        return findings

    async def judge_candidates(self, *, candidates: list[Finding]) -> list[Finding]:
        return candidates
