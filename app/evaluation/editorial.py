from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EditorialExpectation:
    gold_id: str
    original_text: str
    expected_decision: str
    expected_rules: list[str] = field(default_factory=list)
    suggested_text: str | None = None
    category: str | None = None
    must_not_rewrite: bool = False
    section_id: str | None = None


@dataclass
class EditorialScorecard:
    client: str
    gold_total: int = 0
    span_hits: int = 0
    decision_hits: int = 0
    rule_hits: int = 0
    suggestion_hits: int = 0
    quote_preserve_ok: int = 0
    quote_preserve_total: int = 0
    detected_findings: int = 0
    rejected_findings: int = 0
    processing_time_ms: float = 0.0
    details: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def span_recall(self) -> float:
        return self.span_hits / self.gold_total if self.gold_total else 0.0

    @property
    def decision_recall(self) -> float:
        return self.decision_hits / self.gold_total if self.gold_total else 0.0

    @property
    def quote_preserve_rate(self) -> float:
        return (
            self.quote_preserve_ok / self.quote_preserve_total
            if self.quote_preserve_total
            else 1.0
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "client": self.client,
            "gold_total": self.gold_total,
            "span_hits": self.span_hits,
            "decision_hits": self.decision_hits,
            "rule_hits": self.rule_hits,
            "suggestion_hits": self.suggestion_hits,
            "span_recall": round(self.span_recall, 3),
            "decision_recall": round(self.decision_recall, 3),
            "quote_preserve_ok": self.quote_preserve_ok,
            "quote_preserve_total": self.quote_preserve_total,
            "quote_preserve_rate": round(self.quote_preserve_rate, 3),
            "detected_findings": self.detected_findings,
            "rejected_findings": self.rejected_findings,
            "processing_time_ms": round(self.processing_time_ms, 1),
            "poc_pass": self.span_recall >= 0.6 and self.quote_preserve_rate >= 0.5,
            "details": self.details,
            "errors": self.errors,
        }


_DECISION_ALIASES = {
    "acceptable_with_note": {
        "needs_editor_review",
        "acceptable",
        "soft_warning",
        "acceptable_with_note",
    },
    "hard_warning": {"hard_warning", "ban", "needs_editor_review"},
    "soft_warning": {"soft_warning", "suggest", "needs_editor_review"},
    "needs_editor_review": {"needs_editor_review", "soft_warning", "hard_warning"},
}


def load_editorial_golden(path: Path) -> list[EditorialExpectation]:
    expectations: list[EditorialExpectation] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        for item in raw.get("expected_issues", []):
            expectations.append(
                EditorialExpectation(
                    gold_id=raw.get("record_id") or raw.get("gold_id") or "GOLD",
                    original_text=item["original_text"],
                    expected_decision=item.get("expected_decision")
                    or item.get("decision")
                    or "needs_editor_review",
                    expected_rules=list(item.get("expected_rules") or item.get("rule_ids") or []),
                    suggested_text=item.get("suggested_text"),
                    category=item.get("category"),
                    must_not_rewrite=bool(item.get("must_not_rewrite", False)),
                    section_id=raw.get("section_id"),
                )
            )
    return expectations


def _decision_match(expected: str, actual: str | None) -> bool:
    if actual is None:
        return False
    actual_s = str(getattr(actual, "value", actual))
    allowed = _DECISION_ALIASES.get(expected, {expected})
    return actual_s in allowed


def score_editorial_findings(
    *,
    client: str,
    expectations: list[EditorialExpectation],
    findings: list[dict[str, Any]],
    rejected: list[dict[str, Any]] | None = None,
    processing_time_ms: float = 0.0,
) -> EditorialScorecard:
    card = EditorialScorecard(
        client=client,
        gold_total=len(expectations),
        detected_findings=len(findings),
        rejected_findings=len(rejected or []),
        processing_time_ms=processing_time_ms,
    )

    for exp in expectations:
        detail: dict[str, Any] = {
            "gold_id": exp.gold_id,
            "span": exp.original_text,
            "span_hit": False,
            "decision_hit": False,
            "rule_hit": False,
            "suggestion_hit": False,
            "quote_ok": None,
        }
        matches = [
            f
            for f in findings
            if exp.original_text in (f.get("original_text") or "")
            or (f.get("original_text") or "") in exp.original_text
        ]
        # Prefer exact span matches over substring collisions.
        matches.sort(
            key=lambda f: (
                0 if f.get("original_text") == exp.original_text else 1,
                abs(len(f.get("original_text") or "") - len(exp.original_text)),
            )
        )
        if matches:
            card.span_hits += 1
            detail["span_hit"] = True
            best = matches[0]
            actual_decision = best.get("decision")
            if _decision_match(exp.expected_decision, actual_decision):
                card.decision_hits += 1
                detail["decision_hit"] = True
            actual_rules = set(best.get("rule_ids") or [])
            if exp.expected_rules and actual_rules.intersection(exp.expected_rules):
                card.rule_hits += 1
                detail["rule_hit"] = True
            if (
                exp.suggested_text
                and best.get("suggested_text") == exp.suggested_text
            ):
                card.suggestion_hits += 1
                detail["suggestion_hit"] = True
            if exp.must_not_rewrite:
                card.quote_preserve_total += 1
                suggested = best.get("suggested_text")
                ok = suggested in (None, "", exp.original_text)
                # Also fail if decision is replace with different text
                if (
                    best.get("decision") == "replace"
                    and suggested
                    and suggested != exp.original_text
                ):
                    ok = False
                if ok:
                    card.quote_preserve_ok += 1
                detail["quote_ok"] = ok
        else:
            if exp.must_not_rewrite:
                # Missing quote finding is acceptable for preserve cases
                card.quote_preserve_total += 1
                card.quote_preserve_ok += 1
                detail["quote_ok"] = True
                detail["note"] = "span not flagged — treated as preserve OK"
        card.details.append(detail)
    return card
