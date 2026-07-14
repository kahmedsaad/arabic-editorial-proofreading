#!/usr/bin/env python3
"""Compare two silence/eval run directories (read-only)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation.clean_metrics import bucket_category, compute_clean_fp_metrics  # noqa: E402


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _metrics_from_run(run_dir: Path) -> dict:
    report = _load_json(run_dir / "report.json")
    articles = _load_jsonl(run_dir / "articles.jsonl")
    if articles:
        cats = [list(a.get("categories") or []) for a in articles]
        split = compute_clean_fp_metrics(article_finding_categories=cats)
    else:
        split = {}
    # Prefer recomputed split; fall back to report fields
    out = {**report, **split}
    out["_run_dir"] = str(run_dir)
    out["_articles"] = articles
    out["_labels"] = _load_jsonl(run_dir / "fp_labels_todo.jsonl")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two evaluation run directories")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    if not args.baseline.exists():
        raise SystemExit(f"Missing baseline: {args.baseline}")
    if not args.candidate.exists():
        raise SystemExit(
            f"Missing candidate run directory: {args.candidate}\n"
            "Wait for the run to finish before comparing."
        )

    base = _metrics_from_run(args.baseline)
    cand = _metrics_from_run(args.candidate)

    def g(d: dict, key: str, default=None):
        return d.get(key, default)

    b_fp = g(base, "clean_fp_rate_all", g(base, "clean_article_fp_rate"))
    c_fp = g(cand, "clean_fp_rate_all", g(cand, "clean_article_fp_rate"))
    b_total = g(base, "total_findings", 0) or 0
    c_total = g(cand, "total_findings", 0) or 0
    b_punct = (g(base, "fp_by_category") or {}).get("punctuation", 0)
    c_punct = (g(cand, "fp_by_category") or {}).get("punctuation", 0)
    b_zero = g(base, "zero_finding_clean_article_rate")
    c_zero = g(cand, "zero_finding_clean_article_rate")

    abs_red = None if b_fp is None or c_fp is None else round(b_fp - c_fp, 4)
    rel_red = None
    if b_fp and c_fp is not None and b_fp > 0:
        rel_red = round((b_fp - c_fp) / b_fp, 4)

    # Category comparison
    b_cats = Counter(g(base, "fp_by_category") or {})
    c_cats = Counter(g(cand, "fp_by_category") or {})
    all_cats = sorted(set(b_cats) | set(c_cats))
    cat_rows = []
    for cat in all_cats:
        cat_rows.append(
            {
                "category": cat,
                "bucket": bucket_category(cat),
                "baseline": b_cats.get(cat, 0),
                "candidate": c_cats.get(cat, 0),
                "delta": c_cats.get(cat, 0) - b_cats.get(cat, 0),
            }
        )

    # Article comparison
    b_art = {a.get("record_id"): a for a in base.get("_articles") or []}
    c_art = {a.get("record_id"): a for a in cand.get("_articles") or []}
    art_ids = sorted(set(b_art) | set(c_art))
    art_rows = []
    unexpected_non_punct_deltas = 0
    for aid in art_ids:
        ba = b_art.get(aid) or {}
        ca = c_art.get(aid) or {}
        b_list = list(ba.get("categories") or [])
        c_list = list(ca.get("categories") or [])
        b_n = len(b_list)
        c_n = len(c_list)
        b_e = sum(1 for x in b_list if x != "punctuation")
        c_e = sum(1 for x in c_list if x != "punctuation")
        if b_e != c_e:
            unexpected_non_punct_deltas += 1
        art_rows.append(
            {
                "article_id": aid,
                "baseline_findings": b_n,
                "candidate_findings": c_n,
                "baseline_editorial": b_e,
                "candidate_editorial": c_e,
                "delta_all": c_n - b_n,
                "delta_editorial": c_e - b_e,
            }
        )

    summary = {
        "baseline": str(args.baseline),
        "candidate": str(args.candidate),
        "baseline_clean_fp_rate": b_fp,
        "candidate_clean_fp_rate": c_fp,
        "absolute_reduction_clean_fp": abs_red,
        "relative_reduction_clean_fp": rel_red,
        "baseline_total_findings": b_total,
        "candidate_total_findings": c_total,
        "total_findings_reduction": b_total - c_total,
        "baseline_punctuation_findings": b_punct,
        "candidate_punctuation_findings": c_punct,
        "punctuation_findings_removed": b_punct - c_punct,
        "baseline_zero_finding_rate": b_zero,
        "candidate_zero_finding_rate": c_zero,
        "zero_finding_improvement": None
        if b_zero is None or c_zero is None
        else round(c_zero - b_zero, 4),
        "baseline_editorial_fp_rate": g(base, "clean_fp_rate_editorial_only"),
        "candidate_editorial_fp_rate": g(cand, "clean_fp_rate_editorial_only"),
        "articles_with_editorial_count_changed": unexpected_non_punct_deltas,
        "caution": (
            "Clean-set FP reduction from disabling punctuation does not equal "
            "editorial precision improvement. Human keep/drop labels are required "
            "before claiming editorial precision gains."
        ),
        "baseline_split": {
            k: g(base, k)
            for k in (
                "clean_fp_rate_all",
                "clean_fp_rate_editorial_only",
                "clean_fp_rate_punctuation_only",
                "findings_per_article_all",
                "findings_per_article_editorial_only",
                "zero_finding_clean_article_rate",
                "zero_editorial_finding_clean_article_rate",
                "category_report",
            )
        },
        "candidate_split": {
            k: g(cand, k)
            for k in (
                "clean_fp_rate_all",
                "clean_fp_rate_editorial_only",
                "clean_fp_rate_punctuation_only",
                "findings_per_article_all",
                "findings_per_article_editorial_only",
                "zero_finding_clean_article_rate",
                "zero_editorial_finding_clean_article_rate",
                "category_report",
            )
        },
    }

    out: Path = args.output
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (out / "category_comparison.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["category", "bucket", "baseline", "candidate", "delta"]
        )
        w.writeheader()
        w.writerows(cat_rows)
    with (out / "article_comparison.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "article_id",
                "baseline_findings",
                "candidate_findings",
                "baseline_editorial",
                "candidate_editorial",
                "delta_all",
                "delta_editorial",
            ],
        )
        w.writeheader()
        w.writerows(art_rows)

    readme = f"""# Run comparison

- Baseline: `{args.baseline}`
- Candidate: `{args.candidate}`

## Headline

| Metric | Baseline | Candidate | Delta |
|--------|----------|-----------|-------|
| Clean FP rate | {b_fp} | {c_fp} | {abs_red} |
| Total findings | {b_total} | {c_total} | {b_total - c_total} |
| Punctuation findings | {b_punct} | {c_punct} | {b_punct - c_punct} |
| Zero-finding rate | {b_zero} | {c_zero} | {summary['zero_finding_improvement']} |

## Caution

{summary['caution']}

Articles with editorial finding-count changes (unexpected if only punctuation policy changed): **{unexpected_non_punct_deltas}**
"""
    (out / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nWrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
