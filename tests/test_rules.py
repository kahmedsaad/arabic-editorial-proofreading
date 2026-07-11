from pathlib import Path

from app.models.schemas import Zone
from app.rules.repository import JsonRuleRepository

ROOT = Path(__file__).resolve().parents[1]


def test_loads_seed_rules():
    repo = JsonRuleRepository(ROOT / "data" / "rules")
    rules = repo.list_rules()
    ids = {r.rule_id for r in rules}
    assert "ATTR-001" in ids
    assert "SPELL-001" in ids
    retrieved = repo.retrieve_for_segment(
        zone=Zone.HEADLINE,
        normalized_text="قال مصدر إن الحكومة",
        limit=5,
    )
    assert any(r.rule_id == "ATTR-001" for r in retrieved)
