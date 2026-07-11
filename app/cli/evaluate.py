from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.config import ROOT_DIR
from app.evaluation.metrics import metrics_to_dict, run_evaluation
from app.models.schemas import ReviewRequest
from app.orchestration.review import ReviewOrchestrator


async def _review_record(orchestrator: ReviewOrchestrator, record):
    return await orchestrator.review(
        ReviewRequest(
            document_id=record.record_id,
            headline=record.headline,
            body=record.body,
            source="evaluation",
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate proofreading engine on golden JSONL")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=ROOT_DIR / "data" / "evaluation" / "golden.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON report path",
    )
    args = parser.parse_args(argv)
    orchestrator = ReviewOrchestrator()

    async def review_fn(record):
        return await _review_record(orchestrator, record)

    metrics = asyncio.run(run_evaluation(args.dataset, review_fn))
    payload = metrics_to_dict(metrics)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
