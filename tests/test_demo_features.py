"""Tests for demo auth, prompts, staged review, and bulk paste."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.schemas import ReviewRequest
from app.orchestration.review import ReviewOrchestrator
from app.rules.bulk import parse_entities_paste, parse_rules_paste


@pytest.mark.asyncio
async def test_login_admin_and_list_prompts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        bad = await client.post(
            "/api/v1/auth/login", json={"username": "user", "password": "wrong"}
        )
        assert bad.status_code == 401

        ok = await client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin"}
        )
        assert ok.status_code == 200
        token = ok.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        prompts = await client.get("/api/v1/admin/prompts", headers=headers)
        assert prompts.status_code == 200
        phases = {p["phase"] for p in prompts.json()}
        assert {"discover", "judge", "repair", "rule_author"} <= phases


@pytest.mark.asyncio
async def test_review_includes_stages():
    orchestrator = ReviewOrchestrator()
    result = await orchestrator.review(
        ReviewRequest(
            document_id="DOC-STAGES",
            headline="حسب مصادر رسمية",
            body="النص هنا عن حزب الله.",
        )
    )
    stage_ids = [s.stage_id for s in result.stages]
    assert stage_ids[0] == "retrieve"
    assert "candidates" in stage_ids
    assert "judgment" in stage_ids
    assert "validation" in stage_ids
    assert stage_ids[-1] == "final"


def test_parse_entities_and_rules_paste():
    entities = parse_entities_paste(
        "canonical_ar\taliases\tcategory\nحزب الله\tالحزب;الجماعة\torganization\n"
    )
    assert len(entities) == 1
    assert entities[0].canonical_ar == "حزب الله"
    assert "الحزب" in entities[0].aliases

    rules = parse_rules_paste(
        "title_ar\tdescription_ar\tcategory\tkeywords\nقاعدة تجريبية\tوصف القاعدة\tterminology\tكلمة;أخرى\n"
    )
    assert len(rules) == 1
    assert rules[0].title_ar == "قاعدة تجريبية"
    assert "كلمة" in rules[0].keywords
