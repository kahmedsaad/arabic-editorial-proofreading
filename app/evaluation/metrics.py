from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EvalIssue:
    category: str
    original_text: str
    suggested_text: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None


@dataclass
class EvalRecord:
    record_id: str
    headline: str = ""
    body: str = ""
    expected_issues: list[EvalIssue] = field(default_factory=list)


@dataclass
class EvalMetrics:
    expected_issues: int = 0
    detected_issues: int = 0
    exact_match: int = 0
    partial_span_match: int = 0
    category_match: int = 0
    suggestion_match: int = 0
    false_positives: int = 0
    missed_findings: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    processing_time_ms: float = 0.0
    gemini_calls: int = 0
    token_usage: dict[str, Any] = field(default_factory=dict)
    details: list[dict[str, Any]] = field(default_factory=list)


def load_golden(path: Path | str) -> list[EvalRecord]:
    """Load golden JSONL from a local path or gs:// URI via shared dataset loaders."""
    path_str = str(path)
    records: list[EvalRecord] = []
    from app.data.loader import is_gcs_path, resolve_loader_for_path

    loader = resolve_loader_for_path(path_str)
    if is_gcs_path(path_str):
        rows = loader.read_jsonl(path_str)
    else:
        p = Path(path_str)
        if not p.exists():
            raise FileNotFoundError(p)
        rows = loader.read_jsonl(str(p))

    for raw in rows:
        issues = [EvalIssue(**item) for item in raw.get("expected_issues", [])]
        records.append(
            EvalRecord(
                record_id=raw.get("record_id") or raw.get("pair_id") or "REC",
                headline=raw.get("headline", ""),
                body=raw.get("body") or raw.get("original_text", "") or raw.get("mutated_text", ""),
                expected_issues=issues,
            )
        )
    return records


def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and b_start < a_end


def score_record(expected: list[EvalIssue], detected: list[dict[str, Any]]) -> dict[str, Any]:
    matched_det: set[int] = set()
    exact = partial = category = suggestion = 0
    for exp in expected:
        found = False
        for idx, det in enumerate(detected):
            if idx in matched_det:
                continue
            text_match = det.get("original_text") == exp.original_text
            span_match = False
            if (
                exp.start_offset is not None
                and exp.end_offset is not None
                and det.get("start_offset") is not None
                and det.get("end_offset") is not None
            ):
                span_match = _overlap(
                    exp.start_offset,
                    exp.end_offset,
                    int(det["start_offset"]),
                    int(det["end_offset"]),
                )
            soft = text_match or span_match or (
                exp.original_text and exp.original_text in (det.get("original_text") or "")
            )
            if not soft:
                continue
            matched_det.add(idx)
            found = True
            if text_match and (
                exp.start_offset is None
                or (
                    det.get("start_offset") == exp.start_offset
                    and det.get("end_offset") == exp.end_offset
                )
            ):
                exact += 1
            else:
                partial += 1
            if det.get("category") == exp.category:
                category += 1
            if exp.suggested_text is not None and det.get("suggested_text") == exp.suggested_text:
                suggestion += 1
            break
        if not found:
            pass
    missed = len(expected) - (exact + partial)
    # recount missed properly
    missed = len(expected) - len(
        [
            1
            for exp in expected
            if any(
                (det.get("original_text") == exp.original_text)
                or (exp.original_text and exp.original_text in (det.get("original_text") or ""))
                for det in detected
            )
        ]
    )
    fp = max(0, len(detected) - len(matched_det))
    return {
        "exact_match": exact,
        "partial_span_match": partial,
        "category_match": category,
        "suggestion_match": suggestion,
        "false_positives": fp,
        "missed_findings": missed,
        "matched": len(matched_det),
    }


async def run_evaluation(
    golden_path: Path | str,
    review_fn,
) -> EvalMetrics:
    records = load_golden(golden_path)
    metrics = EvalMetrics()
    started = time.perf_counter()
    for record in records:
        response = await review_fn(record)
        detected = [f.model_dump() if hasattr(f, "model_dump") else f for f in response.findings]
        stats = score_record(record.expected_issues, detected)
        metrics.expected_issues += len(record.expected_issues)
        metrics.detected_issues += len(detected)
        metrics.exact_match += stats["exact_match"]
        metrics.partial_span_match += stats["partial_span_match"]
        metrics.category_match += stats["category_match"]
        metrics.suggestion_match += stats["suggestion_match"]
        metrics.false_positives += stats["false_positives"]
        metrics.missed_findings += stats["missed_findings"]
        metrics.details.append({"record_id": record.record_id, **stats})
        if getattr(response, "ai_finding_count", 0):
            metrics.gemini_calls += 0  # mock path; real gemini tracked by client
    metrics.processing_time_ms = (time.perf_counter() - started) * 1000
    tp = metrics.exact_match + metrics.partial_span_match
    denom_p = tp + metrics.false_positives
    denom_r = tp + metrics.missed_findings
    metrics.precision = (tp / denom_p) if denom_p else 0.0
    metrics.recall = (tp / denom_r) if denom_r else 0.0
    if metrics.precision + metrics.recall:
        metrics.f1 = 2 * metrics.precision * metrics.recall / (metrics.precision + metrics.recall)
    return metrics


def metrics_to_dict(metrics: EvalMetrics) -> dict[str, Any]:
    return asdict(metrics)
