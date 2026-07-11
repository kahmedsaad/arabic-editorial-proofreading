#!/usr/bin/env python
"""5-minute POC demo: health → parse → review → debug → evaluate."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

SAMPLE = {
    "document_id": "DOC-DEMO-001",
    "headline": "حسب مصادر محلية!! الحكومة تتحمل مسؤلية اللأمر",
    "body": "قال قال المتحدث إن الوضع  مستقر .\nوأضاف أن الإجراءات الجديدة بدأت في تونس.",
}


async def run_demo(*, base_url: str | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("AI_CLIENT =", settings.ai_client)
    print("USE_GCP   =", settings.use_gcp)
    print("---")

    if base_url:
        client_cm = AsyncClient(base_url=base_url, timeout=60.0)
    else:
        client_cm = AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://demo.local",
            timeout=60.0,
        )

    async with client_cm as client:
        health = await client.get("/api/v1/health")
        print("1) HEALTH", health.status_code, health.json())

        parsed = await client.post(
            "/api/v1/documents/parse",
            json={"text": SAMPLE["headline"] + "\n\n" + SAMPLE["body"]},
        )
        print(
            "2) PARSE ",
            parsed.status_code,
            f"segments={len(parsed.json().get('segments', []))}",
        )

        review = await client.post("/api/v1/reviews", json=SAMPLE)
        review.raise_for_status()
        payload = review.json()
        print(
            "3) REVIEW",
            review.status_code,
            f"findings={len(payload['findings'])} "
            f"rejected={len(payload['rejected_findings'])} "
            f"mech={payload['mechanical_finding_count']} "
            f"ai={payload['ai_finding_count']}",
        )
        for finding in payload["findings"][:5]:
            print(
                "   -",
                finding["category"],
                "|",
                finding["original_text"],
                "->",
                finding.get("suggested_text"),
            )

        review_id = payload["review_id"]
        editor = await client.get(f"/api/v1/reviews/{review_id}")
        debug = await client.get(f"/api/v1/reviews/{review_id}/debug")
        print(
            "4) GET   ",
            f"editor_rejected={len(editor.json()['rejected_findings'])} "
            f"debug_rejected={len(debug.json()['rejected_findings'])}",
        )

        evaluation = await client.post("/api/v1/evaluations/run", json={})
        evaluation.raise_for_status()
        metrics = evaluation.json()["metrics"]
        print(
            "5) EVAL  ",
            f"P={metrics['precision']:.2f} R={metrics['recall']:.2f} "
            f"F1={metrics['f1']:.2f} "
            f"expected={metrics['expected_issues']} detected={metrics['detected_issues']}",
        )
        print("---")
        print("Demo complete.")
        summary = {"review_id": review_id, "run_id": evaluation.json()["run_id"]}
        print(json.dumps(summary, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run POC demo against in-process app or URL")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Optional running server, e.g. http://localhost:8000",
    )
    args = parser.parse_args(argv)
    return asyncio.run(run_demo(base_url=args.base_url))


if __name__ == "__main__":
    raise SystemExit(main())
