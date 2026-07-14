#!/usr/bin/env python3
"""Read-only validation for editorial keep/drop label JSONL files."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_DECISIONS = frozenset({"keep", "drop", "uncertain"})
ALLOWED_DROP_REASONS = frozenset(
    {
        "context_resolves_issue",
        "headline_compression",
        "valid_quotation",
        "optional_style",
        "too_low_impact",
        "incorrect_rule",
        "duplicate",
        "wrong_span",
        "acceptable_arabic",
        "out_of_scope_fact_check",
        "incorrect_category",
        "other",
    }
)


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def validate_rows(rows: list[dict]) -> dict:
    category_counts: Counter[str] = Counter()
    composite_ids: list[str] = []
    finding_ids_only: list[str] = []
    blank_decision = 0
    blank_drop_reason = 0
    missing_article = 0
    missing_segment = 0
    invalid_json_already_parsed = 0  # kept for schema symmetry
    errors: list[dict] = []
    labeled = 0

    for i, row in enumerate(rows, start=1):
        cat = row.get("category") or "unknown"
        category_counts[cat] += 1
        fid = row.get("finding_id")
        aid = row.get("article_id")
        if fid:
            finding_ids_only.append(str(fid))
            composite_ids.append(f"{aid}::{fid}")
        if _is_blank(aid):
            missing_article += 1
            errors.append({"line": i, "error": "missing_article_id"})
        if _is_blank(row.get("segment_id")):
            missing_segment += 1
            # Older run3 exports omitted segment_id — warn only
            errors.append({"line": i, "error": "missing_segment_id", "severity": "warn"})

        decision = row.get("decision")
        drop_reason = row.get("drop_reason")

        if _is_blank(decision):
            blank_decision += 1
            continue

        decision_s = str(decision).strip().lower()
        labeled += 1
        if decision_s not in ALLOWED_DECISIONS:
            errors.append(
                {
                    "line": i,
                    "error": "invalid_decision",
                    "value": decision,
                    "finding_id": fid,
                }
            )
            continue

        if _is_blank(drop_reason):
            blank_drop_reason += 1
            if decision_s == "drop":
                errors.append(
                    {
                        "line": i,
                        "error": "drop_requires_drop_reason",
                        "finding_id": fid,
                    }
                )
        else:
            reason_s = str(drop_reason).strip().lower()
            if reason_s not in ALLOWED_DROP_REASONS:
                errors.append(
                    {
                        "line": i,
                        "error": "invalid_drop_reason",
                        "value": drop_reason,
                        "finding_id": fid,
                    }
                )

    id_counts = Counter(composite_ids)
    duplicate_finding_ids = sorted([k for k, v in id_counts.items() if v > 1])
    # Also note finding_id reuse across articles (expected; not an error)
    reuse_across_articles = sum(1 for v in Counter(finding_ids_only).values() if v > 1)

    hard_errors = [e for e in errors if e.get("severity") != "warn"]
    return {
        "total_rows": len(rows),
        "category_counts": dict(category_counts.most_common()),
        "blank_decision": blank_decision,
        "blank_drop_reason_among_all_rows": blank_drop_reason,
        "labeled_rows": labeled,
        "unlabeled_rows": blank_decision,
        "duplicate_finding_ids": duplicate_finding_ids,
        "duplicate_finding_id_count": len(duplicate_finding_ids),
        "finding_id_reuse_across_articles": reuse_across_articles,
        "duplicate_key": "article_id::finding_id",
        "missing_article_ids": missing_article,
        "missing_segment_ids": missing_segment,
        "invalid_jsonl_rows": invalid_json_already_parsed,
        "validation_errors": hard_errors,
        "validation_warnings": [e for e in errors if e.get("severity") == "warn"],
        "ok": len(hard_errors) == 0 and len(duplicate_finding_ids) == 0,
        "allowed_decisions": sorted(ALLOWED_DECISIONS),
        "allowed_drop_reasons": sorted(ALLOWED_DROP_REASONS),
        "rules": {
            "keep": "drop_reason may be blank",
            "drop": "drop_reason required and must be allowed",
            "uncertain": "drop_reason may be blank",
            "empty_decision": "treated as unlabeled, not dropped",
            "precision": "exclude uncertain from precision denominator (keep/(keep+drop))",
            "uniqueness": "duplicates are article_id::finding_id (finding_id alone may repeat)",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate editorial label JSONL (read-only)")
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data" / "local" / "sprint2" / "non_punctuation_to_label.jsonl",
    )
    args = parser.parse_args(argv)

    path: Path = args.input
    if not path.exists():
        print(json.dumps({"error": f"missing file: {path}"}, indent=2))
        return 2

    rows: list[dict] = []
    bad_lines: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                rows.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                bad_lines.append({"line": i, "error": str(exc)})

    report = validate_rows(rows)
    report["input"] = str(path)
    report["invalid_jsonl_rows"] = len(bad_lines)
    report["invalid_jsonl_details"] = bad_lines[:20]
    if bad_lines:
        report["ok"] = False
        report["validation_errors"] = [
            *report["validation_errors"],
            *[{"line": b["line"], "error": "invalid_json", "detail": b["error"]} for b in bad_lines],
        ]

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
