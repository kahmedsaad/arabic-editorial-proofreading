"""Matching utilities for benchmark_v2 scoring."""

from __future__ import annotations

from benchmark_v2.private.scorer.schemas import EngineFinding, ForbiddenFinding, GoldFinding


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def token_set(value: str | None) -> set[str]:
    return {t for t in normalize_text(value).split() if t}


def span_overlap_ratio(a: str | None, b: str | None) -> float:
    sa, sb = token_set(a), token_set(b)
    if not sa or not sb:
        # Fall back to substring containment for short Arabic spans.
        na, nb = normalize_text(a), normalize_text(b)
        if not na or not nb:
            return 0.0
        if na in nb or nb in na:
            return 1.0 if na == nb else 0.6
        return 0.0
    return len(sa & sb) / len(sa | sb)


def exact_span_match(required_any: list[str], original_text: str) -> bool:
    ot = normalize_text(original_text)
    for span in required_any:
        ns = normalize_text(span)
        if ns and (ns == ot or ns in ot or ot in ns):
            # Exact equality or full required span present.
            if ns == ot:
                return True
            if ns in ot and len(ns) >= max(2, int(0.8 * len(ot))):
                return True
            if ot == ns:
                return True
    return any(normalize_text(span) == ot for span in required_any if span)


def partial_span_match(
    required_any: list[str],
    original_text: str,
    *,
    threshold: float = 0.25,
) -> tuple[bool, float]:
    best = 0.0
    ot = original_text or ""
    for span in required_any:
        ratio = span_overlap_ratio(span, ot)
        # Also reward required span as contiguous substring.
        if normalize_text(span) and normalize_text(span) in normalize_text(ot):
            ratio = max(ratio, 0.85)
        if normalize_text(ot) and normalize_text(ot) in normalize_text(span):
            ratio = max(ratio, 0.75)
        best = max(best, ratio)
    return best >= threshold, best


def category_match(gold: GoldFinding, engine: EngineFinding) -> bool:
    return normalize_text(gold.category) == normalize_text(engine.category)


def severity_band_match(gold: GoldFinding, engine: EngineFinding) -> bool:
    if not gold.severity_band:
        return True
    return normalize_text(engine.severity) in {normalize_text(s) for s in gold.severity_band}


def decision_match(gold: GoldFinding, engine: EngineFinding) -> bool:
    if not gold.acceptable_decisions:
        return True
    return normalize_text(engine.decision) in {
        normalize_text(d) for d in gold.acceptable_decisions
    }


def explanation_keyword_match(gold: GoldFinding, engine: EngineFinding) -> bool:
    if not gold.must_explain:
        return True
    expl = normalize_text(engine.explanation_ar)
    if not expl:
        return False
    hits = 0
    for kw in gold.must_explain:
        nk = normalize_text(kw)
        if nk and nk in expl:
            hits += 1
    # At least one required keyword, or half if many.
    need = 1 if len(gold.must_explain) <= 2 else max(1, len(gold.must_explain) // 2)
    return hits >= need


def suggestion_is_safe(gold: GoldFinding, engine: EngineFinding) -> bool:
    """Unsafe if rewrite is required incorrectly, or meaning-changing replace appears."""
    sug = (engine.suggested_text or "").strip()
    orig = (engine.original_text or "").strip()
    decision = normalize_text(engine.decision)

    if gold.suggestion_required:
        if not sug:
            return False
        if normalize_text(sug) == normalize_text(orig):
            return False
        return True

    # Not required: replacing quoted / attributed language is unsafe.
    if decision in {"replace", "ban"} and sug and normalize_text(sug) != normalize_text(orig):
        # Soft allow if suggestion only trims whitespace.
        if normalize_text(sug) == normalize_text(orig):
            return True
        return False
    return True


def score_gold_against_engine(gold: GoldFinding, engine: EngineFinding) -> dict:
    exact = exact_span_match(gold.required_span_any, engine.original_text)
    partial, overlap = partial_span_match(gold.required_span_any, engine.original_text)
    cat = category_match(gold, engine)
    sev = severity_band_match(gold, engine)
    dec = decision_match(gold, engine)
    expl = explanation_keyword_match(gold, engine)
    safe = suggestion_is_safe(gold, engine)

    points = 0.0
    if exact:
        points += 4.0
    elif partial:
        points += 2.0 + min(2.0, overlap * 2.0)
    if cat:
        points += 2.0
    if sev:
        points += 1.0
    if dec:
        points += 1.0
    if expl:
        points += 1.0
    if safe:
        points += 1.0
    else:
        points -= 2.0

    # Minimum gate: need some span signal + (category or decision)
    matched = (exact or partial) and (cat or dec) and points >= 5.0
    return {
        "matched": matched,
        "score": points,
        "exact_span": exact,
        "partial_span": partial and not exact,
        "category_match": cat,
        "severity_band_match": sev,
        "decision_match": dec,
        "explanation_keyword_match": expl,
        "suggestion_safe": safe,
        "overlap": overlap,
    }


def hits_forbidden(forbidden: ForbiddenFinding, engine: EngineFinding) -> bool:
    span = normalize_text(forbidden.span)
    if not span:
        return False
    hay = normalize_text(engine.original_text)
    sug = normalize_text(engine.suggested_text)
    if span in hay or (sug and span in sug):
        if forbidden.decisions:
            return normalize_text(engine.decision) in {
                normalize_text(d) for d in forbidden.decisions
            }
        if forbidden.category:
            return normalize_text(engine.category) == normalize_text(forbidden.category)
        # Any finding covering the forbidden span counts (esp. rewrite).
        if normalize_text(engine.decision) in {"replace", "ban"} and sug:
            return True
        # For clean cases, any finding on the span is a forbidden hit.
        return True
    return False
