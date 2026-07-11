import json
from pathlib import Path

from app.models.schemas import EditorialRule, Zone


class JsonRuleRepository:
    """Local JSON rule repository. One rule per file or a rules.json array."""

    def __init__(self, rules_dir: Path) -> None:
        self.rules_dir = rules_dir
        self._rules: dict[str, EditorialRule] = {}
        self.reload()

    def reload(self) -> None:
        self._rules.clear()
        if not self.rules_dir.exists():
            return

        for path in sorted(self.rules_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            items = payload if isinstance(payload, list) else [payload]
            for item in items:
                rule = EditorialRule.model_validate(item)
                self._rules[rule.rule_id] = rule

    def list_rules(self, *, active_only: bool = True) -> list[EditorialRule]:
        rules = list(self._rules.values())
        if active_only:
            rules = [r for r in rules if r.active]
        return sorted(rules, key=lambda r: r.rule_id)

    def get(self, rule_id: str) -> EditorialRule | None:
        return self._rules.get(rule_id)

    def upsert(self, rule: EditorialRule) -> EditorialRule:
        self._rules[rule.rule_id] = rule
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        path = self.rules_dir / f"{rule.rule_id}.json"
        path.write_text(
            json.dumps(rule.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return rule

    def known_rule_ids(self) -> set[str]:
        return set(self._rules)

    def known_categories(self) -> set[str]:
        return {r.category for r in self._rules.values()} | {
            "spelling",
            "punctuation",
            "terminology",
            "entity_name",
            "attribution",
            "attribution_strength",
            "unsupported_certainty",
            "loaded_framing",
            "implicit_blame",
            "quote_voice",
            "publisher_voice",
            "headline_framing",
            "caption_framing",
            "unsupported_causality",
            "stance_drift",
            "clarity",
            "repetition",
            "grammar",
            "consistency",
            "numeric_contradiction",
            "headline_body_mismatch",
            "claim_contradiction",
            "temporal_contradiction",
            "legal_contradiction",
            "majority_precision",
            "entity_confusion",
            "pronoun_ambiguity",
            "cross_paragraph_contradiction",
            "source_misrepresentation",
            "source_quality",
        }

    def retrieve_for_segment(
        self,
        *,
        zone: Zone,
        normalized_text: str,
        limit: int = 5,
    ) -> list[EditorialRule]:
        scored: list[tuple[int, EditorialRule]] = []
        for rule in self.list_rules():
            if rule.applies_to_zones and zone not in rule.applies_to_zones:
                continue
            score = 0
            for keyword in rule.keywords:
                if keyword and keyword in normalized_text:
                    score += 2
            if score == 0 and not rule.keywords:
                score = 1
            if score > 0:
                scored.append((score, rule))
        scored.sort(key=lambda item: (-item[0], item[1].rule_id))
        return [rule for _, rule in scored[:limit]]
