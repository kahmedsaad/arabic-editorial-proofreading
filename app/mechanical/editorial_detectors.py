"""Deterministic editorial detectors driven by house phrase lexicons."""

from __future__ import annotations

import json
from pathlib import Path

from app.models.schemas import Decision, Finding, FindingSource, Segment, Severity, Zone

_QUOTE_CHARS = "\"'«»“”‘’"


def _inside_quotes(text: str, start: int, end: int) -> bool:
    """Heuristic: odd count of opening-style quotes before span => inside quotes."""
    before = text[:start]
    # Count paired Arabic/English quote chars; treat « ” “ ' " as toggles.
    toggles = 0
    for ch in before:
        if ch in _QUOTE_CHARS:
            toggles += 1
    if toggles % 2 == 1:
        return True
    # Also true if nearest left quote is opener and right closer wraps the span.
    left = max((before.rfind(ch) for ch in "«\"“‘"), default=-1)
    if left < 0:
        return False
    after = text[end:]
    right_pos = min(
        (i for i, ch in enumerate(after) if ch in "»\"”’"),
        default=-1,
    )
    return right_pos >= 0


def load_editorial_phrases(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _decision(value: str) -> Decision:
    try:
        return Decision(value)
    except ValueError:
        return Decision.NEEDS_EDITOR_REVIEW


def _severity(value: str) -> Severity:
    try:
        return Severity(value)
    except ValueError:
        return Severity.MEDIUM


def _zone_ok(segment: Segment, prefer_zones: list[str] | None) -> bool:
    if not prefer_zones:
        return True
    return segment.zone.value in prefer_zones or segment.zone == Zone.UNKNOWN


def _emit(
    *,
    counter: list[int],
    segment: Segment,
    entry: dict,
    start: int,
    end: int,
) -> Finding:
    counter[0] += 1
    return Finding(
        finding_id=f"FND-E-{counter[0]:04d}",
        document_id=segment.document_id,
        segment_id=segment.segment_id,
        source=FindingSource.MECHANICAL,
        category=str(entry.get("category") or "loaded_framing"),
        decision=_decision(str(entry.get("decision") or "needs_editor_review")),
        severity=_severity(str(entry.get("severity") or "medium")),
        original_text=segment.text[start:end],
        suggested_text=entry.get("suggested_text"),
        start_offset=start,
        end_offset=end,
        rule_ids=list(entry.get("rule_ids") or []),
        explanation_ar=str(entry.get("explanation_ar") or "مراجعة تحريرية مقترحة."),
        confidence=0.95,
        requires_editor_review=bool(entry.get("requires_editor_review", True)),
    )


def _overlaps(claimed: set[tuple[str, int, int]], segment_id: str, start: int, end: int) -> bool:
    for sid, c_start, c_end in claimed:
        if sid != segment_id:
            continue
        if start < c_end and end > c_start:
            return True
    return False


def _scan_bucket(
    *,
    segments: list[Segment],
    entries: list[dict],
    counter: list[int],
    require_quote: bool | None = None,
    claimed: set[tuple[str, int, int]] | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    # Longer spans first to avoid partial overlaps within the same bucket.
    ordered = sorted(entries, key=lambda e: len(str(e.get("span") or "")), reverse=True)
    claimed = claimed if claimed is not None else set()

    for entry in ordered:
        span = str(entry.get("span") or "").strip()
        if not span:
            continue
        prefer_zones = entry.get("prefer_zones")
        must_quote = entry.get("must_be_quoted")
        if require_quote is True and not must_quote:
            continue
        if require_quote is False and must_quote:
            continue

        for segment in segments:
            if not _zone_ok(segment, prefer_zones):
                continue
            start = 0
            while True:
                idx = segment.text.find(span, start)
                if idx < 0:
                    break
                end = idx + len(span)
                start = end
                if _overlaps(claimed, segment.segment_id, idx, end):
                    continue
                if must_quote:
                    window = segment.text[max(0, idx - 2) : min(len(segment.text), end + 2)]
                    if not any(ch in window for ch in _QUOTE_CHARS):
                        continue
                if entry.get("skip_if_quoted") and _inside_quotes(segment.text, idx, end):
                    continue
                claimed.add((segment.segment_id, idx, end))
                findings.append(
                    _emit(counter=counter, segment=segment, entry=entry, start=idx, end=end)
                )
    return findings


def run_editorial_detectors(
    segments: list[Segment],
    lexicon: dict | None = None,
    *,
    grammar_lexicon: dict | None = None,
    counter_start: int = 0,
) -> list[Finding]:
    """Emit deterministic editorial findings from phrase lexicons."""
    data = lexicon or {}
    counter = [counter_start]
    findings: list[Finding] = []
    claimed: set[tuple[str, int, int]] = set()

    grammar_entries = list((grammar_lexicon or {}).get("patterns") or [])
    if grammar_entries:
        findings.extend(
            _scan_bucket(
                segments=segments,
                entries=grammar_entries,
                counter=counter,
                claimed=claimed,
            )
        )

    for key in (
        "quote_preserve",
        "evidence_gaps",
        "overgeneralizations",
        "vague_sources",
        "loaded_caption_phrases",
        "nonstate_descriptors",
        "confirmation_verbs",
        "coup_inference",
    ):
        findings.extend(
            _scan_bucket(
                segments=segments,
                entries=list(data.get(key) or []),
                counter=counter,
                claimed=claimed,
            )
        )
    return findings


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    """Keep one finding per segment+span; prefer harder decisions and more rules."""
    decision_rank = {
        Decision.BAN: 6,
        Decision.HARD_WARNING: 5,
        Decision.NEEDS_EDITOR_REVIEW: 4,
        Decision.SOFT_WARNING: 3,
        Decision.REPLACE: 2,
        Decision.SUGGEST: 1,
        Decision.ACCEPTABLE: 0,
    }
    best: dict[tuple[str, str], Finding] = {}
    order: list[tuple[str, str]] = []

    for finding in findings:
        key = (finding.segment_id, finding.original_text.strip())
        if key not in best:
            best[key] = finding
            order.append(key)
            continue
        current = best[key]
        # Never let model echoes replace deterministic editorial detectors.
        if current.finding_id.startswith("FND-E") and finding.source == FindingSource.GEMINI:
            continue
        if finding.finding_id.startswith("FND-E") and current.source == FindingSource.GEMINI:
            best[key] = finding
            continue
        curr_score = (
            decision_rank.get(current.decision, 0),
            len(current.rule_ids),
            current.confidence,
        )
        new_score = (
            decision_rank.get(finding.decision, 0),
            len(finding.rule_ids),
            finding.confidence,
        )
        if new_score > curr_score:
            best[key] = finding
        elif new_score == curr_score and finding.finding_id.startswith("FND-E"):
            best[key] = finding

    return [best[k] for k in order]
