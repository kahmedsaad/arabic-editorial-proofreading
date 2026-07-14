"""Run4 punctuation policy / gate / metrics regression tests (no GCP)."""

from __future__ import annotations

from app.config import settings
from app.evaluation.clean_metrics import compute_clean_fp_metrics
from app.mechanical.checks import run_mechanical_checks
from app.models.schemas import (
    Decision,
    Finding,
    FindingSource,
    Segment,
    Severity,
    Zone,
)
from app.postprocess.punctuation_gate import (
    dedupe_punctuation_findings,
    gate_punctuation_findings,
    should_show_punctuation_finding,
)
from app.postprocess.punctuation_policy import normalize_policy
from app.segmentation.article import segment_article
from app.models.schemas import Document


def _seg(text: str, *, zone: Zone = Zone.BODY, sid: str = "SEG-001") -> Segment:
    return Segment(
        segment_id=sid,
        document_id="DOC",
        zone=zone,
        text=text,
        normalized_text=text,
        start_offset=0,
        end_offset=len(text),
        sequence=0,
    )


def _punct_finding(**kwargs) -> Finding:
    defaults = dict(
        finding_id="FND-M-0001",
        document_id="DOC",
        segment_id="SEG-001",
        source=FindingSource.MECHANICAL,
        category="punctuation",
        decision=Decision.REPLACE,
        severity=Severity.LOW,
        original_text="،،",
        suggested_text="،",
        start_offset=0,
        end_offset=2,
        rule_ids=["MECH-PUNCT-DUP"],
        explanation_ar="تكرار غير ضروري لعلامة الترقيم.",
        confidence=1.0,
        punctuation_subtype="repeated_punctuation",
    )
    defaults.update(kwargs)
    return Finding(**defaults)


def test_policy_normalize_default_strict():
    assert normalize_policy(None) == "strict"
    assert normalize_policy("STRICT") == "strict"
    assert normalize_policy("off") == "off"
    assert settings.punctuation_policy in {"off", "strict", "full"}


def test_off_suppresses_all_punctuation():
    f = _punct_finding()
    show, reason = should_show_punctuation_finding(
        f, policy="off", segment_text="قال المسؤول،، إن القرار نهائي."
    )
    assert show is False
    assert reason == "suppressed_policy_off"


def test_strict_allows_repeated_punctuation_arabic():
    text = "قال المسؤول،، إن القرار نهائي."
    f = _punct_finding(original_text="،،", start_offset=text.find("،،"), end_offset=text.find("،،") + 2)
    show, reason = should_show_punctuation_finding(f, policy="strict", segment_text=text)
    assert show is True
    assert reason == "allowed_objective_error"


def test_strict_allows_unbalanced_quotes():
    text = '"قال المسؤول إن القرار نهائي.'
    f = _punct_finding(
        finding_id="FND-M-QUOTE",
        original_text='"',
        start_offset=0,
        end_offset=1,
        rule_ids=["MECH-QUOTE"],
        punctuation_subtype="unbalanced_quotes",
        suggested_text=None,
        decision=Decision.SOFT_WARNING,
        explanation_ar="علامة فتح اقتباس دون إغلاق مطابق.",
    )
    show, reason = should_show_punctuation_finding(f, policy="strict", segment_text=text)
    assert show is True
    assert reason == "allowed_objective_error"


def test_strict_suppresses_optional_comma_style():
    text = "قال المسؤول، إن القرار نهائي"
    f = _punct_finding(
        original_text="،",
        suggested_text="، ",
        start_offset=text.find("،"),
        end_offset=text.find("،") + 1,
        rule_ids=["MECH-PUNCT-AFTER"],
        punctuation_subtype="malformed_spacing",
        explanation_ar="تنقص مسافة بعد علامة الترقيم.",
        decision=Decision.SUGGEST,
    )
    show, reason = should_show_punctuation_finding(f, policy="strict", segment_text=text)
    assert show is False
    assert reason in {"suppressed_optional_style", "suppressed_low_confidence"}


def test_strict_suppresses_headline_final_period_style():
    text = "الجيش يعلن السيطرة على المنطقة"
    seg = _seg(text, zone=Zone.HEADLINE, sid="SEG-H")
    f = _punct_finding(
        segment_id="SEG-H",
        original_text=text[-1],
        suggested_text=text[-1] + ".",
        start_offset=len(text) - 1,
        end_offset=len(text),
        rule_ids=[],
        punctuation_subtype=None,
        explanation_ar="يفضل وضع نقطة في نهاية العنوان.",
        decision=Decision.SUGGEST,
    )
    show, reason = should_show_punctuation_finding(
        f, policy="strict", segment_text=text, zone=Zone.HEADLINE
    )
    assert show is False
    assert reason == "suppressed_headline_style"


def test_full_preserves_spacing_finding():
    text = "كلمة .أخرى"
    f = _punct_finding(
        original_text=" .",
        suggested_text=".",
        start_offset=text.find(" ."),
        end_offset=text.find(" .") + 2,
        rule_ids=["MECH-PUNCT-SPACE"],
        punctuation_subtype="malformed_spacing",
        explanation_ar="مسافة غير صحيحة قبل علامة الترقيم.",
    )
    show, reason = should_show_punctuation_finding(f, policy="full", segment_text=text)
    assert show is True
    assert reason == "allowed_full_policy"


def test_quote_internal_style_suppressed_unless_structural():
    text = 'قال: «مرحبا، عالم»'
    # Stylistic comma spacing inside quotes
    idx = text.find("،")
    f = _punct_finding(
        original_text="،",
        suggested_text="، ",
        start_offset=idx,
        end_offset=idx + 1,
        rule_ids=["MECH-PUNCT-AFTER"],
        punctuation_subtype="malformed_spacing",
        explanation_ar="تنقص مسافة بعد علامة الترقيم.",
        decision=Decision.REPLACE,
    )
    show, reason = should_show_punctuation_finding(f, policy="strict", segment_text=text)
    assert show is False
    assert reason == "suppressed_inside_quote"


def test_broken_quote_delimiter_still_shown():
    text = '"قال المسؤول إن القرار نهائي.'
    findings = run_mechanical_checks([_seg(text)])
    quote_findings = [f for f in findings if "MECH-QUOTE" in f.rule_ids]
    assert quote_findings
    kept, suppressed, _ = gate_punctuation_findings(
        quote_findings, policy="strict", segments=[_seg(text)]
    )
    assert kept
    assert not any(f.finding_id == kept[0].finding_id for f in suppressed)


def test_suggestions_do_not_rewrite_quote_when_gated():
    text = 'قال: «مرحبا عالم»'
    f = _punct_finding(
        original_text="مرحبا",
        suggested_text="أهلا",
        start_offset=text.find("مرحبا"),
        end_offset=text.find("مرحبا") + len("مرحبا"),
        rule_ids=[],
        punctuation_subtype="quote_internal_style",
        decision=Decision.REPLACE,
    )
    show, reason = should_show_punctuation_finding(f, policy="strict", segment_text=text)
    assert show is False


def test_dedupe_prefers_mechanical_over_gemini():
    mech = _punct_finding(finding_id="FND-M-1", source=FindingSource.MECHANICAL)
    gem = _punct_finding(
        finding_id="FND-AI-1",
        source=FindingSource.GEMINI,
        severity=Severity.MEDIUM,
    )
    kept, audit = dedupe_punctuation_findings([gem, mech])
    punct = [f for f in kept if f.category == "punctuation"]
    assert len(punct) == 1
    assert punct[0].finding_id == "FND-M-1"
    assert any(a.get("reason") == "suppressed_duplicate" for a in audit)


def test_dedupe_identical_offsets_collapse():
    a = _punct_finding(finding_id="FND-M-1")
    b = _punct_finding(finding_id="FND-M-2")
    kept, audit = dedupe_punctuation_findings([a, b])
    punct = [f for f in kept if f.category == "punctuation"]
    assert len(punct) == 1
    assert audit


def test_metrics_split_editorial_vs_punctuation():
    articles = [
        ["punctuation", "punctuation"],
        ["attribution"],
        [],
        ["clarity", "punctuation"],
    ]
    m = compute_clean_fp_metrics(article_finding_categories=articles)
    assert m["clean_fp_rate_all"] == 0.75
    assert m["clean_fp_rate_editorial_only"] == 0.5
    assert m["clean_fp_rate_punctuation_only"] == 0.5
    assert m["zero_finding_clean_article_rate"] == 0.25
    assert m["zero_editorial_finding_clean_article_rate"] == 0.5
    assert m["findings_per_article_punctuation_only"] == 0.75
    assert m["findings_per_article_editorial_only"] == 0.5


def test_mechanical_arabic_cases_policy_outcomes():
    # Repeated punctuation should surface under full/strict via detector
    doc = Document(
        document_id="DOC",
        headline="الجيش يعلن السيطرة على المنطقة",
        body="قال المسؤول،، إن القرار نهائي.",
    )
    segs = segment_article(doc)
    findings = run_mechanical_checks(segs)
    kept_strict, suppressed_strict, _ = gate_punctuation_findings(
        findings, policy="strict", segments=segs
    )
    kept_off, _, _ = gate_punctuation_findings(findings, policy="off", segments=segs)
    assert all(f.category != "punctuation" for f in kept_off)
    # Headline without final period should not yield shown punct findings in strict
    headline_punct = [
        f
        for f in kept_strict
        if f.category == "punctuation"
        and any(s.segment_id == f.segment_id and s.zone == Zone.HEADLINE for s in segs)
    ]
    assert headline_punct == []
    # Body repeated punct allowed
    assert any(
        f.punctuation_subtype == "repeated_punctuation" or "،،" in (f.original_text or "")
        for f in kept_strict
        if f.category == "punctuation"
    )
    # Optional comma style body should be suppressible relative to full
    doc2 = Document(document_id="DOC2", headline="خبر", body="قال المسؤول، إن القرار نهائي")
    segs2 = segment_article(doc2)
    f2 = run_mechanical_checks(segs2)
    full_kept, _, _ = gate_punctuation_findings(f2, policy="full", segments=segs2)
    strict_kept, _, _ = gate_punctuation_findings(f2, policy="strict", segments=segs2)
    full_punct = [f for f in full_kept if f.category == "punctuation"]
    strict_punct = [f for f in strict_kept if f.category == "punctuation"]
    assert len(strict_punct) <= len(full_punct)
