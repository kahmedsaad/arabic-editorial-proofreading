from pathlib import Path

from app.mechanical.checks import load_spelling_replacements, run_mechanical_checks
from app.models.schemas import Document
from app.segmentation.article import segment_article

ROOT = Path(__file__).resolve().parents[1]


def test_mechanical_checks_detect_common_issues():
    doc = Document(
        document_id="DOC-M",
        headline="خبر عاجل!!",
        body="قال قال المتحدث إن الوضع  مستقر . وفيه مسؤلية كبيرة.",
    )
    segments = segment_article(doc)
    replacements = load_spelling_replacements(ROOT / "data" / "spelling" / "replacements.json")
    findings = run_mechanical_checks(segments, replacements)

    categories = {f.category for f in findings}
    assert "repetition" in categories
    assert "punctuation" in categories
    assert "spelling" in categories

    for finding in findings:
        segment = next(s for s in segments if s.segment_id == finding.segment_id)
        assert segment.text[finding.start_offset : finding.end_offset] == finding.original_text
