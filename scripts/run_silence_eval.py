#!/usr/bin/env python3
"""Sprint 2: freeze a silence / clean-article eval run (gemini_run3 target).

On a silence set (expected_issues=[]), every finding is an FP. Reports:
- clean_article_fp_rate = share of articles with ≥1 finding
- findings_per_article
- FP counts by category (attribution, quote_voice, …)

Also writes a findings dump ready for keep/drop labeling.

Usage:
  python scripts/run_silence_eval.py --run-id gemini_run3
  python scripts/run_silence_eval.py --dataset data/evaluation/sprint2/silence_seed.jsonl --run-id smoke
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation.clean_metrics import compute_clean_fp_metrics  # noqa: E402
from app.evaluation.metrics import load_golden  # noqa: E402
from app.config import settings  # noqa: E402
from app.models.schemas import ReviewRequest  # noqa: E402
from app.orchestration.review import ReviewOrchestrator  # noqa: E402
from app.postprocess.punctuation_policy import normalize_policy  # noqa: E402

FP_FAMILIES = (
    "attribution",
    "attribution_strength",
    "source_quality",
    "quote_voice",
    "publisher_voice",
    "headline_framing",
    "consistency",
)


def _family(category: str) -> str:
    c = (category or "").lower()
    if c in {"attribution", "attribution_strength", "source_quality", "source_misrepresentation"}:
        return "attribution"
    if c in {"quote_voice"}:
        return "quote_voice"
    if c in {"publisher_voice", "headline_framing", "caption_framing"}:
        return "headline_compression"
    if "مصدر" in c or c == "vague_source":
        return "vague_masadir"
    if c in {"consistency"}:
        return "consistency"
    return c or "other"


async def _run(dataset: Path, run_id: str, out_dir: Path) -> dict:
    orchestrator = ReviewOrchestrator()
    records = load_golden(dataset)
    article_rows: list[dict] = []
    label_rows: list[dict] = []
    family_counts: Counter[str] = Counter()
    per_article_categories: list[list[str]] = []

    for i, record in enumerate(records, start=1):
        print(f"[{i}/{len(records)}] {record.record_id}", flush=True)
        response = await orchestrator.review(
            ReviewRequest(
                document_id=record.record_id,
                headline=record.headline,
                body=record.body,
                source="sprint2_silence_eval",
            )
        )
        findings = list(response.findings or [])
        cats: list[str] = []
        for finding in findings:
            payload = finding.model_dump() if hasattr(finding, "model_dump") else dict(finding)
            cat = payload.get("category") or ""
            cats.append(cat)
            family_counts[_family(cat)] += 1
            label_rows.append(
                {
                    "label_id": f"{run_id}:{record.record_id}:{payload.get('finding_id')}",
                    "run_id": run_id,
                    "article_id": record.record_id,
                    "finding_id": payload.get("finding_id"),
                    "category": cat,
                    "fp_family": _family(cat),
                    "punctuation_subtype": payload.get("punctuation_subtype"),
                    "severity": payload.get("severity"),
                    "decision": payload.get("decision"),
                    "original_text": payload.get("original_text"),
                    "suggested_text": payload.get("suggested_text"),
                    "explanation_ar": payload.get("explanation_ar"),
                    "confidence": payload.get("confidence"),
                    "source": payload.get("source"),
                    "segment_id": payload.get("segment_id"),
                    "start_offset": payload.get("start_offset"),
                    "end_offset": payload.get("end_offset"),
                    "headline": record.headline[:200],
                    "body_excerpt": (record.body or "")[:400],
                    # Editor fills these:
                    "annotator_decision": None,  # keep | drop | modify
                    "drop_reason": None,
                    "notes": None,
                }
            )
        per_article_categories.append(cats)
        article_rows.append(
            {
                "record_id": record.record_id,
                "finding_count": len(findings),
                "categories": cats,
            }
        )

    split = compute_clean_fp_metrics(article_finding_categories=per_article_categories)
    report = {
        "run_id": run_id,
        "dataset": str(dataset),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "punctuation_policy": normalize_policy(settings.punctuation_policy),
        **split,
        "fp_by_family": dict(family_counts.most_common()),
        "target_clean_fp_rate": 0.10,
        "run4_intermediate_targets": {
            "clean_fp_rate_all": 0.25,
            "clean_fp_rate_editorial_only": 0.15,
            "punctuation_findings_strict_max": 30,
            "findings_per_article_all": 0.3,
            "zero_finding_clean_article_rate": 0.75,
        },
        "notes": (
            "Silence set: expected_issues empty -> every finding counts as FP. "
            "Freeze this report before prompt/gate changes; compare run4 vs run3."
        ),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (out_dir / "articles.jsonl").open("w", encoding="utf-8") as fh:
        for row in article_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    labels_path = out_dir / "fp_labels_todo.jsonl"
    with labels_path.open("w", encoding="utf-8") as fh:
        for row in label_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    report["labels_path"] = str(labels_path)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze silence eval run")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=ROOT / "data" / "local" / "sprint2" / "silence_v1.jsonl",
    )
    parser.add_argument("--run-id", default="gemini_run3")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Defaults to data/evaluation/runs/<run-id>/",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow writing into an existing run directory (default: refuse)",
    )
    args = parser.parse_args(argv)

    dataset = args.dataset
    if not dataset.exists():
        seed = ROOT / "data" / "evaluation" / "sprint2" / "silence_seed.jsonl"
        if seed.exists():
            print(f"dataset missing ({dataset}); falling back to {seed}", flush=True)
            dataset = seed
        else:
            raise SystemExit(
                f"Missing dataset {dataset}. Run: python scripts/sample_silence_set.py --n 300"
            )

    out_dir = args.out_dir or (ROOT / "data" / "evaluation" / "runs" / args.run_id)
    if out_dir.exists() and any(out_dir.iterdir()) and not args.overwrite:
        raise SystemExit(
            f"Run directory already exists and is non-empty: {out_dir}\n"
            "Refusing to overwrite. Pass --overwrite only if intentional.\n"
            "Resume is not supported; wait for the in-progress run or use a new --run-id."
        )

    report = asyncio.run(_run(dataset, args.run_id, out_dir))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nWrote {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
