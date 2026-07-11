from pathlib import Path

from app.config import ROOT_DIR
from app.mechanical.editorial_detectors import (
    dedupe_findings,
    load_editorial_phrases,
    run_editorial_detectors,
)
from app.models.schemas import Decision, Document, Finding, FindingSource, Severity
from app.segmentation.article import segment_article


def test_editorial_detectors_hit_golden_spans():
    doc = Document(
        document_id="DOC-ED",
        headline="حزب الله ربما يرد بعد مقتل أحد مقاتليه في غارة إسرائيلية",
        body=(
            "صورة للميليشيا المدعومة من الخارج لترهيب الحدود الإسرائيلية.\n"
            "قالت وسائل إعلام لبنانية إن الجيش الإسرائيلي شن غارة.\n"
            "وقالت الجماعة إن \"المقاومة لن تسكت على هذا العدوان\".\n"
            "ونقلت رويترز عن مصدر أمني تأكيده أن الغارة أسفرت عن قتلى.\n"
            "ووصف وزير حزب الله بأنه \"منظمة إرهابية\"."
        ),
    )
    segments = segment_article(doc)
    lexicon = load_editorial_phrases(ROOT_DIR / "data" / "lexicons" / "editorial_phrases.json")
    findings = run_editorial_detectors(segments, lexicon)

    by_rule: set[str] = set()
    for finding in findings:
        by_rule.update(finding.rule_ids)
        segment = next(s for s in segments if s.segment_id == finding.segment_id)
        assert segment.text[finding.start_offset : finding.end_offset] == finding.original_text

    for rule_id in (
        "R_DESC_NONSTATE",
        "R_SOURCE_VAGUE",
        "R_ATTR_CONFIRMATION",
        "R_LOADED_FRAME",
        "R_TERROR_LABEL",
        "R03",
    ):
        assert rule_id in by_rule


def test_dedupe_prefers_harder_decision():
    soft = Finding(
        finding_id="A",
        document_id="D",
        segment_id="S",
        source=FindingSource.GEMINI,
        category="attribution",
        decision=Decision.SOFT_WARNING,
        severity=Severity.LOW,
        original_text="وسائل إعلام لبنانية",
        start_offset=0,
        end_offset=19,
        rule_ids=["R_SOURCE_VAGUE"],
        explanation_ar="x",
        confidence=0.5,
    )
    hard = Finding(
        finding_id="FND-E-0001",
        document_id="D",
        segment_id="S",
        source=FindingSource.MECHANICAL,
        category="attribution",
        decision=Decision.HARD_WARNING,
        severity=Severity.HIGH,
        original_text="وسائل إعلام لبنانية",
        start_offset=0,
        end_offset=19,
        rule_ids=["R_SOURCE_VAGUE"],
        explanation_ar="y",
        confidence=0.95,
    )
    out = dedupe_findings([soft, hard])
    assert len(out) == 1
    assert out[0].decision == Decision.HARD_WARNING
