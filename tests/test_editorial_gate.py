from __future__ import annotations

import pytest

from app.ai.mock_client import MockEditorialAIClient
from app.config import settings
from app.models.schemas import (
    ArticleContext,
    AttributionLink,
    Decision,
    Finding,
    FindingSource,
    Segment,
    Severity,
    Zone,
)
from app.models.schemas import ReviewRequest
from app.orchestration.review import ReviewOrchestrator
from app.postprocess.editorial_gate import (
    ATTRIBUTION_REASON,
    CLARITY_REASON,
    HEADLINE_REASON,
    POLICY_OFF,
    POLICY_RUN5,
    POLICY_RUN5B,
    editorial_gate_decision,
    gate_editorial_findings,
    normalize_editorial_gate_policy,
)


def _segment(
    text: str,
    *,
    segment_id: str = "S1",
    zone: Zone = Zone.BODY,
    sequence: int = 0,
) -> Segment:
    return Segment(
        segment_id=segment_id,
        document_id="D1",
        zone=zone,
        text=text,
        normalized_text=text,
        start_offset=0,
        end_offset=len(text),
        sequence=sequence,
    )


def _finding(
    *,
    category: str,
    original: str,
    explanation: str,
    segment_id: str = "S1",
    source: FindingSource = FindingSource.MOCK,
) -> Finding:
    return Finding(
        finding_id=f"F-{category}",
        document_id="D1",
        segment_id=segment_id,
        source=source,
        category=category,
        decision=Decision.NEEDS_EDITOR_REVIEW,
        severity=Severity.MEDIUM,
        original_text=original,
        suggested_text=None,
        start_offset=0,
        end_offset=len(original),
        explanation_ar=explanation,
        confidence=1.0,
    )


def _gate(
    finding: Finding,
    segments: list[Segment],
    context: ArticleContext | None = None,
    *,
    policy: str = "run5",
):
    return gate_editorial_findings(
        [finding],
        policy=policy,
        context=context or ArticleContext(),
        segments=segments,
    )


def test_r1_suppresses_vague_source_request():
    finding = _finding(
        category="attribution",
        original="مصادر محلية",
        explanation="مصدر مبهم يحتاج إلى تسمية أكثر دقة.",
    )
    kept, suppressed, audit = _gate(
        finding, [_segment("ذكرت مصادر محلية أن الاجتماع سيعقد غداً.")]
    )
    assert not kept
    assert suppressed
    assert audit[0]["reason_code"] == ATTRIBUTION_REASON
    assert f"editorial_gate:{ATTRIBUTION_REASON}" in suppressed[0].validation_errors


def test_r1_suppresses_claim_already_attributed_nearby():
    claim = "ستنخفض الأسعار في الربع المقبل"
    finding = _finding(
        category="attribution",
        original=claim,
        explanation="يحتاج الادعاء إلى إسناد واضح.",
    )
    context = ArticleContext(
        attribution_links=[
            AttributionLink(
                claim_span=claim,
                speaker="المتحدث",
                attribution_verb="قال",
                segment_id="S1",
            )
        ]
    )
    kept, suppressed, audit = _gate(
        finding,
        [_segment(f"قال المتحدث إن {claim}.")],
        context,
    )
    assert not kept and suppressed
    assert audit[0]["reason_code"] == ATTRIBUTION_REASON


def test_run5b_keeps_attribution_strength_certainty_escalation_criticals():
    # case-0005 / case-0038 style findings incorrectly suppressed by run5 R1.
    for original, explanation in (
        (
            "وأكد",
            "استخدام فعل التأكيد (أكد) مع مصدر واحد غير مسمى يبالغ في قوة الادعاء.",
        ),
        (
            "مؤكدًا",
            "استخدام كلمة 'مؤكدًا' منسوبة إلى 'التقرير' (وهو مصدر مبهم) قد يضفي درجة من اليقين.",
        ),
    ):
        finding = _finding(
            category="attribution_strength",
            original=original,
            explanation=explanation,
        )
        kept, suppressed, audit = _gate(
            finding,
            [_segment(f"{original} التقرير أن الاتفاق وشيك.")],
            policy="run5b",
        )
        assert kept == [finding]
        assert not suppressed
        assert audit[0]["decision"] == "keep"


def test_run5b_r2_suppresses_mechanical_long_paragraph_clarity():
    finding = _finding(
        category="clarity",
        original="نص طويل",
        explanation="مقطع طويل جداً قد يحتاج إعادة تقسيم.",
        source=FindingSource.MECHANICAL,
    )
    kept, suppressed, audit = _gate(
        finding, [_segment("نص طويل.")], policy="run5b"
    )
    assert not kept and suppressed
    assert audit[0]["reason_code"] == CLARITY_REASON


def test_run5b_r2_keeps_mechanical_digit_mix_clarity():
    finding = _finding(
        category="clarity",
        original="2",
        explanation="خلط بين الأرقام العربية واللاتينية في المقطع.",
        source=FindingSource.MECHANICAL,
    )
    kept, suppressed, audit = _gate(
        finding, [_segment("بلغت القيمة 2 و٤ معاً.")], policy="run5b"
    )
    assert kept == [finding]
    assert not suppressed
    assert audit[0]["decision"] == "keep"


def test_r4_suppresses_supported_headline_compression():
    headline = _segment(
        "ارتفاع صافي الأصول فوق مئتين بالمئة",
        segment_id="H1",
        zone=Zone.HEADLINE,
        sequence=0,
    )
    body = _segment(
        "أظهر التقرير ارتفاع صافي الأصول فوق مئتين بالمئة في الفترة ذاتها.",
        segment_id="B1",
        sequence=1,
    )
    finding = _finding(
        category="headline_body_mismatch",
        original="ارتفاع صافي الأصول فوق مئتين بالمئة",
        explanation="العنوان يغيّر مستوى اليقين أسلوبياً مع دعم المتن للادعاء.",
        segment_id="H1",
    )
    kept, suppressed, audit = _gate(finding, [headline, body])
    assert not kept and suppressed
    assert audit[0]["reason_code"] == HEADLINE_REASON


def test_run5b_r4_suppresses_only_proven_safe_compression():
    headline = _segment(
        "الفريق يعلن قائمته الجديدة",
        segment_id="H1",
        zone=Zone.HEADLINE,
        sequence=0,
    )
    body = _segment(
        "الفريق يعلن قائمته الجديدة للموسم في بيان اليوم.",
        segment_id="B1",
        sequence=1,
    )
    finding = _finding(
        category="headline_body_mismatch",
        original="الفريق يعلن قائمته الجديدة",
        explanation="العنوان يختصر صياغة المتن؛ اختصار أسلوبي فقط ولا يغير المعنى.",
        segment_id="H1",
    )
    kept, suppressed, audit = _gate(
        finding, [headline, body], policy="run5b"
    )
    assert not kept and suppressed
    assert audit[0]["policy_version"] == "run5b"
    assert audit[0]["rule_id"] == "R4"
    assert audit[0]["reason_code"] == HEADLINE_REASON


def test_run5b_r4_keeps_certainty_escalation_fail_open():
    headline = _segment(
        "صافي الأصول يتجاوز 200% حتى 2020",
        segment_id="H1",
        zone=Zone.HEADLINE,
        sequence=0,
    )
    body = _segment(
        "توقع تقرير ستاندرد آند بورز أن يتجاوز صافي الأصول 200% حتى 2020.",
        segment_id="B1",
        sequence=1,
    )
    finding = _finding(
        category="unsupported_certainty",
        original="صافي الأصول يتجاوز 200% حتى 2020",
        explanation="العنوان يقدم توقع التقرير كحقيقة مؤكدة بصوت الناشر.",
        segment_id="H1",
    )
    kept, suppressed, audit = _gate(finding, [headline, body], policy="run5b")
    assert kept == [finding]
    assert not suppressed
    assert audit[0]["decision"] == "keep"


def test_r4_keeps_material_conflict_and_unsupported_overstatement():
    headline = _segment(
        "أطلق سراح ستة مواطنين",
        segment_id="H1",
        zone=Zone.HEADLINE,
        sequence=0,
    )
    body = _segment(
        "قالت الوزارة إن المواطنين ما زالوا محتجزين لدى السلطات المحلية.",
        segment_id="B1",
        sequence=1,
    )
    contradiction = _finding(
        category="headline_body_mismatch",
        original="أطلق سراح ستة مواطنين",
        explanation="العنوان يقول إطلاق سراح بينما المتن يقول إنهم محتجزون.",
        segment_id="H1",
    )
    kept, suppressed, audit = _gate(contradiction, [headline, body])
    assert kept == [contradiction]
    assert not suppressed and not audit

    unsupported = _finding(
        category="headline_body_mismatch",
        original="مشروعات بقيمة 8 مليارات",
        explanation="ادعاء مادي غير مدعوم ولا يحتوي المتن على القيمة المذكورة.",
        segment_id="H1",
    )
    kept, suppressed, audit = _gate(unsupported, [headline, body])
    assert kept == [unsupported]
    assert not suppressed and not audit


def test_run5b_accepted_correction_si40_fails_open_when_support_uncertain():
    headline_text = "مايكروسوفت تفتح برنامج Windows Live Messenger"
    headline = _segment(
        headline_text,
        segment_id="H1",
        zone=Zone.HEADLINE,
        sequence=0,
    )
    body = _segment(
        "أتاحت شركة مايكروسوفت برنامج Windows Live Messenger لكافة المستخدمين "
        "الذين يتمتعون بعضوية Microsoft Passport، وقد كان الدخول يتطلب دعوة.",
        segment_id="B1",
        sequence=1,
    )
    finding = _finding(
        category="headline_body_mismatch",
        original=headline_text,
        explanation=(
            "العنوان يفيد بأن مايكروسوفت تفتح البرنامج بشكل قاطع، بينما كان "
            "يتطلب دعوة والخبر ليس إعلاناً رسمياً."
        ),
        segment_id="H1",
    )
    kept, suppressed, audit = _gate(finding, [headline, body], policy="run5b")
    # Fail-open: official/hedged body cues prevent hard compression suppression.
    assert kept == [finding]
    assert not suppressed
    assert audit[0]["decision"] == "keep"


@pytest.mark.parametrize(
    ("headline_text", "body_text", "explanation"),
    [
        (
            "ليفاندوفسكي ينتقل إلى بايرن ميونخ",
            "كشف مقدم البرنامج أن اللاعب سيعلن انتقاله في الثاني من يناير.",
            "يزعم وجود تناقض لأن اللاعب نفى صحة التقارير لاحقاً.",
        ),
        (
            "تظاهرات تطالب قطر بمنع ترحيل مسلم من الإيغور إلى الصين",
            "تظاهر ناشطون للمطالبة بعدم إبعاد الناشط خوفاً على حياته.",
            "يزعم أن السلطات توقفت عن ترحيل الناشط في متن غير متاح.",
        ),
    ],
)
def test_accepted_uncertain_headline_corrections_remain_visible_without_context(
    headline_text: str,
    body_text: str,
    explanation: str,
):
    headline = _segment(
        headline_text,
        segment_id="H1",
        zone=Zone.HEADLINE,
        sequence=0,
    )
    body = _segment(body_text, segment_id="B1", sequence=1)
    finding = _finding(
        category="headline_body_mismatch",
        original=headline_text,
        explanation=explanation,
        segment_id="H1",
    )
    kept, suppressed, audit = _gate(finding, [headline, body])
    assert kept == [finding]
    assert not suppressed and not audit


@pytest.mark.parametrize("source_index", [128, 129])
def test_accepted_numeric_corrections_are_not_gate_targets(source_index: int):
    finding = _finding(
        category="numeric_contradiction",
        original="3 انتصارات",
        explanation=f"التصحيح المقبول للمصدر {source_index}: 3 مطلوبة و8 متحققة.",
    )
    kept, suppressed, audit = _gate(
        finding,
        [_segment("حقق ثمانية انتصارات ويحتاج ثلاثة انتصارات لكسر الرقم.")],
    )
    assert kept == [finding]
    assert not suppressed and not audit


def test_numeric_punctuation_and_other_categories_pass_through():
    segments = [_segment("بلغ العدد 8 بدلاً من 3.")]
    for category in ("numeric_contradiction", "temporal_contradiction", "punctuation", "spelling"):
        finding = _finding(
            category=category,
            original="8",
            explanation="تناقض عددي واضح.",
        )
        kept, suppressed, audit = _gate(finding, segments)
        assert kept == [finding]
        assert not suppressed and not audit


def test_policy_off_preserves_all_findings():
    finding = _finding(
        category="clarity",
        original="فقرة",
        explanation="مقطع طويل جداً قد يحتاج إعادة تقسيم.",
    )
    kept, suppressed, audit = _gate(finding, [_segment("فقرة طويلة.")], policy="off")
    assert kept == [finding]
    assert not suppressed and not audit


def test_policy_versions_are_distinct_and_unknown_fails_off():
    assert normalize_editorial_gate_policy("off") == POLICY_OFF
    assert normalize_editorial_gate_policy("run5") == POLICY_RUN5
    assert normalize_editorial_gate_policy("run5b") == POLICY_RUN5B
    assert normalize_editorial_gate_policy("future") == POLICY_OFF


def test_frozen_run5_behavior_is_unchanged_at_known_boundaries():
    mechanical = _finding(
        category="clarity",
        original="نص طويل",
        explanation="مقطع طويل جداً قد يحتاج إعادة تقسيم.",
        source=FindingSource.MECHANICAL,
    )
    kept, suppressed, audit = _gate(
        mechanical, [_segment("نص طويل.")], policy="run5"
    )
    assert kept == [mechanical] and not suppressed and not audit

    strength = _finding(
        category="attribution_strength",
        original="وأكد",
        explanation="استخدام فعل التأكيد مع مصدر واحد غير مسمى يبالغ في قوة الادعاء.",
    )
    kept, suppressed, audit = _gate(
        strength, [_segment("وأكد التقرير أن الاتفاق وشيك.")], policy="run5"
    )
    assert not kept and suppressed
    assert audit[0]["reason_code"] == ATTRIBUTION_REASON

    headline = _segment(
        "صافي الأصول يتجاوز 200% حتى 2020",
        segment_id="H1",
        zone=Zone.HEADLINE,
        sequence=0,
    )
    body = _segment(
        "توقع تقرير أن يتجاوز صافي الأصول 200% حتى 2020.",
        segment_id="B1",
        sequence=1,
    )
    certainty = _finding(
        category="unsupported_certainty",
        original="صافي الأصول يتجاوز 200% حتى 2020",
        explanation="العنوان يقدم توقع التقرير كحقيقة مؤكدة بصوت الناشر.",
        segment_id="H1",
    )
    kept, suppressed, audit = _gate(
        certainty, [headline, body], policy="run5"
    )
    assert not kept and suppressed
    assert audit[0]["reason_code"] == HEADLINE_REASON


def test_run5b_normalizes_arabic_generic_clarity():
    finding = _finding(
        category="clarity",
        original="نص",
        explanation="مَقْطَعٌ طَوِيلٌ جِدًّا قَدْ يَحْتَاجُ إِعَادَةَ تَقْسِيمٍ.",
        source=FindingSource.MECHANICAL,
    )
    kept, suppressed, audit = _gate(
        finding, [_segment("نص طويل.")], policy="run5b"
    )
    assert not kept and suppressed
    assert audit[0]["reason_code"] == CLARITY_REASON


@pytest.mark.parametrize(
    "explanation",
    [
        "مرجع الضمير غير واضح بين الوزير والمتحدث.",
        "يتناقض اسم المنظمة مع المذكور في المتن.",
        "المكان في العنوان مدينة أخرى.",
        "دور اللاعب في العنوان يختلف عن دوره في المتن.",
        "الفاعل والمفعول معكوسان فتغير معنى الحدث.",
        "النتيجة المذكورة عكس outcome الحدث في المتن.",
        "العنوان ينفي ما يثبته المتن.",
        "العنوان يحول احتمالاً إلى يقين.",
        "نسبة القول إلى مصدر مختلف.",
        "الاقتباس المباشر تغير معناه.",
    ],
)
def test_run5b_r4_keeps_material_semantic_differences(explanation: str):
    headline = _segment(
        "عنوان الخبر",
        segment_id="H1",
        zone=Zone.HEADLINE,
        sequence=0,
    )
    body = _segment("عنوان الخبر في المتن.", segment_id="B1", sequence=1)
    finding = _finding(
        category="headline_body_mismatch",
        original="عنوان الخبر",
        explanation=explanation,
        segment_id="H1",
    )
    kept, suppressed, audit = _gate(
        finding, [headline, body], policy="run5b"
    )
    assert kept == [finding] and not suppressed
    assert audit[0]["decision"] == "keep"
    assert audit[0]["rule_id"] == "R4"
    assert audit[0]["reason_code"] == "headline_material_or_not_proven_safe"


def test_run5b_diagnostics_cover_kept_and_suppressed_findings():
    generic = _finding(
        category="clarity",
        original="فقرة",
        explanation="الفقرة طويلة ويمكن تبسيط الصياغة.",
        source=FindingSource.MECHANICAL,
    )
    concrete = _finding(
        category="clarity",
        original="هو",
        explanation="مرجع الضمير هو غير واضح.",
    ).model_copy(update={"finding_id": "F-concrete"})
    kept, suppressed, audit = gate_editorial_findings(
        [generic, concrete],
        policy="run5b",
        context=ArticleContext(),
        segments=[_segment("فقرة طويلة وهو غير واضح.")],
    )
    assert kept == [concrete]
    assert len(suppressed) == 1
    assert {event["decision"] for event in audit} == {"keep", "suppress"}
    for event in audit:
        assert event["policy_version"] == "run5b"
        assert event["rule_id"] == "R2"
        assert event["reason_code"]
        assert event["matched_evidence"]


def test_run5b_numeric_date_and_punctuation_are_unconditional_pass_through():
    for category in (
        "numeric_contradiction",
        "temporal_contradiction",
        "date",
        "punctuation",
    ):
        finding = _finding(
            category=category,
            original="2026",
            explanation="مقطع طويل وقد يحتاج توضيحاً.",
        )
        kept, suppressed, audit = _gate(
            finding, [_segment("2026")], policy="run5b"
        )
        assert kept == [finding] and not suppressed
        assert audit[0]["decision"] == "keep"
        if category != "punctuation":
            assert audit[0]["reason_code"] == "numeric_or_date_protected"


def test_replay_matches_live_gate_decisions():
    from scripts.replay_editorial_gates import _finding_from_row, _segments_for_row
    from app.context.article_context import extract_article_context
    from app.postprocess.editorial_gate import gate_editorial_findings, suppression_reason

    row = {
        "article_id": "D1",
        "finding_id": "F1",
        "category": "clarity",
        "source": "mechanical",
        "original_text": "نص",
        "explanation_ar": "مقطع طويل جداً قد يحتاج إعادة تقسيم.",
        "headline": "عنوان",
        "body_excerpt": "نص طويل.",
        "decision": "soft_warning",
        "severity": "low",
        "confidence": 1.0,
        "segment_id": "SEG-001",
        "start_offset": 0,
        "end_offset": 3,
    }
    finding = _finding_from_row(row)
    document, segments = _segments_for_row(row)
    context = extract_article_context(document, segments)
    reason = suppression_reason(
        finding, policy="run5b", context=context, segments=segments
    )
    kept, suppressed, audit = gate_editorial_findings(
        [finding], policy="run5b", context=context, segments=segments
    )
    assert reason == CLARITY_REASON
    assert not kept and suppressed and audit[0]["reason_code"] == reason


@pytest.mark.asyncio
async def test_orchestrator_records_reason_code_and_keeps_raw_trace(monkeypatch):
    monkeypatch.setattr(settings, "editorial_gate_policy", "run5")

    async def fake_discover(**kwargs):
        segment = kwargs["segments"][0]
        span = "وسائل إعلام لبنانية"
        idx = segment.text.find(span)
        return [
            Finding(
                finding_id="FND-AI-ATTR",
                document_id=segment.document_id,
                segment_id=segment.segment_id,
                source=FindingSource.MOCK,
                category="attribution",
                decision=Decision.NEEDS_EDITOR_REVIEW,
                severity=Severity.MEDIUM,
                original_text=span,
                suggested_text=None,
                start_offset=idx,
                end_offset=idx + len(span),
                explanation_ar="مصدر مبهم يحتاج تسمية أوضح.",
                confidence=1.0,
            )
        ]

    class _Client:
        last_call_trace = {
            "system_prompt": "mock",
            "user_payload": "{}",
            "raw_response": '{"findings":[]}',
        }

        async def discover_candidates(self, **kwargs):
            return await fake_discover(**kwargs)

        async def judge_candidates(self, **kwargs):
            return kwargs["candidates"]

        async def repair_findings(self, **kwargs):
            return []

    monkeypatch.setattr(
        "app.orchestration.review.gate_gemini_findings",
        lambda **kwargs: (kwargs["gemini_findings"], []),
    )
    monkeypatch.setattr(
        "app.orchestration.review.adjudicate_findings",
        lambda **kwargs: (kwargs["findings"], []),
    )
    orchestrator = ReviewOrchestrator(ai_client=_Client())
    response = await orchestrator.review(
        ReviewRequest(
            document_id="D-R1",
            headline="خبر منسوب",
            body="ذكرت وسائل إعلام لبنانية أن الاجتماع سيعقد غداً.",
        )
    )
    errors = [
        error
        for finding in response.rejected_findings
        for error in finding.validation_errors
    ]
    assert f"editorial_gate:{ATTRIBUTION_REASON}" in errors
    step = next(item for item in response.pipeline_log if item.step_id == "editorial_gate")
    assert step.output_summary["reason_counts"].get(ATTRIBUTION_REASON, 0) >= 1
    judge = next(item for item in response.pipeline_log if item.step_id == "judge")
    assert judge.raw_response is not None


@pytest.mark.asyncio
async def test_orchestrator_suppresses_mechanical_long_clarity(monkeypatch):
    monkeypatch.setattr(settings, "editorial_gate_policy", "run5b")
    orchestrator = ReviewOrchestrator(ai_client=MockEditorialAIClient())
    long_body = "كلمة " * 600
    response = await orchestrator.review(
        ReviewRequest(
            document_id="D-R2",
            headline="عنوان قصير",
            body=long_body,
        )
    )
    clarity_errors = [
        error
        for finding in response.rejected_findings
        for error in finding.validation_errors
        if error.startswith("editorial_gate:")
    ]
    assert f"editorial_gate:{CLARITY_REASON}" in clarity_errors
    assert all(
        (finding.category or "").lower() != "clarity"
        or "خلط" in (finding.explanation_ar or "")
        for finding in response.findings
        if (finding.category or "").lower() == "clarity"
    ) or not any(
        (finding.category or "").lower() == "clarity"
        and "مقطع طويل" in (finding.explanation_ar or "")
        for finding in response.findings
    )


@pytest.mark.asyncio
async def test_orchestrator_frozen_run5_leaves_mechanical_clarity_visible(monkeypatch):
    monkeypatch.setattr(settings, "editorial_gate_policy", "run5")
    orchestrator = ReviewOrchestrator(ai_client=MockEditorialAIClient())
    response = await orchestrator.review(
        ReviewRequest(
            document_id="D-RUN5-FROZEN",
            headline="عنوان قصير",
            body="كلمة " * 600,
        )
    )
    assert any(
        (finding.category or "").lower() == "clarity"
        and finding.source == FindingSource.MECHANICAL
        and "مقطع طويل" in (finding.explanation_ar or "")
        for finding in response.findings
    )
    assert not any(
        f"editorial_gate:{CLARITY_REASON}" in (finding.validation_errors or [])
        for finding in response.rejected_findings
    )
