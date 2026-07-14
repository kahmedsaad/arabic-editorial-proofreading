"""Punctuation policy modes, subtypes, and confidence thresholds (run4 precision)."""

from __future__ import annotations

from typing import Literal

PunctuationPolicy = Literal["off", "strict", "full"]

PUNCTUATION_SUBTYPES = (
    "repeated_punctuation",
    "unbalanced_quotes",
    "unbalanced_parentheses",
    "unbalanced_brackets",
    "broken_sentence_boundary",
    "malformed_spacing",
    "optional_comma",
    "optional_period",
    "headline_style",
    "quote_internal_style",
    "other",
)

# Strict mode: only these objective high-value subtypes (plus gated malformed_spacing).
STRICT_ALLOWED_SUBTYPES = frozenset(
    {
        "repeated_punctuation",
        "unbalanced_quotes",
        "unbalanced_parentheses",
        "unbalanced_brackets",
        "broken_sentence_boundary",
    }
)

# Subtype confidence floors (central config).
PUNCTUATION_SUBTYPE_THRESHOLDS: dict[str, float] = {
    "repeated_punctuation": 0.95,
    "unbalanced_quotes": 0.95,
    "unbalanced_parentheses": 0.95,
    "unbalanced_brackets": 0.95,
    "broken_sentence_boundary": 0.92,
    "malformed_spacing": 0.98,
    "optional_comma": 1.01,  # effectively suppressed
    "optional_period": 1.01,
    "headline_style": 1.01,
    "quote_internal_style": 1.01,
    "other": 1.01,
}

RULE_ID_TO_SUBTYPE: dict[str, str] = {
    "MECH-PUNCT-DUP": "repeated_punctuation",
    "MECH-QUOTE": "unbalanced_quotes",
    "MECH-PAREN": "unbalanced_parentheses",
    "MECH-BRACK": "unbalanced_brackets",
    "MECH-SENT-BOUND": "broken_sentence_boundary",
    "MECH-PUNCT-SPACE": "malformed_spacing",
    "MECH-PUNCT-AFTER": "malformed_spacing",
    "MECH-WS": "malformed_spacing",
}


def normalize_policy(value: str | None) -> PunctuationPolicy:
    raw = (value or "strict").strip().lower()
    if raw in {"off", "strict", "full"}:
        return raw  # type: ignore[return-value]
    return "strict"


def threshold_for_subtype(subtype: str) -> float:
    return PUNCTUATION_SUBTYPE_THRESHOLDS.get(subtype, 1.01)
