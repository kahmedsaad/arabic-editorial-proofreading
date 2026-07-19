from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable


_GENERIC_CONTRADICTION_ALIASES = {
    "consistency",
    "internal_inconsistency",
    "contradiction",
}

_RULE_PRECEDENCE = (
    ("CONS-DATE", "temporal_contradiction"),
    ("CONS-NUMBER", "numeric_contradiction"),
    ("CONS-NAME", "entity_confusion"),
    ("CONS-CLAIM", "claim_contradiction"),
)

_DIRECT_RULE_ALIASES = {
    "numbers": ("CONS-NUMBER", "numeric_contradiction"),
    "date": ("CONS-DATE", "temporal_contradiction"),
    "name": ("CONS-NAME", "entity_confusion"),
}


@dataclass(frozen=True)
class CategoryCanonicalization:
    raw_category: str
    normalized_category: str
    canonical_category: str
    rule_ids: tuple[str, ...]
    mapping_occurred: bool
    alias_mapping_occurred: bool
    reason_code: str

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rule_ids"] = list(self.rule_ids)
        return payload


def normalize_category_token(category: object) -> str:
    """Normalize category syntax only; never infer or fuzzy-match semantics."""
    token = str(category or "").strip().lower()
    token = re.sub(r"[\s-]+", "_", token)
    return re.sub(r"_+", "_", token)


def canonicalize_category(
    category: object,
    rule_ids: Iterable[object] = (),
) -> CategoryCanonicalization:
    """Apply reviewed aliases only when an exact structured rule corroborates them."""
    raw_category = str(category or "")
    normalized = normalize_category_token(raw_category)
    raw_rules = tuple(str(rule_id) for rule_id in rule_ids)
    normalized_rules = {
        rule_id.strip().upper() for rule_id in raw_rules if rule_id.strip()
    }

    canonical = normalized
    alias_mapped = False
    reason = "category_canonicalization:unchanged"

    if normalized in _GENERIC_CONTRADICTION_ALIASES:
        for rule_id, target in _RULE_PRECEDENCE:
            if rule_id in normalized_rules:
                canonical = target
                alias_mapped = True
                reason = f"category_canonicalization:{rule_id.lower()}"
                break
        if not alias_mapped:
            reason = "category_canonicalization:generic_alias_without_approved_rule"
    elif normalized in _DIRECT_RULE_ALIASES:
        rule_id, target = _DIRECT_RULE_ALIASES[normalized]
        if rule_id in normalized_rules:
            canonical = target
            alias_mapped = True
            reason = f"category_canonicalization:{rule_id.lower()}"
        else:
            reason = "category_canonicalization:alias_without_required_rule"
    elif normalized != raw_category:
        reason = "category_canonicalization:syntax_normalization"

    return CategoryCanonicalization(
        raw_category=raw_category,
        normalized_category=normalized,
        canonical_category=canonical,
        rule_ids=raw_rules,
        mapping_occurred=canonical != raw_category,
        alias_mapping_occurred=alias_mapped,
        reason_code=reason,
    )
