#!/usr/bin/env python3
"""Analyze immutable gemini_run3 outputs for precision planning (run4 prep).

Reads run3 label/report files without modifying them. Writes derived artifacts to:
  data/evaluation/analysis/gemini_run3_precision/
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation.clean_metrics import compute_clean_fp_metrics  # noqa: E402
from app.postprocess.punctuation_gate import classify_punctuation_subtype  # noqa: E402
from app.models.schemas import Finding, FindingSource, Decision, Severity  # noqa: E402

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
EDITORIAL_PRIORITY = {
    "attribution": 100,
    "attribution_strength": 99,
    "headline_body_mismatch": 90,
    "headline_framing": 89,
    "publisher_voice": 88,
    "clarity": 80,
    "quote_voice": 70,
    "loaded_framing": 60,
}

ALLOWED_DECISIONS = ("keep", "drop", "uncertain")
ALLOWED_DROP_REASONS = (
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
)


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _infer_subtype(row: dict) -> str:
    if row.get("punctuation_subtype"):
        return str(row["punctuation_subtype"])
    # Reconstruct a minimal Finding for classifier heuristics.
    finding = Finding(
        finding_id=row.get("finding_id") or "X",
        document_id=row.get("article_id") or "DOC",
        segment_id=row.get("segment_id") or "SEG",
        source=FindingSource.MECHANICAL
        if str(row.get("finding_id", "")).startswith("FND-M")
        else FindingSource.GEMINI,
        category=row.get("category") or "punctuation",
        decision=Decision(row["decision"])
        if row.get("decision") in Decision._value2member_map_
        else Decision.SUGGEST,
        severity=Severity(row["severity"])
        if row.get("severity") in Severity._value2member_map_
        else Severity.LOW,
        original_text=row.get("original_text") or "",
        suggested_text=row.get("suggested_text"),
        start_offset=int(row.get("start_offset") or 0),
        end_offset=int(row.get("end_offset") or 0),
        explanation_ar=row.get("explanation_ar") or "",
        confidence=float(row.get("confidence") or 1.0),
        rule_ids=[],
    )
    # rule_id hints from explanation
    expl = finding.explanation_ar
    if "تكرار غير ضروري" in expl:
        finding.rule_ids = ["MECH-PUNCT-DUP"]
    elif "مسافة غير صحيحة قبل" in expl:
        finding.rule_ids = ["MECH-PUNCT-SPACE"]
    elif "تنقص مسافة بعد" in expl:
        finding.rule_ids = ["MECH-PUNCT-AFTER"]
    elif "مسافات بيضاء" in expl:
        finding.rule_ids = ["MECH-WS"]
    elif "اقتباس" in expl:
        finding.rule_ids = ["MECH-QUOTE"]
    return classify_punctuation_subtype(finding)


def _sort_key(row: dict) -> tuple:
    cat = (row.get("category") or "").lower()
    sev = SEVERITY_RANK.get((row.get("severity") or "low").lower(), 0)
    pri = EDITORIAL_PRIORITY.get(cat, 10)
    return (-sev, -pri, row.get("article_id") or "", row.get("finding_id") or "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze gemini_run3 FPs (read-only)")
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "data" / "evaluation" / "runs" / "gemini_run3",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data" / "evaluation" / "analysis" / "gemini_run3_precision",
    )
    parser.add_argument("--punct-sample", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260714)
    args = parser.parse_args(argv)

    run_dir: Path = args.run_dir
    labels_path = run_dir / "fp_labels_todo.jsonl"
    articles_path = run_dir / "articles.jsonl"
    report_path = run_dir / "report.json"
    if not labels_path.exists():
        raise SystemExit(f"Missing {labels_path}")

    labels = _load_jsonl(labels_path)
    articles = _load_jsonl(articles_path) if articles_path.exists() else []
    frozen_report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}

    enriched: list[dict] = []
    for row in labels:
        item = dict(row)
        item["punctuation_subtype"] = (
            _infer_subtype(row) if (row.get("category") or "").lower() == "punctuation" else None
        )
        item["source"] = item.get("source") or (
            "mechanical" if str(item.get("finding_id", "")).startswith("FND-M") else "gemini"
        )
        enriched.append(item)

    punct = [r for r in enriched if (r.get("category") or "").lower() == "punctuation"]
    non_punct = [r for r in enriched if (r.get("category") or "").lower() != "punctuation"]
    non_punct_sorted = sorted(non_punct, key=_sort_key)

    # Labeling sheet for editors (non-punctuation first priority)
    todo_rows = []
    for row in non_punct_sorted:
        todo_rows.append(
            {
                **row,
                "decision": None,
                "drop_reason": None,
                "editor_notes": None,
                "allowed_decisions": list(ALLOWED_DECISIONS),
                "allowed_drop_reasons": list(ALLOWED_DROP_REASONS),
            }
        )

    rng = random.Random(args.seed)
    sample = list(punct)
    rng.shuffle(sample)
    sample = sample[: min(args.punct_sample, len(sample))]

    # Metrics from articles.jsonl if present
    if articles:
        cats = [list(a.get("categories") or []) for a in articles]
        split = compute_clean_fp_metrics(article_finding_categories=cats)
    else:
        # Fallback: group labels by article
        by_art: dict[str, list[str]] = {}
        for row in enriched:
            by_art.setdefault(row.get("article_id") or "?", []).append(row.get("category") or "")
        # Include silent articles from frozen report n if available
        split = compute_clean_fp_metrics(article_finding_categories=list(by_art.values()))

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "source_run": str(run_dir),
        "immutable": True,
        "frozen_report_echo": {
            "clean_article_fp_rate": frozen_report.get("clean_article_fp_rate"),
            "total_findings": frozen_report.get("total_findings"),
            "fp_by_category": frozen_report.get("fp_by_category"),
        },
        "derived_split_metrics": split,
        "punctuation_count": len(punct),
        "non_punctuation_count": len(non_punct),
        "punctuation_sample_size": len(sample),
        "punctuation_subtype_counts": dict(
            Counter(r.get("punctuation_subtype") or "unknown" for r in punct).most_common()
        ),
        "run4_intermediate_targets": {
            "clean_fp_rate_all": "<=25%",
            "clean_fp_rate_editorial_only": "<=15%",
            "punctuation_findings_strict": "<=30",
            "findings_per_clean_article": "<=0.3",
            "zero_finding_clean_articles": ">=75%",
        },
        "poc_final_targets": {
            "clean_fp_rate": "<=10%",
            "editorial_precision": ">=55%",
            "quote_preservation_safety": ">=98%",
            "invalid_span_rate": "0%",
        },
        "root_cause": (
            "Dominant FPs are deterministic mechanical punctuation spacing checks "
            "(MECH-PUNCT-AFTER / MECH-PUNCT-SPACE / MECH-WS), not Gemini quality."
        ),
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # category_counts.csv
    cat_counts = Counter(r.get("category") or "unknown" for r in enriched)
    with (out_dir / "category_counts.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["category", "count"])
        for cat, n in cat_counts.most_common():
            w.writerow([cat, n])

    # article_fp_distribution.csv
    art_counts: Counter[str] = Counter()
    for row in enriched:
        art_counts[row.get("article_id") or "?"] += 1
    with (out_dir / "article_fp_distribution.csv").open(
        "w", encoding="utf-8", newline=""
    ) as fh:
        w = csv.writer(fh)
        w.writerow(["article_id", "finding_count"])
        for aid, n in sorted(art_counts.items(), key=lambda x: (-x[1], x[0])):
            w.writerow([aid, n])

    with (out_dir / "non_punctuation_todo.jsonl").open("w", encoding="utf-8") as fh:
        for row in todo_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    with (out_dir / "punctuation_sample.jsonl").open("w", encoding="utf-8") as fh:
        for row in sample:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nWrote {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
