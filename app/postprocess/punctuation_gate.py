"""Gate punctuation findings before final aggregation (run4 precision)."""

from __future__ import annotations

import re
from typing import Any

from app.models.schemas import Finding, FindingSource, Segment, Zone
from app.postprocess.punctuation_policy import (
    PunctuationPolicy,
    RULE_ID_TO_SUBTYPE,
    STRICT_ALLOWED_SUBTYPES,
    normalize_policy,
    threshold_for_subtype,
)

_QUOTE_CHARS = "«»\"“”‘’'"
_REPEATED_PUNCT_RE = re.compile(r"^([.,:;!?،؛؟])\1+$")
_STRUCTURAL_SUBTYPES = frozenset(
    {
        "repeated_punctuation",
        "unbalanced_quotes",
        "unbalanced_parentheses",
        "unbalanced_brackets",
        "broken_sentence_boundary",
    }
)


def classify_punctuation_subtype(
    finding: Finding,
    *,
    segment_text: str = "",
    zone: Zone | None = None,
) -> str:
    """Normalize / infer punctuation subtype for a finding."""
    existing = getattr(finding, "punctuation_subtype", None)
    if existing:
        return str(existing)

    for rid in finding.rule_ids or []:
        if rid in RULE_ID_TO_SUBTYPE:
            return RULE_ID_TO_SUBTYPE[rid]

    original = (finding.original_text or "").strip()
    if _REPEATED_PUNCT_RE.match(original) or "،،" in original or ".." in original:
        return "repeated_punctuation"

    explanation = (finding.explanation_ar or "").lower()
    if any(k in explanation for k in ("اقتباس", "quote", "علامة فتح", "علامة إغلاق")):
        return "unbalanced_quotes"
    if "قوس" in explanation or "parenthes" in explanation:
        return "unbalanced_parentheses"
    if "قوس مربع" in explanation or "bracket" in explanation:
        return "unbalanced_brackets"

    if zone in {Zone.HEADLINE, Zone.SUBHEADLINE}:
        # Non-structural headline punctuation is style.
        return "headline_style"

    if original in {"،", ","} or (finding.suggested_text or "").strip() in {"،", ","}:
        return "optional_comma"
    if original in {".", "۔"} or (finding.suggested_text or "").endswith(". "):
        # Missing space after period / optional period style.
        if "مسافة" in (finding.explanation_ar or "") or "تنقص" in (finding.explanation_ar or ""):
            return "malformed_spacing"
        return "optional_period"

    if "مسافة" in (finding.explanation_ar or "") or "مسافات" in (finding.explanation_ar or ""):
        return "malformed_spacing"

    return "other"


def _inside_quotes(text: str, start: int, end: int) -> bool:
    before = text[: max(0, start)]
    toggles = sum(1 for ch in before if ch in _QUOTE_CHARS)
    if toggles % 2 == 1:
        return True
    left = max((before.rfind(ch) for ch in "«\"“‘"), default=-1)
    if left < 0:
        return False
    after = text[end:]
    return any(ch in after for ch in "»\"”’")


def _is_objectively_malformed_spacing(finding: Finding) -> bool:
    """Very high bar: only extreme / corruption-like spacing defects."""
    original = finding.original_text or ""
    # 4+ consecutive spaces (or blank runs with tabs) — parse corruption signal.
    if re.search(r"[^\S\n]{4,}", original):
        return True
    if "\n\n\n" in original:
        return True
    return False


def _quote_rewrite_risk(finding: Finding, segment_text: str) -> bool:
    """True if suggestion would rewrite interior of a quoted span."""
    if finding.suggested_text is None:
        return False
    if not _inside_quotes(segment_text, finding.start_offset, finding.end_offset):
        return False
    # Structural delimiter fixes on the quote marks themselves are ok.
    if finding.punctuation_subtype in {
        "unbalanced_quotes",
        "unbalanced_parentheses",
        "unbalanced_brackets",
    }:
        return False
    return True


def should_show_punctuation_finding(
    finding: Finding,
    *,
    policy: PunctuationPolicy,
    segment_text: str,
    article_type: str | None = None,
    zone: Zone | None = None,
) -> tuple[bool, str]:
    """
    Returns:
        (show, reason_code)
    """
    _ = article_type  # reserved for future article-type nuance
    policy = normalize_policy(policy)

    if (finding.category or "").lower() != "punctuation":
        return True, "not_punctuation"

    if policy == "off":
        return False, "suppressed_policy_off"

    subtype = classify_punctuation_subtype(
        finding, segment_text=segment_text, zone=zone
    )
    finding.punctuation_subtype = subtype

    if policy == "full":
        return True, "allowed_full_policy"

    # --- strict ---
    if zone in {Zone.HEADLINE, Zone.SUBHEADLINE}:
        if subtype not in _STRUCTURAL_SUBTYPES:
            return False, "suppressed_headline_style"
        # Still require structural allow-list.
        if subtype not in STRICT_ALLOWED_SUBTYPES and subtype != "malformed_spacing":
            return False, "suppressed_headline_style"

    inside_quote = _inside_quotes(segment_text, finding.start_offset, finding.end_offset)
    if inside_quote and subtype not in _STRUCTURAL_SUBTYPES:
        finding.punctuation_subtype = "quote_internal_style"
        return False, "suppressed_inside_quote"
    if inside_quote and _quote_rewrite_risk(finding, segment_text):
        # Never hard-replace quoted content for style.
        finding.suggested_text = None
        if finding.decision.value in {"replace", "suggest"}:
            return False, "suppressed_inside_quote"

    if subtype in {"optional_comma", "optional_period", "headline_style", "quote_internal_style"}:
        return False, "suppressed_optional_style"

    if subtype == "other":
        return False, "suppressed_unknown_subtype"

    if subtype == "malformed_spacing":
        if finding.confidence < threshold_for_subtype(subtype):
            return False, "suppressed_low_confidence"
        if not _is_objectively_malformed_spacing(finding):
            return False, "suppressed_optional_style"
        return True, "allowed_objective_error"

    if subtype not in STRICT_ALLOWED_SUBTYPES:
        return False, "suppressed_unknown_subtype"

    if finding.confidence < threshold_for_subtype(subtype):
        return False, "suppressed_low_confidence"

    return True, "allowed_objective_error"


def dedupe_punctuation_findings(
    findings: list[Finding],
) -> tuple[list[Finding], list[dict[str, Any]]]:
    """Dedupe punctuation by article/segment/offsets/subtype; prefer deterministic."""
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    kept: list[Finding] = []
    audit: list[dict[str, Any]] = []
    best: dict[tuple[str, str, int, int, str], Finding] = {}
    order: list[tuple[str, str, int, int, str]] = []

    non_punct: list[Finding] = []
    for finding in findings:
        if (finding.category or "").lower() != "punctuation":
            non_punct.append(finding)
            continue
        subtype = finding.punctuation_subtype or classify_punctuation_subtype(finding)
        finding.punctuation_subtype = subtype
        key = (
            finding.document_id,
            finding.segment_id,
            finding.start_offset,
            finding.end_offset,
            subtype,
        )
        if key not in best:
            best[key] = finding
            order.append(key)
            continue
        current = best[key]
        # Prefer mechanical/deterministic over Gemini/mock.
        curr_mech = current.source == FindingSource.MECHANICAL
        new_mech = finding.source == FindingSource.MECHANICAL
        prefer_new = False
        if new_mech and not curr_mech:
            prefer_new = True
        elif curr_mech and not new_mech:
            prefer_new = False
        else:
            # Both objective: keep higher severity.
            if severity_rank.get(finding.severity.value, 0) > severity_rank.get(
                current.severity.value, 0
            ):
                prefer_new = True
        dropped = current if prefer_new else finding
        winner = finding if prefer_new else current
        if prefer_new:
            best[key] = finding
        audit.append(
            {
                "reason": "suppressed_duplicate",
                "kept_finding_id": winner.finding_id,
                "dropped_finding_id": dropped.finding_id,
                "key": {
                    "document_id": key[0],
                    "segment_id": key[1],
                    "start_offset": key[2],
                    "end_offset": key[3],
                    "subtype": key[4],
                },
                "preferred_source": winner.source.value,
            }
        )

    for key in order:
        kept.append(best[key])
    return [*non_punct, *kept], audit


def gate_punctuation_findings(
    findings: list[Finding],
    *,
    policy: PunctuationPolicy | str,
    segments: list[Segment] | None = None,
    article_type: str | None = None,
) -> tuple[list[Finding], list[Finding], list[dict[str, Any]]]:
    """Filter + dedupe punctuation findings.

    Returns:
        (kept, suppressed, audit_events)
    """
    policy = normalize_policy(str(policy))
    by_seg = {s.segment_id: s for s in (segments or [])}
    kept: list[Finding] = []
    suppressed: list[Finding] = []
    audit: list[dict[str, Any]] = []

    for finding in findings:
        if (finding.category or "").lower() != "punctuation":
            kept.append(finding)
            continue
        seg = by_seg.get(finding.segment_id)
        segment_text = seg.text if seg else ""
        zone = seg.zone if seg else None
        show, reason = should_show_punctuation_finding(
            finding,
            policy=policy,
            segment_text=segment_text,
            article_type=article_type,
            zone=zone,
        )
        if show:
            kept.append(finding)
            audit.append(
                {
                    "finding_id": finding.finding_id,
                    "action": "show",
                    "reason_code": reason,
                    "subtype": finding.punctuation_subtype,
                }
            )
        else:
            finding.validation_errors = [
                *(finding.validation_errors or []),
                f"punctuation_gate:{reason}",
            ]
            suppressed.append(finding)
            audit.append(
                {
                    "finding_id": finding.finding_id,
                    "action": "suppress",
                    "reason_code": reason,
                    "subtype": finding.punctuation_subtype,
                }
            )

    kept, dedupe_audit = dedupe_punctuation_findings(kept)
    audit.extend(dedupe_audit)
    # Dedupe may have dropped some punctuation still in kept list handling —
    # drop ids recorded only in audit as suppressed_duplicate.
    dropped_ids = {a["dropped_finding_id"] for a in dedupe_audit if "dropped_finding_id" in a}
    if dropped_ids:
        still = []
        for f in kept:
            if f.finding_id in dropped_ids and (f.category or "").lower() == "punctuation":
                suppressed.append(f)
            else:
                still.append(f)
        kept = still

    return kept, suppressed, audit
