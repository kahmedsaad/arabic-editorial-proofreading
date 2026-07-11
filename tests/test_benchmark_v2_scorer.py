"""Unit tests for benchmark_v2 scorer (synthetic gold — no engine changes)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark_v2.private.scorer.matching import (
    decision_match,
    exact_span_match,
    explanation_keyword_match,
    partial_span_match,
    score_gold_against_engine,
    suggestion_is_safe,
)
from benchmark_v2.private.scorer.report_html import render_html_report
from benchmark_v2.private.scorer.schemas import (
    BenchmarkCase,
    EngineCaseOutput,
    EngineFinding,
    ForbiddenFinding,
    GoldCase,
    GoldFinding,
)
from benchmark_v2.private.scorer.score import (
    consistency_across_runs,
    score_case,
    score_outputs,
    score_repeated_runs,
    write_json_report,
)


@pytest.fixture
def gold_finding() -> GoldFinding:
    return GoldFinding(
        category="unsupported_certainty",
        severity_band=["high", "critical"],
        segment_zone="headline",
        required_span_any=["تكشف تورط", "تورط مسؤولين"],
        acceptable_decisions=["hard_warning", "needs_editor_review"],
        suggestion_required=False,
        must_explain=["تحقيقات أولية", "اتهامات رسمية"],
    )


def test_benchmark_case_has_no_gold_fields():
    case = BenchmarkCase(case_id="case-0001", headline="ع", body="ب")
    dumped = case.model_dump()
    assert "expected_findings" not in dumped
    assert "forbidden_findings" not in dumped


def test_exact_and_partial_span_match():
    assert exact_span_match(["تكشف تورط"], "تكشف تورط")
    ok, ratio = partial_span_match(["تكشف تورط"], "تحقيقات تكشف تورط مسؤولين")
    assert ok
    assert ratio >= 0.25


def test_category_severity_decision_explanation(gold_finding: GoldFinding):
    engine = EngineFinding(
        category="unsupported_certainty",
        decision="hard_warning",
        severity="high",
        original_text="تكشف تورط",
        explanation_ar="التحقيقات أولية ولم توجه اتهامات رسمية.",
    )
    detail = score_gold_against_engine(gold_finding, engine)
    assert detail["matched"] is True
    assert detail["exact_span"] is True
    assert detail["category_match"] is True
    assert detail["severity_band_match"] is True
    assert detail["decision_match"] is True
    assert detail["explanation_keyword_match"] is True
    assert decision_match(gold_finding, engine)
    assert explanation_keyword_match(gold_finding, engine)


def test_unsafe_suggestion_penalty(gold_finding: GoldFinding):
    engine = EngineFinding(
        category="unsupported_certainty",
        decision="replace",
        severity="high",
        original_text="تكشف تورط",
        suggested_text="تشير إلى اشتباه",
        explanation_ar="تحقيقات أولية واتهام ات رسمية",
    )
    # Fix explanation to include keywords
    engine.explanation_ar = "التحقيقات أولية دون اتهامات رسمية"
    assert suggestion_is_safe(gold_finding, engine) is False
    detail = score_gold_against_engine(gold_finding, engine)
    assert detail["suggestion_safe"] is False


def test_false_positive_and_forbidden_penalties():
    gold = GoldCase(
        case_id="case-x",
        expected_findings=[],
        forbidden_findings=[
            ForbiddenFinding(span="جدية", reason="Quoted attribution; do not rewrite.")
        ],
        metadata={"clean_case": True, "contains_critical_issue": False},
    )
    output = EngineCaseOutput(
        case_id="case-x",
        findings=[
            EngineFinding(
                category="loaded_framing",
                decision="replace",
                severity="medium",
                original_text="جدية",
                suggested_text="مهمة",
                explanation_ar="إعادة صياغة",
            )
        ],
        latency_ms=12.0,
    )
    scored = score_case(gold, output)
    assert scored.false_positives >= 1
    assert scored.forbidden_hits >= 1
    assert scored.clean_case is True


def test_score_outputs_end_to_end(tmp_path: Path):
    gold_dir = tmp_path / "gold"
    gold_dir.mkdir()
    gold = GoldCase(
        case_id="case-0001",
        expected_findings=[
            GoldFinding(
                category="publisher_voice",
                severity_band=["high"],
                required_span_any=["ويؤكد ذلك"],
                acceptable_decisions=["hard_warning"],
                must_explain=["قرائن"],
            )
        ],
        forbidden_findings=[],
        metadata={"clean_case": False, "contains_critical_issue": True},
    )
    (gold_dir / "case-0001.gold.json").write_text(
        gold.model_dump_json(indent=2), encoding="utf-8"
    )

    outputs = tmp_path / "out.json"
    outputs.write_text(
        json.dumps(
            [
                {
                    "case_id": "case-0001",
                    "latency_ms": 100,
                    "findings": [
                        {
                            "category": "publisher_voice",
                            "decision": "hard_warning",
                            "severity": "high",
                            "original_text": "ويؤكد ذلك",
                            "suggested_text": None,
                            "explanation_ar": "تحويل قرائن إلى حقيقة.",
                            "segment_zone": "body",
                            "confidence": 0.9,
                        }
                    ],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = score_outputs(gold_dir=gold_dir, outputs=outputs)
    assert report.total_cases == 1
    assert report.tp == 1
    assert report.fn == 0
    assert report.recall == 1.0
    assert report.critical_recall == 1.0
    assert report.average_latency_ms == 100

    json_path = tmp_path / "report.json"
    write_json_report(report, json_path)
    assert json_path.exists()
    html = render_html_report(report)
    assert "benchmark_v2" in html
    assert "case-0001" in html


def test_repeated_runs_consistency(tmp_path: Path):
    gold_dir = tmp_path / "gold"
    gold_dir.mkdir()
    gold = {
        "case_id": "case-0001",
        "expected_findings": [
            {
                "category": "consistency",
                "severity_band": ["high"],
                "required_span_any": ["103%"],
                "acceptable_decisions": ["hard_warning"],
                "must_explain": [],
            }
        ],
        "forbidden_findings": [],
        "metadata": {"clean_case": False, "contains_critical_issue": True},
    }
    (gold_dir / "case-0001.gold.json").write_text(
        json.dumps(gold, ensure_ascii=False), encoding="utf-8"
    )

    finding = {
        "category": "consistency",
        "decision": "hard_warning",
        "severity": "high",
        "original_text": "103%",
        "suggested_text": None,
        "explanation_ar": "مجموع النسب",
        "segment_zone": "body",
        "confidence": 0.8,
    }
    paths = []
    for i in range(3):
        p = tmp_path / f"run{i}.json"
        p.write_text(
            json.dumps(
                [{"case_id": "case-0001", "latency_ms": 10 + i, "findings": [finding]}],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        paths.append(p)

    report = score_repeated_runs(gold_dir=gold_dir, output_paths=paths)
    assert report.run_count == 3
    assert report.consistency_score == 1.0
    assert report.f1 == 1.0


def test_consistency_detects_drift():
    a = {
        "case-1": EngineCaseOutput(
            case_id="case-1",
            findings=[
                EngineFinding(
                    category="x",
                    decision="hard_warning",
                    severity="high",
                    original_text="foo",
                )
            ],
        )
    }
    b = {
        "case-1": EngineCaseOutput(
            case_id="case-1",
            findings=[
                EngineFinding(
                    category="y",
                    decision="soft_warning",
                    severity="low",
                    original_text="bar",
                )
            ],
        )
    }
    score = consistency_across_runs([a, b])
    assert score == 0.0
