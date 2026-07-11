from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.evaluation.metrics import load_golden, run_evaluation
from app.main import app
from app.models.schemas import ReviewRequest
from app.orchestration.review import ReviewOrchestrator

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_parse_and_rules_entities_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        parsed = await client.post(
            "/api/v1/documents/parse",
            json={"text": "عنوان\n\nفقرة أولى."},
        )
        assert parsed.status_code == 200
        assert parsed.json()["segments"]

        rules = await client.get("/api/v1/rules")
        assert rules.status_code == 200
        assert any(r["rule_id"] == "ATTR-001" for r in rules.json())

        entities = await client.get("/api/v1/entities")
        assert entities.status_code == 200


@pytest.mark.asyncio
async def test_review_persist_and_debug():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/api/v1/reviews",
            json={
                "document_id": "DOC-STORE",
                "headline": "حسب مصادر",
                "body": "قال قال النص.",
            },
        )
        assert created.status_code == 200
        review_id = created.json()["review_id"]
        got = await client.get(f"/api/v1/reviews/{review_id}")
        assert got.status_code == 200
        assert got.json()["rejected_findings"] == []
        debug = await client.get(f"/api/v1/reviews/{review_id}/debug")
        assert debug.status_code == 200
        assert debug.json()["rejected_findings"]


@pytest.mark.asyncio
async def test_evaluation_cli_metrics():
    golden = ROOT / "data" / "evaluation" / "golden.jsonl"
    assert load_golden(golden)
    orch = ReviewOrchestrator()

    async def review_fn(record):
        return await orch.review(
            ReviewRequest(
                document_id=record.record_id,
                headline=record.headline,
                body=record.body,
            )
        )

    metrics = await run_evaluation(golden, review_fn)
    assert metrics.detected_issues >= 1
    assert metrics.processing_time_ms >= 0
