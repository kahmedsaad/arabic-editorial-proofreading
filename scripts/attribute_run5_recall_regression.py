#!/usr/bin/env python3
"""Attribute critical-recall regressions between benchmark baseline and run5."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _finding_from_dict(payload: dict[str, Any]):
    from app.models.schemas import Finding

    data = dict(payload)
    data.pop("segment_zone", None)
    return Finding.model_validate(data)


def _segments_for_case(case_id: str, case: dict[str, str]):
    from app.parsing.document import parse_document_text

    parsed = parse_document_text(
        document_id=case_id,
        headline=case.get("headline") or "",
        body=case.get("body") or "",
        source="benchmark_v2",
    )
    return parsed.document, parsed.segments


def _gate_reason_for_finding(
    finding_payload: dict[str, Any],
    case: dict[str, str],
    case_id: str,
    *,
    policy: str,
) -> str | None:
    from app.context.article_context import extract_article_context
    from app.postprocess.editorial_gate import suppression_reason

    finding = _finding_from_dict(finding_payload)
    document, segments = _segments_for_case(case_id, case)
    context = extract_article_context(document, segments)
    return suppression_reason(
        finding, policy=policy, context=context, segments=segments
    )


def attribute(
    *,
    baseline_report: Path,
    candidate_report: Path,
    baseline_outputs: Path,
    candidate_outputs: Path,
    gold_dir: Path,
    cases_dir: Path,
    policy: str = "run5",
) -> list[dict[str, Any]]:
    from benchmark_v2.private.scorer.matching import score_gold_against_engine
    from benchmark_v2.private.scorer.schemas import EngineFinding
    from benchmark_v2.private.scorer.score import load_gold_cases

    base = _load_json(baseline_report)
    cand = _load_json(candidate_report)
    out_base = {row["case_id"]: row for row in _load_json(baseline_outputs)["outputs"]}
    out_cand = {row["case_id"]: row for row in _load_json(candidate_outputs)["outputs"]}
    golds = {g.case_id: g for g in load_gold_cases(gold_dir)}
    cases = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(cases_dir.glob("*.json"))
    }

    rows: list[dict[str, Any]] = []
    for base_case, cand_case in zip(base["cases"], cand["cases"]):
        case_id = base_case["case_id"]
        gold = golds[case_id]
        case = cases[case_id]
        contains_critical = bool(gold.metadata.get("contains_critical_issue"))
        base_matched = {
            match["gold_index"] for match in base_case["matches"] if match.get("matched")
        }
        cand_matched = {
            match["gold_index"] for match in cand_case["matches"] if match.get("matched")
        }
        for gold_index, expected in enumerate(gold.expected_findings):
            is_critical = bool(expected.critical) or contains_critical
            if not is_critical:
                continue
            if gold_index not in base_matched or gold_index in cand_matched:
                continue

            base_match = next(m for m in base_case["matches"] if m["gold_index"] == gold_index)
            base_finding = out_base[case_id]["findings"][base_match["engine_index"]]
            best_score = -999.0
            best_finding = None
            best_detail = None
            for finding in out_cand[case_id]["findings"]:
                detail = score_gold_against_engine(
                    expected, EngineFinding.model_validate(finding)
                )
                if detail["score"] > best_score:
                    best_score = detail["score"]
                    best_finding = finding
                    best_detail = detail

            # Replay gate on the baseline finding that previously matched.
            gate_reason_on_baseline = _gate_reason_for_finding(
                base_finding, case, case_id, policy=policy
            )
            # Also check whether any candidate finding would be suppressed if present.
            similar_candidate = None
            similar_gate = None
            for finding in out_cand[case_id]["findings"]:
                if (finding.get("original_text") or "") == (base_finding.get("original_text") or ""):
                    similar_candidate = finding
                    similar_gate = _gate_reason_for_finding(
                        finding, case, case_id, policy=policy
                    )
                    break

            if gate_reason_on_baseline:
                root_cause = f"gate_would_suppress:{gate_reason_on_baseline}"
                disposition = "would_be_suppressed_by_gate_if_emitted"
            elif similar_candidate is None and best_score < 5.0:
                root_cause = "model_or_pipeline_did_not_emit_matching_finding"
                disposition = "missing_from_exposed_findings"
            elif best_detail and not best_detail.get("matched"):
                root_cause = "emitted_but_below_match_threshold_or_wrong_span"
                disposition = "present_but_unmatched"
            else:
                root_cause = "unrelated_evaluation_variance"
                disposition = "unknown"

            # Clarify: if gate would suppress baseline finding, and candidate lacks match,
            # still distinguish whether candidate ever emitted it.
            emitted_like_baseline = any(
                (f.get("original_text") or "") == (base_finding.get("original_text") or "")
                or (f.get("finding_id") == base_finding.get("finding_id"))
                for f in out_cand[case_id]["findings"]
            )
            if gate_reason_on_baseline and not emitted_like_baseline:
                # Cannot prove live suppression without rejected_findings; note limitation.
                root_cause = (
                    f"likely_gate_or_nonemit; baseline_finding_matches_suppress_rule:"
                    f"{gate_reason_on_baseline}"
                )
                disposition = "not_in_exposed_findings;_rejected_findings_not_persisted"

            rows.append(
                {
                    "benchmark_id": case_id,
                    "gold_index": gold_index,
                    "category": expected.category,
                    "expected_issue": {
                        "required_span_any": list(expected.required_span_any or []),
                        "category": expected.category,
                        "severity_band": list(expected.severity_band or []),
                        "critical": True,
                        "must_explain": list(expected.must_explain or []),
                    },
                    "baseline_raw_finding": {
                        "finding_id": base_finding.get("finding_id"),
                        "category": base_finding.get("category"),
                        "original_text": base_finding.get("original_text"),
                        "explanation_ar": base_finding.get("explanation_ar"),
                        "decision": base_finding.get("decision"),
                        "severity": base_finding.get("severity"),
                    },
                    "candidate_best_finding": None
                    if best_finding is None
                    else {
                        "finding_id": best_finding.get("finding_id"),
                        "category": best_finding.get("category"),
                        "original_text": best_finding.get("original_text"),
                        "explanation_ar": best_finding.get("explanation_ar"),
                        "score": best_score,
                        "matched": bool(best_detail and best_detail.get("matched")),
                    },
                    "gate_reason_on_baseline_finding": gate_reason_on_baseline,
                    "gate_reason_on_similar_candidate": similar_gate,
                    "candidate_rejected_finding_count": out_cand[case_id].get(
                        "rejected_finding_count"
                    ),
                    "final_disposition": disposition,
                    "root_cause": root_cause,
                    "evidence_note": (
                        "Engine outputs store rejected_finding_count only; "
                        "rejected finding payloads / gate reason codes were not persisted "
                        "in run5 benchmark artifacts. Gate attribution uses deterministic "
                        "replay of the baseline matched finding against current gate rules."
                    ),
                }
            )
    return rows


def render_markdown(rows: list[dict[str, Any]], *, baseline_label: str, candidate_label: str) -> str:
    by_cause: dict[str, int] = {}
    by_gate: dict[str, int] = {}
    for row in rows:
        by_cause[row["root_cause"]] = by_cause.get(row["root_cause"], 0) + 1
        reason = row.get("gate_reason_on_baseline_finding")
        if reason:
            by_gate[reason] = by_gate.get(reason, 0) + 1

    lines = [
        "# Run5 critical-recall regression attribution",
        "",
        f"Baseline: `{baseline_label}`  ",
        f"Candidate: `{candidate_label}`",
        "",
        "## Aggregate",
        "",
        f"- Lost critical items (matched in baseline, unmatched in candidate): **{len(rows)}**",
        f"- Gate-suppressible under current R1/R2/R4 replay: **{sum(1 for r in rows if r.get('gate_reason_on_baseline_finding'))}**",
        "",
        "### By root cause",
        "",
    ]
    for cause, count in sorted(by_cause.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{cause}`: {count}")
    lines.extend(["", "### By gate reason (replay on baseline finding)", ""])
    if by_gate:
        for reason, count in sorted(by_gate.items()):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "### Attribution caveat",
            "",
            "Run5 benchmark outputs did not persist `rejected_findings` or gate reason codes.",
            "Therefore live suppressions cannot be proven from artifacts alone.",
            "Attribution below combines missing exposed matches with deterministic replay of",
            "the baseline matched finding through the current editorial gate.",
            "",
            "## Lost critical items",
            "",
        ]
    )
    for row in rows:
        expected = row["expected_issue"]
        baseline = row["baseline_raw_finding"]
        lines.extend(
            [
                f"### {row['benchmark_id']} gold_index={row['gold_index']}",
                "",
                f"- category: `{row['category']}`",
                f"- expected spans: {expected['required_span_any']}",
                f"- baseline finding: `{baseline['finding_id']}` / `{baseline['category']}` / `{baseline['original_text']}`",
                f"- gate replay on baseline finding: `{row['gate_reason_on_baseline_finding']}`",
                f"- disposition: `{row['final_disposition']}`",
                f"- root cause: `{row['root_cause']}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline-report",
        type=Path,
        default=ROOT / "benchmark_v2" / "results" / "report_gemini_run2.json",
    )
    parser.add_argument(
        "--candidate-report",
        type=Path,
        default=ROOT
        / "benchmark_v2"
        / "results"
        / "report_gemini_run5_editorial_gates.json",
    )
    parser.add_argument(
        "--baseline-outputs",
        type=Path,
        default=ROOT / "benchmark_v2" / "results" / "engine_outputs_gemini_run2.json",
    )
    parser.add_argument(
        "--candidate-outputs",
        type=Path,
        default=ROOT
        / "benchmark_v2"
        / "results"
        / "engine_outputs_gemini_run5_editorial_gates.json",
    )
    parser.add_argument(
        "--gold-dir",
        type=Path,
        default=ROOT / "benchmark_v2" / "private" / "gold",
    )
    parser.add_argument(
        "--cases-dir",
        type=Path,
        default=ROOT / "benchmark_v2" / "public" / "cases",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=ROOT
        / "data"
        / "evaluation"
        / "analysis"
        / "editorial_labels_run3"
        / "run5_recall_regression_attribution.md",
    )
    parser.add_argument(
        "--out-jsonl",
        type=Path,
        default=ROOT
        / "data"
        / "evaluation"
        / "analysis"
        / "editorial_labels_run3"
        / "run5_recall_regression_attribution.jsonl",
    )
    parser.add_argument("--policy", default="run5")
    args = parser.parse_args(argv)

    rows = attribute(
        baseline_report=args.baseline_report,
        candidate_report=args.candidate_report,
        baseline_outputs=args.baseline_outputs,
        candidate_outputs=args.candidate_outputs,
        gold_dir=args.gold_dir,
        cases_dir=args.cases_dir,
        policy=args.policy,
    )
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(
        render_markdown(
            rows,
            baseline_label=str(args.baseline_report),
            candidate_label=str(args.candidate_report),
        ),
        encoding="utf-8",
    )
    args.out_jsonl.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "lost_critical": len(rows),
                "gate_suppressible": sum(
                    1 for row in rows if row.get("gate_reason_on_baseline_finding")
                ),
                "out_md": str(args.out_md),
                "out_jsonl": str(args.out_jsonl),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
