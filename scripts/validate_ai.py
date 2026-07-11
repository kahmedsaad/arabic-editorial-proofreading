#!/usr/bin/env python
"""Validate AI editorial quality: mock vs optional Gemini scorecard."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai.gemini_client import GeminiEditorialAIClient  # noqa: E402
from app.ai.mock_client import MockEditorialAIClient  # noqa: E402
from app.config import settings  # noqa: E402
from app.evaluation.editorial import (  # noqa: E402
    load_editorial_golden,
    score_editorial_findings,
)
from app.models.schemas import ReviewRequest  # noqa: E402
from app.orchestration.review import ReviewOrchestrator  # noqa: E402


def _load_article(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


async def _run_client(name: str, client, article: dict) -> dict:
    orchestrator = ReviewOrchestrator(ai_client=client)
    started = time.perf_counter()
    # Include caption in body so caption goldens are reachable with current zones.
    body = article.get("body", "")
    caption = (article.get("metadata") or {}).get("caption")
    if caption and caption not in body:
        body = f"{body}\n{caption}"
    response = await orchestrator.review(
        ReviewRequest(
            document_id=article.get("article_id", "DOC-EDITORIAL"),
            headline=article.get("headline") or article.get("title", ""),
            body=body,
            source="editorial_validation",
            metadata=article.get("metadata") or {},
        )
    )
    elapsed = (time.perf_counter() - started) * 1000
    return {
        "client": name,
        "response": response,
        "elapsed_ms": elapsed,
    }


def _print_card(card_dict: dict) -> None:
    print(f"\n=== {card_dict['client'].upper()} ===")
    print(
        f"span_recall={card_dict['span_recall']:.2f} "
        f"decision_recall={card_dict['decision_recall']:.2f} "
        f"quote_preserve={card_dict['quote_preserve_rate']:.2f}"
    )
    print(
        f"hits: span={card_dict['span_hits']}/{card_dict['gold_total']} "
        f"decision={card_dict['decision_hits']} "
        f"rules={card_dict['rule_hits']} "
        f"suggestions={card_dict['suggestion_hits']}"
    )
    print(
        f"findings={card_dict['detected_findings']} "
        f"rejected={card_dict['rejected_findings']} "
        f"time_ms={card_dict['processing_time_ms']}"
    )
    print(f"poc_pass={card_dict['poc_pass']}")
    for detail in card_dict["details"]:
        flags = []
        if detail.get("span_hit"):
            flags.append("span")
        if detail.get("decision_hit"):
            flags.append("decision")
        if detail.get("rule_hit"):
            flags.append("rule")
        if detail.get("suggestion_hit"):
            flags.append("suggest")
        if detail.get("quote_ok") is True:
            flags.append("quote_ok")
        if detail.get("quote_ok") is False:
            flags.append("quote_FAIL")
        print(f"  - {detail['gold_id']}: {detail['span'][:40]} [{', '.join(flags) or 'MISS'}]")


async def main_async(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Validate AI editorial findings")
    parser.add_argument(
        "--article",
        type=Path,
        default=ROOT / "data" / "evaluation" / "hezbollah_article.json",
    )
    parser.add_argument(
        "--golden",
        type=Path,
        default=ROOT / "data" / "evaluation" / "golden_editorial.jsonl",
    )
    parser.add_argument(
        "--with-gemini",
        action="store_true",
        help="Also run Gemini client (needs GEMINI_API_KEY / credentials)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "evaluation" / "ai_scorecard.json",
    )
    args = parser.parse_args(argv)

    article = _load_article(args.article)
    expectations = load_editorial_golden(args.golden)
    print(f"article={article.get('article_id')}")
    print(f"golden_expectations={len(expectations)}")
    print(f"settings.ai_client={settings.ai_client}")

    results = []
    mock_run = await _run_client("mock", MockEditorialAIClient(), article)
    mock_card = score_editorial_findings(
        client="mock",
        expectations=expectations,
        findings=[f.model_dump(mode="json") for f in mock_run["response"].findings],
        rejected=[f.model_dump(mode="json") for f in mock_run["response"].rejected_findings],
        processing_time_ms=mock_run["elapsed_ms"],
    )
    results.append(mock_card.to_dict())
    _print_card(results[-1])

    if args.with_gemini or settings.ai_client.lower() == "gemini":
        gemini_client = GeminiEditorialAIClient()
        gemini_run = await _run_client("gemini", gemini_client, article)
        gemini_card = score_editorial_findings(
            client="gemini",
            expectations=expectations,
            findings=[f.model_dump(mode="json") for f in gemini_run["response"].findings],
            rejected=[f.model_dump(mode="json") for f in gemini_run["response"].rejected_findings],
            processing_time_ms=gemini_run["elapsed_ms"],
        )
        card = gemini_card.to_dict()
        if gemini_client.last_token_usage:
            card["token_usage"] = gemini_client.last_token_usage
        if gemini_client.last_latency_ms is not None:
            card["gemini_latency_ms"] = gemini_client.last_latency_ms
        results.append(card)
        _print_card(results[-1])

    payload = {
        "article_id": article.get("article_id"),
        "golden_path": str(args.golden),
        "clients": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nWrote {args.output}")

    mock_pass = results[0]["poc_pass"]
    if len(results) > 1:
        return 0 if (mock_pass and results[1]["poc_pass"]) else 1
    return 0 if mock_pass else 1


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(main_async(argv))


if __name__ == "__main__":
    raise SystemExit(main())
