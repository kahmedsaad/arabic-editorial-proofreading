"""CLI for scoring engine outputs against private gold.

The engine must never receive gold. This CLI only reads:
  - public case IDs implicitly via gold case_id alignment
  - engine output JSON produced from public/cases only
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark_v2.private.scorer.report_html import write_html_report
from benchmark_v2.private.scorer.score import score_outputs, score_repeated_runs, write_json_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score benchmark_v2 engine outputs")
    parser.add_argument(
        "--gold-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "gold",
        help="Private gold directory (never pass to the engine)",
    )
    parser.add_argument(
        "--outputs",
        type=Path,
        action="append",
        required=True,
        help="Engine outputs JSON (repeat for consistency runs)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "results" / "report.json",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=None,
        help="Optional HTML report path (default: sibling .html of --report)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    outputs = list(args.outputs)
    if len(outputs) == 1:
        report = score_outputs(gold_dir=args.gold_dir, outputs=outputs[0])
    else:
        report = score_repeated_runs(gold_dir=args.gold_dir, output_paths=outputs)

    write_json_report(report, args.report)
    html_path = args.html or args.report.with_suffix(".html")
    write_html_report(report, html_path)
    print(json.dumps(report.model_dump(exclude={"cases"}), ensure_ascii=False, indent=2))
    print(f"wrote {args.report}")
    print(f"wrote {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
