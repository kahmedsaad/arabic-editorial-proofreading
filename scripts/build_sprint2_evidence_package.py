#!/usr/bin/env python3
"""Assemble Sprint 2 evidence package (read-only; no gate implementation)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_partial_actions(out: Path, *, run4_ready: bool, labels_ready: bool) -> None:
    lines = [
        "# Recommended next actions (evidence package)",
        "",
        "Status:",
        f"- run4 no-punctuation ready: **{run4_ready}**",
        f"- human labels scored: **{labels_ready}**",
        "",
        "Do **not** implement `gemini_run5_editorial_gates` until both are true.",
        "",
    ]
    if not run4_ready:
        lines.append("- Wait for `gemini_run4_no_punctuation` to finish, then re-run this script.")
    if not labels_ready:
        lines += [
            "- Label `data/local/sprint2/non_punctuation_priority_to_label.jsonl` (or the working copy).",
            "- Score with `python scripts/score_editorial_labels.py`.",
        ]
    if run4_ready and labels_ready:
        lines += [
            "",
            "When both are ready, fill category rows from `human_label_summary.json`:",
            "",
            "| Category | Labeled | Keep rate | Drop rate | Top drop reasons | Example FPs | Recommended action | Recall risk | Regression tests |",
            "|----------|---------|-----------|-----------|------------------|-------------|--------------------|-------------|------------------|",
            "| Attribution | … | … | … | … | … | Pending evidence | Check attribution recall | … |",
            "",
            "Only then design targeted suppressions for high drop-rate categories.",
        ]
    (out / "recommended_next_actions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build sprint2 evidence package")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data" / "evaluation" / "analysis" / "sprint2_precision_evidence",
    )
    args = parser.parse_args(argv)
    out: Path = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    run4 = ROOT / "data" / "evaluation" / "runs" / "gemini_run4_no_punctuation" / "report.json"
    cmp = (
        ROOT
        / "data"
        / "evaluation"
        / "analysis"
        / "run3_vs_run4_no_punctuation"
        / "summary.json"
    )
    labels = ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3"

    run4_ready = run4.exists()
    labels_ready = (labels / "summary.json").exists()

    if run4_ready:
        shutil.copy2(run4, out / "run4_baseline_summary.json")
    else:
        (out / "run4_baseline_summary.json").write_text(
            json.dumps({"status": "pending", "path": str(run4)}, indent=2) + "\n",
            encoding="utf-8",
        )

    if cmp.exists():
        shutil.copy2(cmp, out / "run3_vs_run4_summary.json")
    else:
        (out / "run3_vs_run4_summary.json").write_text(
            json.dumps({"status": "pending", "path": str(cmp)}, indent=2) + "\n",
            encoding="utf-8",
        )

    if labels_ready:
        shutil.copy2(labels / "summary.json", out / "human_label_summary.json")
        for name in ("category_precision.csv", "drop_reasons.csv"):
            src = labels / name
            if src.exists():
                shutil.copy2(src, out / name)
        # Top FP examples = drops
        drops = []
        labeled_csv = labels / "labeled_findings.csv"
        if labeled_csv.exists():
            import csv

            with labeled_csv.open(encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    if (row.get("decision") or "").lower() == "drop":
                        drops.append(row)
            drops = drops[:50]
        with (out / "top_false_positive_examples.jsonl").open("w", encoding="utf-8") as fh:
            for row in drops:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    else:
        (out / "human_label_summary.json").write_text(
            json.dumps({"status": "pending_labels"}, indent=2) + "\n", encoding="utf-8"
        )
        (out / "category_precision.csv").write_text(
            "category,findings,keep,drop,uncertain,precision\n", encoding="utf-8"
        )
        (out / "drop_reasons.csv").write_text("drop_reason,count\n", encoding="utf-8")
        (out / "top_false_positive_examples.jsonl").write_text("", encoding="utf-8")

    _write_partial_actions(out, run4_ready=run4_ready, labels_ready=labels_ready)
    print(
        json.dumps(
            {"out": str(out), "run4_ready": run4_ready, "labels_ready": labels_ready},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
