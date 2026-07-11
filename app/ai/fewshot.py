"""Load compact golden examples for Gemini few-shot packets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MUST_CHECK_RULES = [
    {
        "rule_id": "R_DESC_NONSTATE",
        "look_for": "مقاتل / مقاتليه / مقاتليها in publisher voice",
        "preferred": "عناصر / عناصره / عناصرها",
        "decision": "hard_warning",
    },
    {
        "rule_id": "R_SOURCE_VAGUE",
        "look_for": "وسائل إعلام / مصادر مطلعة without naming outlet",
        "preferred": "named outlet or soften attribution",
        "decision": "hard_warning",
    },
    {
        "rule_id": "R_ATTR_CONFIRMATION",
        "look_for": "تأكيد / أكد with a single source",
        "preferred": "قال / قوله",
        "decision": "soft_warning",
    },
    {
        "rule_id": "R_LOADED_FRAME",
        "look_for": "loaded phrasing inside quotes",
        "preferred": "preserve quote; needs_editor_review; no rewrite",
        "decision": "needs_editor_review",
    },
    {
        "rule_id": "R_TERROR_LABEL",
        "look_for": "منظمة إرهابية / إرهابي inside quotes",
        "preferred": "preserve quote; needs_editor_review; no rewrite",
        "decision": "needs_editor_review",
    },
    {
        "rule_id": "R03/R04/R07",
        "look_for": "ميليشيا / مدعومة من الخارج / ترهيب in captions",
        "preferred": "hard_warning; do not invent facts",
        "decision": "hard_warning",
    },
]


def load_golden_fewshots(path: Path, *, limit: int = 8) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    examples: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        for issue in record.get("expected_issues") or []:
            examples.append(
                {
                    "record_id": record.get("record_id"),
                    "section_id": record.get("section_id"),
                    "original_text": issue.get("original_text"),
                    "suggested_text": issue.get("suggested_text"),
                    "decision": issue.get("expected_decision"),
                    "rule_ids": issue.get("expected_rules") or [],
                    "category": issue.get("category"),
                    "must_not_rewrite": bool(issue.get("must_not_rewrite")),
                }
            )
            if len(examples) >= limit:
                return examples
    return examples
