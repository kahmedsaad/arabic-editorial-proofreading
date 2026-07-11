"""Optional live Gemini test — skipped unless RUN_GEMINI_LIVE=1."""

import os

import pytest

from app.ai.gemini_client import GeminiEditorialAIClient
from app.models.schemas import Segment, Zone

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_GEMINI_LIVE") != "1",
    reason="Set RUN_GEMINI_LIVE=1 to run live Gemini integration",
)


@pytest.mark.asyncio
async def test_live_gemini_returns_list_or_fallback():
    client = GeminiEditorialAIClient(timeout_seconds=20)
    segments = [
        Segment(
            segment_id="SEG-001",
            document_id="DOC-LIVE",
            zone=Zone.HEADLINE,
            text="حسب مصادر محلية",
            normalized_text="حسب مصادر محلية",
            start_offset=0,
            end_offset=15,
            sequence=1,
        )
    ]
    findings = await client.discover_candidates(
        document_id="DOC-LIVE",
        segments=segments,
        mechanical_findings=[],
        rules=[],
    )
    assert isinstance(findings, list)
