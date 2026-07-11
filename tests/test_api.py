import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.schemas import ReviewRequest
from app.orchestration.review import ReviewOrchestrator

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_reviews_endpoint_returns_validated_findings():
    fixture = json.loads(
        (ROOT / "data" / "fixtures" / "sample_article.json").read_text(encoding="utf-8")
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/reviews", json=fixture)
    assert response.status_code == 200
    payload = response.json()
    assert payload["document"]["document_id"] == "DOC-FIXTURE-001"
    assert payload["segments"]
    assert payload["mechanical_finding_count"] >= 1
    # Invalid mock finding excluded from editor findings
    finding_ids = {f["finding_id"] for f in payload["findings"]}
    assert "FND-AI-INVALID" not in finding_ids
    assert any(f["finding_id"] == "FND-AI-INVALID" for f in payload["rejected_findings"])
    for finding in payload["findings"]:
        segment = next(s for s in payload["segments"] if s["segment_id"] == finding["segment_id"])
        span = segment["text"][finding["start_offset"] : finding["end_offset"]]
        assert span == finding["original_text"]


@pytest.mark.asyncio
async def test_orchestrator_direct():
    orchestrator = ReviewOrchestrator()
    result = await orchestrator.review(
        ReviewRequest(
            document_id="DOC-DIRECT",
            headline="حسب مصادر رسمية",
            body="النص هنا.",
        )
    )
    assert result.document.document_id == "DOC-DIRECT"
    assert any(f.finding_id == "FND-AI-0001" for f in result.findings)
    assert any(f.finding_id == "FND-AI-INVALID" for f in result.rejected_findings)
