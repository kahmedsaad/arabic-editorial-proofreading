"""Pydantic schemas for hidden benchmark_v2."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class BenchmarkCase(BaseModel):
    """Public engine input only — never includes gold labels."""

    case_id: str
    headline: str = ""
    body: str = ""
    language: str = "ar"
    metadata: dict[str, Any] = Field(default_factory=dict)


class GoldFinding(BaseModel):
    """Expected finding criteria used only by the private scorer."""

    category: str
    severity_band: list[str] = Field(default_factory=list)
    segment_zone: str = "body"
    required_span_any: list[str] = Field(default_factory=list)
    acceptable_decisions: list[str] = Field(default_factory=list)
    suggestion_required: bool = False
    must_explain: list[str] = Field(default_factory=list)
    critical: bool = False


class ForbiddenFinding(BaseModel):
    """Spans / behaviors that must not appear in engine output."""

    span: str
    reason: str = ""
    category: Optional[str] = None
    decisions: list[str] = Field(default_factory=list)


class GoldCase(BaseModel):
    case_id: str
    expected_findings: list[GoldFinding] = Field(default_factory=list)
    forbidden_findings: list[ForbiddenFinding] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EngineFinding(BaseModel):
    """Normalized engine finding for scoring (gold-free)."""

    category: str
    decision: str
    severity: str
    original_text: str
    suggested_text: Optional[str] = None
    explanation_ar: str = ""
    segment_zone: str = "body"
    confidence: float = 0.0


class EngineCaseOutput(BaseModel):
    case_id: str
    findings: list[EngineFinding] = Field(default_factory=list)
    latency_ms: Optional[float] = None
    token_usage: Optional[int] = None
    run_id: Optional[str] = None


class MatchDetail(BaseModel):
    gold_index: int
    matched: bool
    engine_index: Optional[int] = None
    score: float = 0.0
    exact_span: bool = False
    partial_span: bool = False
    category_match: bool = False
    severity_band_match: bool = False
    decision_match: bool = False
    explanation_keyword_match: bool = False
    suggestion_safe: bool = True
    notes: list[str] = Field(default_factory=list)


class CaseScore(BaseModel):
    case_id: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    forbidden_hits: int = 0
    unsafe_suggestions: int = 0
    attribution_preserved: bool = True
    suggestion_safety: float = 1.0
    precision: float = 1.0
    recall: float = 1.0
    f1: float = 1.0
    critical_hits: int = 0
    critical_total: int = 0
    latency_ms: Optional[float] = None
    clean_case: bool = False
    matches: list[MatchDetail] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class BenchmarkReport(BaseModel):
    benchmark_id: str = "benchmark_v2"
    total_cases: int = 0
    tp: int = 0
    fp: int = 0
    fn: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    critical_recall: float = 0.0
    false_positive_rate: float = 0.0
    clean_case_false_positive_rate: float = 0.0
    attribution_preservation: float = 1.0
    suggestion_safety: float = 1.0
    average_latency_ms: Optional[float] = None
    consistency_score: Optional[float] = None
    run_count: int = 1
    cases: list[CaseScore] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
