#!/usr/bin/env python3
"""Deterministic editorial-gate replay against stored findings (no Gemini calls)."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _finding_from_row(row: dict[str, Any]):
    from app.models.schemas import Decision, Finding, FindingSource, Severity

    source_raw = (row.get("source") or "gemini").lower()
    source = {
        "mechanical": FindingSource.MECHANICAL,
        "mock": FindingSource.MOCK,
        "gemini": FindingSource.GEMINI,
    }.get(source_raw, FindingSource.GEMINI)
    decision_raw = row.get("decision") or "needs_editor_review"
    try:
        decision = Decision(decision_raw)
    except Exception:
        decision = Decision.NEEDS_EDITOR_REVIEW
    severity_raw = row.get("severity") or "medium"
    try:
        severity = Severity(severity_raw)
    except Exception:
        severity = Severity.MEDIUM
    original = row.get("original_text") or ""
    return Finding(
        finding_id=str(row.get("finding_id") or "FND-REPLAY"),
        document_id=str(row.get("article_id") or row.get("document_id") or "DOC"),
        segment_id=str(row.get("segment_id") or "SEG-001"),
        source=source,
        category=str(row.get("category") or "clarity"),
        decision=decision,
        severity=severity,
        original_text=original,
        suggested_text=row.get("suggested_text"),
        start_offset=int(row.get("start_offset") or 0),
        end_offset=int(row.get("end_offset") or max(0, len(original))),
        explanation_ar=str(row.get("explanation_ar") or ""),
        confidence=float(row.get("confidence") or 1.0),
        validation_errors=list(row.get("validation_errors") or []),
    )


def _segments_for_row(row: dict[str, Any]):
    from app.parsing.document import parse_document_text

    headline = row.get("headline") or ""
    body = row.get("body") or row.get("body_excerpt") or ""
    parsed = parse_document_text(
        document_id=str(row.get("article_id") or "DOC"),
        headline=headline,
        body=body,
        source="gate_replay",
    )
    return parsed.document, parsed.segments


def build_pregates_snapshot(
    *,
    run5_labels: Path,
    run5_report: Path,
    out_path: Path,
) -> list[dict[str, Any]]:
    """Combine exposed run5 findings with recorded suppressions as a replay corpus."""
    exposed = _read_jsonl(run5_labels)
    report = json.loads(run5_report.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for row in exposed:
        item = dict(row)
        item["snapshot_status"] = "exposed_in_run5"
        item["run5_gate_action"] = "kept"
        rows.append(item)
    for example in report.get("editorial_suppression_examples") or []:
        item = {
            "label_id": f"suppressed:{example.get('record_id')}:{example.get('finding_id')}",
            "article_id": example.get("record_id"),
            "finding_id": example.get("finding_id"),
            "category": example.get("category"),
            "original_text": example.get("original_text"),
            "explanation_ar": example.get("explanation_ar"),
            "source": "gemini",
            "decision": "needs_editor_review",
            "severity": "medium",
            "confidence": 1.0,
            "headline": "",
            "body_excerpt": "",
            "snapshot_status": "suppressed_in_run5",
            "run5_gate_action": "suppressed",
            "run5_reason_code": example.get("reason_code"),
        }
        rows.append(item)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    return rows


def replay(
    rows: list[dict[str, Any]],
    *,
    policy: str,
) -> dict[str, Any]:
    from app.context.article_context import extract_article_context
    from app.evaluation.clean_metrics import compute_clean_fp_metrics
    from app.postprocess.editorial_gate import gate_editorial_findings

    kept_rows: list[dict[str, Any]] = []
    suppressed_rows: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    per_article: dict[str, list[str]] = {}

    for row in rows:
        finding = _finding_from_row(row)
        document, segments = _segments_for_row(row)
        context = extract_article_context(document, segments)
        kept, suppressed, audit = gate_editorial_findings(
            [finding],
            policy=policy,
            context=context,
            segments=segments,
        )
        article_id = str(row.get("article_id") or finding.document_id)
        per_article.setdefault(article_id, [])
        if kept:
            kept_rows.append(row)
            per_article[article_id].append(finding.category)
        else:
            reason = audit[0]["reason_code"] if audit else "unknown"
            reason_counts[reason] += 1
            suppressed_rows.append({**row, "replay_reason_code": reason})

    article_categories = list(per_article.values())
    metrics = compute_clean_fp_metrics(article_finding_categories=article_categories)
    family_counts: Counter[str] = Counter()
    for cats in article_categories:
        for cat in cats:
            family_counts[cat] += 1

    return {
        "policy": policy,
        "input_findings": len(rows),
        "kept": len(kept_rows),
        "suppressed": len(suppressed_rows),
        "reason_counts": dict(reason_counts.most_common()),
        "family_counts_kept": dict(family_counts.most_common()),
        "silence_metrics": metrics,
        "suppressed_examples": suppressed_rows[:20],
        "kept_examples": kept_rows[:10],
    }


def replay_critical_baseline(
    attribution_jsonl: Path,
    *,
    policy: str,
) -> dict[str, Any]:
    """Replay gates on baseline findings that matched lost critical gold items."""
    from app.context.article_context import extract_article_context
    from app.parsing.document import parse_document_text
    from app.postprocess.editorial_gate import suppression_reason
    from app.models.schemas import Decision, Finding, FindingSource, Severity

    rows = _read_jsonl(attribution_jsonl)
    cases_dir = ROOT / "benchmark_v2" / "public" / "cases"
    preserved = 0
    lost = 0
    details: list[dict[str, Any]] = []
    for row in rows:
        case_id = row["benchmark_id"]
        case = json.loads((cases_dir / f"{case_id}.json").read_text(encoding="utf-8"))
        baseline = row["baseline_raw_finding"]
        finding = Finding(
            finding_id=str(baseline.get("finding_id") or "FND"),
            document_id=case_id,
            segment_id="SEG-001",
            source=FindingSource.GEMINI,
            category=str(baseline.get("category") or "attribution"),
            decision=Decision(baseline.get("decision") or "needs_editor_review")
            if baseline.get("decision") in Decision._value2member_map_
            else Decision.NEEDS_EDITOR_REVIEW,
            severity=Severity(baseline.get("severity") or "medium")
            if baseline.get("severity") in Severity._value2member_map_
            else Severity.MEDIUM,
            original_text=str(baseline.get("original_text") or ""),
            suggested_text=None,
            start_offset=0,
            end_offset=len(str(baseline.get("original_text") or "")),
            explanation_ar=str(baseline.get("explanation_ar") or ""),
            confidence=1.0,
        )
        parsed = parse_document_text(
            document_id=case_id,
            headline=case.get("headline") or "",
            body=case.get("body") or "",
            source="benchmark_v2",
        )
        context = extract_article_context(parsed.document, parsed.segments)
        reason = suppression_reason(
            finding,
            policy=policy,
            context=context,
            segments=parsed.segments,
        )
        if reason is None:
            preserved += 1
            status = "preserved"
        else:
            lost += 1
            status = f"suppressed:{reason}"
        details.append(
            {
                "benchmark_id": case_id,
                "gold_index": row.get("gold_index"),
                "category": row.get("category"),
                "status": status,
                "gate_reason": reason,
            }
        )
    return {
        "policy": policy,
        "critical_items": len(rows),
        "preserved": preserved,
        "lost": lost,
        "details": details,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run5-labels",
        type=Path,
        default=ROOT
        / "data"
        / "evaluation"
        / "runs"
        / "gemini_run5_editorial_gates"
        / "fp_labels_todo.jsonl",
    )
    parser.add_argument(
        "--run5-report",
        type=Path,
        default=ROOT
        / "data"
        / "evaluation"
        / "runs"
        / "gemini_run5_editorial_gates"
        / "report.json",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=ROOT
        / "data"
        / "evaluation"
        / "analysis"
        / "editorial_labels_run3"
        / "run5_pregates_snapshot.jsonl",
    )
    parser.add_argument(
        "--attribution-jsonl",
        type=Path,
        default=ROOT
        / "data"
        / "evaluation"
        / "analysis"
        / "editorial_labels_run3"
        / "run5_recall_regression_attribution.jsonl",
    )
    parser.add_argument("--policy", default="run5")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT
        / "data"
        / "evaluation"
        / "analysis"
        / "editorial_labels_run3"
        / "run5b_gate_replay_report.json",
    )
    args = parser.parse_args(argv)

    rows = build_pregates_snapshot(
        run5_labels=args.run5_labels,
        run5_report=args.run5_report,
        out_path=args.snapshot,
    )
    silence = replay(rows, policy=args.policy)
    critical = replay_critical_baseline(args.attribution_jsonl, policy=args.policy)
    # Compare vs run5 observed suppressions on snapshot
    run5_suppressed = sum(1 for row in rows if row.get("run5_gate_action") == "suppressed")
    payload = {
        "snapshot_path": str(args.snapshot),
        "snapshot_rows": len(rows),
        "run5_recorded_suppressions_in_snapshot": run5_suppressed,
        "silence_replay": silence,
        "critical_replay": critical,
        "acceptance": {
            "critical_gate_suppressed_restored": critical["lost"] == 0,
            "no_new_critical_loss": critical["lost"] == 0,
            "r2_fired": silence["reason_counts"].get("clarity_generic_no_concrete_defect", 0) > 0,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
