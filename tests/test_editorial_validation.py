from pathlib import Path

from app.evaluation.editorial import load_editorial_golden, score_editorial_findings

ROOT = Path(__file__).resolve().parents[1]


def test_editorial_golden_loads():
    expectations = load_editorial_golden(ROOT / "data" / "evaluation" / "golden_editorial.jsonl")
    assert len(expectations) == 6
    assert any(e.must_not_rewrite for e in expectations)


def test_editorial_scorecard_mock_shape():
    expectations = load_editorial_golden(ROOT / "data" / "evaluation" / "golden_editorial.jsonl")
    findings = [
        {
            "original_text": "مقاتليه",
            "decision": "hard_warning",
            "rule_ids": ["R_DESC_NONSTATE"],
            "suggested_text": "عناصره",
        },
        {
            "original_text": "منظمة إرهابية",
            "decision": "needs_editor_review",
            "rule_ids": ["R_TERROR_LABEL"],
            "suggested_text": None,
        },
    ]
    card = score_editorial_findings(
        client="unit",
        expectations=expectations,
        findings=findings,
    )
    assert card.span_hits >= 2
    assert card.to_dict()["span_recall"] > 0
