from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.models.schemas import (
    ArticleContext,
    Decision,
    EditorialHarm,
    EditorialRule,
    Finding,
    FindingSource,
    RuleApplicability,
    Segment,
    Severity,
)
from app.rules.bulk import free_text_to_rule_stub, parse_rules_paste


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
    _EditorialFixture(
        span="النظام الإيراني",
        category="loaded_framing",
        decision=Decision.SOFT_WARNING,
        severity=Severity.MEDIUM,
        rule_ids=["R_IRAN_REGIME"],
        suggested_text="السلطات الإيرانية",
        explanation_ar="صيغة غير مفضلة للإشارة إلى الجهة الحاكمة.",
        finding_id="FND-AI-ED-007",
    ),
    _EditorialFixture(
        span="نظام الملالي",
        category="loaded_framing",
        decision=Decision.BAN,
        severity=Severity.CRITICAL,
        rule_ids=["R_IRAN_MULLAHS"],
        suggested_text="السلطات الإيرانية",
        explanation_ar="وصف محظور في صوت الناشر.",
        finding_id="FND-AI-ED-008",
    ),
)


class MockEditorialAIClient:
    """Deterministic AI client for local tests. No network."""

    def __init__(self) -> None:
        self.last_call_trace: dict[str, Any] | None = None

    def _trace(self, *, phase: str, system: str, user: str, raw: str) -> None:
        self.last_call_trace = {
            "phase": phase,
            "system_prompt": system,
            "user_payload": user,
            "raw_response": raw,
            "client": "mock",
        }

    async def discover_candidates(
        self,
        *,
        document_id: str,
        segments: list[Segment],
        mechanical_findings: list[Finding],
        rules: list[EditorialRule],
        entities: list | None = None,
        article_context: ArticleContext | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        user = json.dumps(
            {
                "document_id": document_id,
                "article_context": (
                    article_context.model_dump(mode="json") if article_context else None
                ),
                "segments": [s.model_dump(mode="json") for s in segments],
                "mechanical_findings": [f.model_dump(mode="json") for f in mechanical_findings],
                "rules": [r.model_dump(mode="json") for r in rules],
                "entities": entities or [],
            },
            ensure_ascii=False,
        )
        if not segments:
            self._trace(
                phase="discover",
                system="mock discover",
                user=user,
                raw='{"findings":[]}',
            )
            return findings

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
                    confidence=0.96,
                    requires_editor_review=True,
                    editorial_harm_if_ignored=EditorialHarm.MEDIUM,
                    rule_applicability=RuleApplicability.CLEAR,
                    would_interrupt_editor=True,
                    article_context_resolves_issue=False,
                )
            )

        # Intentionally invalid finding so the validator + repair path is exercised.
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
        self._trace(
            phase="discover",
            system="mock discover — fixture span matching",
            user=user,
            raw=json.dumps(
                {"findings": [f.model_dump(mode="json") for f in findings]},
                ensure_ascii=False,
            ),
        )
        return findings

    async def judge_candidates(
        self,
        *,
        candidates: list[Finding],
        segments: list[Segment] | None = None,
        rules: list[EditorialRule] | None = None,
        entities: list[dict[str, Any]] | None = None,
        article_context: ArticleContext | None = None,
    ) -> list[Finding]:
        judged: list[Finding] = []
        _ = article_context  # available for future mock heuristics
        for finding in candidates:
            update: dict[str, Any] = {}
            if finding.decision in {
                Decision.BAN,
                Decision.HARD_WARNING,
                Decision.NEEDS_EDITOR_REVIEW,
            }:
                update["requires_editor_review"] = True
            if finding.confidence < 0.35:
                update["decision"] = Decision.NEEDS_EDITOR_REVIEW
                update["requires_editor_review"] = True
            judged.append(finding.model_copy(update=update) if update else finding)
        self._trace(
            phase="judge",
            system="mock judge — heuristic post-process",
            user=json.dumps(
                {
                    "candidates": [c.model_dump(mode="json") for c in candidates],
                    "rules": [r.model_dump(mode="json") for r in (rules or [])],
                    "entities": entities or [],
                    "segment_ids": [s.segment_id for s in (segments or [])],
                },
                ensure_ascii=False,
            ),
            raw=json.dumps(
                {"findings": [f.model_dump(mode="json") for f in judged]},
                ensure_ascii=False,
            ),
        )
        return judged

    async def repair_findings(
        self,
        *,
        findings: list[Finding],
        segments: list[Segment],
        validation_errors: dict[str, list[str]],
    ) -> list[Finding]:
        by_id = {s.segment_id: s for s in segments}
        repaired: list[Finding] = []
        for finding in findings:
            errors = validation_errors.get(finding.finding_id, [])
            if not errors:
                repaired.append(finding)
                continue
            # Drop findings whose span cannot exist in the segment.
            segment = by_id.get(finding.segment_id)
            if segment is None or finding.original_text not in segment.text:
                continue
            idx = segment.text.find(finding.original_text)
            repaired.append(
                finding.model_copy(
                    update={
                        "start_offset": idx,
                        "end_offset": idx + len(finding.original_text),
                        "validation_errors": [],
                        "requires_editor_review": True,
                    }
                )
            )
        self._trace(
            phase="repair",
            system="mock repair — realign offsets or drop",
            user=json.dumps(
                {
                    "findings": [f.model_dump(mode="json") for f in findings],
                    "validation_errors": validation_errors,
                },
                ensure_ascii=False,
            ),
            raw=json.dumps(
                {"findings": [f.model_dump(mode="json") for f in repaired]},
                ensure_ascii=False,
            ),
        )
        return repaired

    async def author_rules(self, *, text: str) -> list[EditorialRule]:
        pasted = parse_rules_paste(text)
        result = pasted if pasted else [free_text_to_rule_stub(text)]
        self._trace(
            phase="rule_author",
            system="mock rule author",
            user=text,
            raw=json.dumps(
                {"rules": [r.model_dump(mode="json") for r in result]},
                ensure_ascii=False,
            ),
        )
        return result
