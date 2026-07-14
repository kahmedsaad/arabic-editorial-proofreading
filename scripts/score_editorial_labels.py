#!/usr/bin/env python3
"""Score labeled non-punctuation findings (keep / drop / uncertain).

Precision formula (documented):
  precision = keep / (keep + drop)
  Rows with decision=uncertain or blank are EXCLUDED from the precision denominator.
  drop_rate = drop / (keep + drop + uncertain) among labeled rows in that category,
              or optionally drop/(keep+drop) — we report both:
    drop_rate_excluding_uncertain = drop / (keep + drop)
    drop_rate_among_labeled = drop / labeled

Allowed decisions: keep | drop | uncertain
Allowed drop reasons: see validate_editorial_label_file.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
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
SEVERITY_HIGH = frozenset({"high", "critical"})


def _load(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _blank(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def _validate_labeled(rows: list[dict]) -> list[dict]:
    errors = []
    for i, row in enumerate(rows, start=1):
        if _blank(row.get("decision")):
            continue
        decision = str(row.get("decision")).strip().lower()
        if decision not in ALLOWED_DECISIONS:
            errors.append({"line": i, "error": "invalid_decision", "value": row.get("decision")})
            continue
        if decision == "drop":
            reason = row.get("drop_reason")
            if _blank(reason) or str(reason).strip().lower() not in ALLOWED_DROP_REASONS:
                errors.append(
                    {
                        "line": i,
                        "error": "drop_requires_valid_drop_reason",
                        "value": reason,
                        "finding_id": row.get("finding_id"),
                    }
                )
        elif not _blank(row.get("drop_reason")):
            reason = str(row.get("drop_reason")).strip().lower()
            if reason not in ALLOWED_DROP_REASONS:
                errors.append(
                    {
                        "line": i,
                        "error": "invalid_drop_reason",
                        "value": row.get("drop_reason"),
                        "finding_id": row.get("finding_id"),
                    }
                )
    return errors


def _bucket(category: str) -> str:
    c = (category or "").lower()
    if c in {"attribution", "attribution_strength", "source_quality", "source_misrepresentation"}:
        return "Attribution"
    if c in {"headline_body_mismatch", "headline_framing", "publisher_voice"}:
        return "Headline mismatch"
    if c == "clarity":
        return "Clarity"
    if c == "quote_voice":
        return "Quote voice"
    if c == "loaded_framing":
        return "Loaded framing"
    if c in {"entity_name", "entity_confusion"}:
        return "Entity consistency"
    if c == "numeric_contradiction":
        return "Numeric consistency"
    if c == "temporal_contradiction":
        return "Temporal consistency"
    return category or "Other"


def _blank(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score editorial keep/drop labels")
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data" / "local" / "sprint2" / "non_punctuation_to_label.jsonl",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3",
    )
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(json.dumps({"error": f"missing {args.input}"}, indent=2))
        return 2

    rows = _load(args.input)
    labeled = [
        r
        for r in rows
        if not _blank(r.get("decision"))
        and str(r.get("decision")).strip().lower() in ALLOWED_DECISIONS
    ]
    if not labeled:
        print(
            json.dumps(
                {
                    "error": "No labeled rows yet",
                    "total_rows": len(rows),
                    "hint": "Set decision=keep|drop|uncertain then re-run.",
                    "precision_formula": "keep / (keep + drop); uncertain excluded",
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1

    hard_fail = _validate_labeled(rows)
    if hard_fail:
        print(
            json.dumps(
                {"error": "label validation failed", "validation_errors": hard_fail[:50]},
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1

    by_cat: dict[str, Counter] = defaultdict(Counter)
    drop_reasons: Counter = Counter()
    drop_reasons_by_cat: dict[str, Counter] = defaultdict(Counter)
    keep_c = drop_c = uncertain_c = 0
    high_fp = high_n = 0
    articles = set()

    for row in labeled:
        cat = _bucket(row.get("category") or "")
        decision = str(row.get("decision")).strip().lower()
        by_cat[cat][decision] += 1
        by_cat[cat]["n"] += 1
        articles.add(row.get("article_id"))
        if decision == "keep":
            keep_c += 1
        elif decision == "drop":
            drop_c += 1
            reason = str(row.get("drop_reason") or "other").strip().lower()
            drop_reasons[reason] += 1
            drop_reasons_by_cat[cat][reason] += 1
        else:
            uncertain_c += 1
        if (row.get("severity") or "").lower() in SEVERITY_HIGH:
            high_n += 1
            if decision == "drop":
                high_fp += 1

    decided = keep_c + drop_c
    precision_overall = (keep_c / decided) if decided else None

    table_rows = []
    for cat in sorted(by_cat.keys(), key=lambda c: -by_cat[c]["n"]):
        n = by_cat[cat]["n"]
        keep = by_cat[cat]["keep"]
        drop = by_cat[cat]["drop"]
        uncertain = by_cat[cat]["uncertain"]
        dec = keep + drop
        precision = (keep / dec) if dec else None
        main_reason = (
            drop_reasons_by_cat[cat].most_common(1)[0][0] if drop_reasons_by_cat[cat] else ""
        )
        table_rows.append(
            {
                "category": cat,
                "findings": n,
                "keep": keep,
                "drop": drop,
                "uncertain": uncertain,
                "precision": None if precision is None else round(precision, 4),
                "drop_rate_excluding_uncertain": round(drop / dec, 4) if dec else None,
                "drop_rate_among_labeled": round(drop / n, 4) if n else 0.0,
                "main_drop_reason": main_reason,
            }
        )

    summary = {
        "input": str(args.input),
        "precision_formula": "precision = keep / (keep + drop); uncertain excluded from denominator",
        "total_rows": len(rows),
        "total_labeled": len(labeled),
        "unlabeled_rows": sum(1 for r in rows if _blank(r.get("decision"))),
        "keep_count": keep_c,
        "drop_count": drop_c,
        "uncertain_count": uncertain_c,
        "precision_overall": None if precision_overall is None else round(precision_overall, 4),
        "precision_by_category": {
            r["category"]: r["precision"] for r in table_rows if r["precision"] is not None
        },
        "drop_rate_by_category": {
            r["category"]: r["drop_rate_excluding_uncertain"] for r in table_rows
        },
        "drop_reason_distribution": dict(drop_reasons.most_common()),
        "average_findings_per_article": round(len(labeled) / max(len(articles), 1), 4),
        "articles_with_editorial_fp": len(articles),
        "high_severity_false_positive_rate": (
            round(high_fp / high_n, 4) if high_n else None
        ),
        "allowed_decisions": sorted(ALLOWED_DECISIONS),
        "allowed_drop_reasons": sorted(ALLOWED_DROP_REASONS),
        "table": table_rows,
        "validation_ok": True,
    }

    out: Path = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with (out / "category_precision.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "category",
                "findings",
                "keep",
                "drop",
                "uncertain",
                "precision",
                "drop_rate_excluding_uncertain",
                "drop_rate_among_labeled",
                "main_drop_reason",
            ],
        )
        w.writeheader()
        w.writerows(table_rows)

    with (out / "drop_reasons.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["drop_reason", "count"])
        for reason, n in drop_reasons.most_common():
            w.writerow([reason, n])

    with (out / "labeled_findings.csv").open("w", encoding="utf-8", newline="") as fh:
        fields = [
            "article_id",
            "finding_id",
            "category",
            "severity",
            "confidence",
            "decision",
            "drop_reason",
            "editor_notes",
            "original_text",
            "explanation_ar",
        ]
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in labeled:
            w.writerow(
                {
                    **row,
                    "editor_notes": row.get("editor_notes") or row.get("notes"),
                }
            )

    # Backward-compatible alias
    with (out / "precision_by_category.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "category",
                "findings",
                "keep",
                "drop",
                "uncertain",
                "precision",
                "drop_rate",
                "main_drop_reason",
            ],
        )
        w.writeheader()
        for r in table_rows:
            w.writerow(
                {
                    "category": r["category"],
                    "findings": r["findings"],
                    "keep": r["keep"],
                    "drop": r["drop"],
                    "uncertain": r["uncertain"],
                    "precision": r["precision"],
                    "drop_rate": r["drop_rate_excluding_uncertain"],
                    "main_drop_reason": r["main_drop_reason"],
                }
            )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nWrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
