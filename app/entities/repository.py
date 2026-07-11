from __future__ import annotations

import json
from pathlib import Path

from app.models.schemas import Entity
from app.normalization.arabic import normalize_arabic


class EntityRepository:
    def __init__(self, entities_dir: Path) -> None:
        self.entities_dir = entities_dir
        self._entities: dict[str, Entity] = {}
        self.reload()

    def reload(self) -> None:
        self._entities.clear()
        if not self.entities_dir.exists():
            return
        for path in sorted(self.entities_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            items = payload if isinstance(payload, list) else [payload]
            for item in items:
                entity = Entity.model_validate(item)
                self._entities[entity.entity_id] = entity

    def list_entities(self, *, active_only: bool = True) -> list[Entity]:
        values = list(self._entities.values())
        if active_only:
            values = [e for e in values if e.active]
        return sorted(values, key=lambda e: e.entity_id)

    def get(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def upsert(self, entity: Entity) -> Entity:
        self._entities[entity.entity_id] = entity
        self.entities_dir.mkdir(parents=True, exist_ok=True)
        path = self.entities_dir / f"{entity.entity_id}.json"
        path.write_text(
            json.dumps(entity.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return entity

    def known_ids(self) -> set[str]:
        return set(self._entities)

    def alias_map(self) -> dict[str, tuple[str, str]]:
        """alias -> (canonical, entity_id), excluding canonical itself."""
        mapping: dict[str, tuple[str, str]] = {}
        for entity in self.list_entities():
            for alias in entity.aliases:
                if alias and alias != entity.canonical_ar:
                    mapping[alias] = (entity.canonical_ar, entity.entity_id)
        return mapping

    def forms_by_entity(self) -> dict[str, list[str]]:
        forms: dict[str, list[str]] = {}
        for entity in self.list_entities():
            forms[entity.entity_id] = [entity.canonical_ar, *entity.aliases]
        return forms


def match_entities_in_text(text: str, entities: list[Entity]) -> list[Entity]:
    """Return entities whose canonical or alias appears in text (normalized match)."""
    normalized = normalize_arabic(text)
    matched: list[Entity] = []
    for entity in entities:
        forms = [entity.canonical_ar, *entity.aliases]
        if any(normalize_arabic(form) and normalize_arabic(form) in normalized for form in forms):
            matched.append(entity)
    return matched
