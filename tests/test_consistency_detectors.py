from pathlib import Path

from app.config import ROOT_DIR
from app.mechanical.consistency import run_consistency_detectors
from app.mechanical.editorial_detectors import (
    load_editorial_phrases,
    run_editorial_detectors,
)
from app.models.schemas import Document
from app.segmentation.article import segment_article


def _marfa_doc() -> Document:
    article = (ROOT_DIR / "data" / "evaluation" / "marfa_article.json").read_text(
        encoding="utf-8"
    )
    import json

    payload = json.loads(article)
    headline = next(s["text"] for s in payload["sections"] if s["surface"] == "headline")
    body = "\n".join(s["text"] for s in payload["sections"] if s["surface"] != "headline")
    return Document(document_id="custom-marfa-chaos-v1", headline=headline, body=body)


def test_grammar_and_claim_detectors_on_marfa():
    segments = segment_article(_marfa_doc())
    phrases = load_editorial_phrases(ROOT_DIR / "data" / "lexicons" / "editorial_phrases.json")
    grammar = load_editorial_phrases(ROOT_DIR / "data" / "lexicons" / "grammar_patterns.json")
    editorial = run_editorial_detectors(segments, phrases, grammar_lexicon=grammar)
    rules = {rid for f in editorial for rid in f.rule_ids}
    spans = {f.original_text for f in editorial}

    assert "MECH-GRAMMAR" in rules
    assert "قام المتظاهرين" in spans
    assert "لم يتسنى" in spans
    assert "أعتبر آخرين" in spans
    assert "إلى مزيداً" in spans
    assert "R_EVIDENCE_WEAK" in rules
    assert "R_OVERGENERALIZE" in rules
    assert "R_PUBLISHER_FACT" in rules


def test_consistency_detectors_on_marfa():
    segments = segment_article(_marfa_doc())
    findings = run_consistency_detectors(segments)
    rules = {rid for f in findings for rid in f.rule_ids}
    assert "CONS-NUMBER" in rules
    assert "CONS-DATE" in rules
    assert "CONS-NAME" in rules
