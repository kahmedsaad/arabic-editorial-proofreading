"""Precision adjudicator: SHOW / SUPPRESS / NEEDS_CONTEXT / DUPLICATE / MECHANICAL_ONLY."""

from __future__ import annotations

from app.context.article_context import (
    body_has_attribution_nearby,
    quotation_status_for_span,
)
from app.models.schemas import (
    AdjudicationVerdict,
    ArticleContext,
    Decision,
    EditorialHarm,
    Finding,
    FindingSource,
    QuotationStatus,
    RuleApplicability,
    Segment,
    Zone,
)
from app.postprocess.gemini_gate import (
    _inside_quotes,
    _span_overlap,
    confidence_threshold_for_category,
    normalize_category,
)

_SUBJECTIVE = {
    "attribution",
    "attribution_strength",
    "source_quality",
    "quote_voice",
    "loaded_framing",
    "publisher_voice",
}

_VAGUE_SOURCE_MARKERS = ("مصادر", "مصدر مطلع", "أوساط", "جهات")
_SENSITIVE_MARKERS = (
    "قتل",
    "اغتيال",
    "إرهاب",
    "فساد",
    "اتهام",
    "مجزرة",
    "قصف",
    "انتهاك",
)


def _infer_harm(finding: Finding) -> EditorialHarm:
    if finding.editorial_harm_if_ignored is not None:
        return finding.editorial_harm_if_ignored
    cat = (finding.category or "").lower()
    if finding.severity.value in {"critical", "high"}:
        return EditorialHarm.HIGH
    if cat in {
        "numeric_contradiction",
        "temporal_contradiction",
        "headline_body_mismatch",
        "entity_confusion",
        "legal_contradiction",
    }:
        return EditorialHarm.HIGH
    if cat in {"loaded_framing", "publisher_voice", "unsupported_certainty"}:
        return EditorialHarm.MEDIUM
    if cat in {"attribution", "attribution_strength", "source_quality", "quote_voice"}:
        return EditorialHarm.LOW
    return EditorialHarm.LOW


def _infer_applicability(finding: Finding) -> RuleApplicability:
    if finding.rule_applicability is not None:
        return finding.rule_applicability
    if finding.rule_ids:
        return RuleApplicability.CLEAR
    cat = (finding.category or "").lower()
    if cat in _SUBJECTIVE:
        return RuleApplicability.UNCERTAIN
    return RuleApplicability.CLEAR


def _suppress(
    finding: Finding,
    *,
    verdict: AdjudicationVerdict,
    reason: str,
    **fields: object,
) -> Finding:
    update = {
        "adjudication_verdict": verdict,
        "validation_errors": list(finding.validation_errors) + [f"adjudicator:{reason}"],
        **fields,
    }
    return finding.model_copy(update=update)


def _show(
    finding: Finding,
    *,
    verdict: AdjudicationVerdict = AdjudicationVerdict.SHOW,
    **fields: object,
) -> Finding:
    return finding.model_copy(
        update={
            "adjudication_verdict": verdict,
            **fields,
        }
    )


def adjudicate_finding(
    finding: Finding,
    *,
    context: ArticleContext,
    segments_by_id: dict[str, Segment],
    mechanical: list[Finding],
    shown_so_far: list[Finding],
) -> Finding:
    """Return finding with adjudication_verdict set; SUPPRESS* should not interrupt editors."""
    finding = finding.model_copy(
        update={"category": normalize_category(finding.category)}
    )
    segment = segments_by_id.get(finding.segment_id)
    span = (finding.original_text or "").strip()

    q_status = finding.quotation_status
    if q_status is None and segment is not None:
        q_status = quotation_status_for_span(
            context,
            segment_id=finding.segment_id,
            start=finding.start_offset,
            end=finding.end_offset,
        )
    publisher_voice = finding.publisher_voice
    if publisher_voice is None:
        publisher_voice = q_status in {
            QuotationStatus.NOT_QUOTE,
            QuotationStatus.UNCERTAIN,
            None,
        } and not (
            segment
            and _inside_quotes(segment.text, finding.start_offset, finding.end_offset)
        )

    harm = _infer_harm(finding)
    applicability = _infer_applicability(finding)
    resolves = finding.article_context_resolves_issue
    interrupt = finding.would_interrupt_editor

    # Mechanical coverage → MECHANICAL_ONLY
    for prior in mechanical:
        if _span_overlap(prior.original_text, span) >= 0.6:
            return _suppress(
                finding,
                verdict=AdjudicationVerdict.MECHANICAL_ONLY,
                reason="covered_by_mechanical",
                quotation_status=q_status,
                publisher_voice=publisher_voice,
                editorial_harm_if_ignored=harm,
                rule_applicability=applicability,
                would_interrupt_editor=False,
            )

    # Duplicates among already-shown AI findings
    for prior in shown_so_far:
        if _span_overlap(prior.original_text, span) >= 0.75 and (
            prior.category == finding.category
            or {prior.category, finding.category} <= {"attribution", "attribution_strength"}
        ):
            return _suppress(
                finding,
                verdict=AdjudicationVerdict.DUPLICATE,
                reason="duplicate_span",
                quotation_status=q_status,
                publisher_voice=publisher_voice,
                editorial_harm_if_ignored=harm,
                rule_applicability=applicability,
                would_interrupt_editor=False,
            )

    # Explicit silence signals from model / heuristics
    if harm == EditorialHarm.NONE:
        return _suppress(
            finding,
            verdict=AdjudicationVerdict.SUPPRESS,
            reason="harm_none",
            quotation_status=q_status,
            publisher_voice=publisher_voice,
            editorial_harm_if_ignored=harm,
            rule_applicability=applicability,
            would_interrupt_editor=False,
        )
    if applicability == RuleApplicability.NOT_APPLICABLE:
        return _suppress(
            finding,
            verdict=AdjudicationVerdict.SUPPRESS,
            reason="rule_not_applicable",
            quotation_status=q_status,
            publisher_voice=publisher_voice,
            editorial_harm_if_ignored=harm,
            rule_applicability=applicability,
            would_interrupt_editor=False,
        )
    if resolves is True:
        return _suppress(
            finding,
            verdict=AdjudicationVerdict.SUPPRESS,
            reason="context_resolves",
            quotation_status=q_status,
            publisher_voice=publisher_voice,
            editorial_harm_if_ignored=harm,
            rule_applicability=applicability,
            article_context_resolves_issue=True,
            would_interrupt_editor=False,
        )
    if interrupt is False:
        return _suppress(
            finding,
            verdict=AdjudicationVerdict.SUPPRESS,
            reason="would_not_interrupt",
            quotation_status=q_status,
            publisher_voice=publisher_voice,
            editorial_harm_if_ignored=harm,
            rule_applicability=applicability,
            would_interrupt_editor=False,
        )

    # Quotation preservation
    in_direct_quote = q_status in {
        QuotationStatus.DIRECT_QUOTE,
        QuotationStatus.PARTIAL_QUOTE,
    } or (
        segment is not None
        and _inside_quotes(segment.text, finding.start_offset, finding.end_offset)
    )
    if in_direct_quote:
        if finding.decision in {Decision.REPLACE, Decision.BAN}:
            finding = finding.model_copy(
                update={
                    "decision": Decision.NEEDS_EDITOR_REVIEW,
                    "suggested_text": None,
                }
            )
        if finding.suggested_text:
            finding = finding.model_copy(update={"suggested_text": None})
        if finding.category in {"attribution", "quote_voice", "attribution_strength"}:
            return _suppress(
                finding,
                verdict=AdjudicationVerdict.SUPPRESS,
                reason="quote_attribution_nag",
                quotation_status=q_status or QuotationStatus.DIRECT_QUOTE,
                publisher_voice=False,
                editorial_harm_if_ignored=harm,
                rule_applicability=applicability,
                would_interrupt_editor=False,
            )

    # Headline compression: do not nag missing قال when body attributes
    if segment is not None and segment.zone == Zone.HEADLINE:
        cat = finding.category
        if cat in {"attribution", "attribution_strength"}:
            if body_has_attribution_nearby(context, claim_hint=span):
                return _suppress(
                    finding,
                    verdict=AdjudicationVerdict.SUPPRESS,
                    reason="headline_compression_body_attributes",
                    quotation_status=q_status,
                    publisher_voice=publisher_voice,
                    editorial_harm_if_ignored=EditorialHarm.NONE,
                    rule_applicability=applicability,
                    article_context_resolves_issue=True,
                    would_interrupt_editor=False,
                )
        # Do not require complete sentence grammar on headlines
        if cat in {"grammar", "spelling"} and finding.confidence < 0.95:
            return _suppress(
                finding,
                verdict=AdjudicationVerdict.SUPPRESS,
                reason="headline_style_low_value",
                quotation_status=q_status,
                publisher_voice=publisher_voice,
                editorial_harm_if_ignored=EditorialHarm.NONE,
                rule_applicability=applicability,
                would_interrupt_editor=False,
            )

    # Attribution: only when contestable claim in publisher voice without nearby source
    if finding.category in {"attribution", "attribution_strength"}:
        if not publisher_voice and not in_direct_quote:
            # Already attributed / source voice → suppress soft nags
            if finding.confidence < 0.95:
                return _suppress(
                    finding,
                    verdict=AdjudicationVerdict.SUPPRESS,
                    reason="attribution_not_publisher_voice",
                    quotation_status=q_status,
                    publisher_voice=False,
                    editorial_harm_if_ignored=harm,
                    rule_applicability=applicability,
                    would_interrupt_editor=False,
                )
        if body_has_attribution_nearby(context, claim_hint=span) and finding.confidence < 0.93:
            return _suppress(
                finding,
                verdict=AdjudicationVerdict.SUPPRESS,
                reason="attribution_resolved_in_context",
                quotation_status=q_status,
                publisher_voice=publisher_voice,
                editorial_harm_if_ignored=harm,
                rule_applicability=applicability,
                article_context_resolves_issue=True,
                would_interrupt_editor=False,
            )

    # Vague sources: مصادر not automatically wrong
    if finding.category in {"source_quality", "attribution"} and any(
        m in span for m in _VAGUE_SOURCE_MARKERS
    ):
        article_text = " ".join(s.text for s in segments_by_id.values())
        sensitive = any(m in article_text for m in _SENSITIVE_MARKERS) or any(
            m in span for m in _SENSITIVE_MARKERS
        )
        if not sensitive and finding.confidence < 0.95:
            return _suppress(
                finding,
                verdict=AdjudicationVerdict.SUPPRESS,
                reason="vague_source_routine",
                quotation_status=q_status,
                publisher_voice=publisher_voice,
                editorial_harm_if_ignored=EditorialHarm.LOW,
                rule_applicability=applicability,
                would_interrupt_editor=False,
            )

    # Late generic silence for low-harm subjective nags without clear rule
    if applicability == RuleApplicability.UNCERTAIN and finding.category in _SUBJECTIVE:
        if harm in {EditorialHarm.NONE, EditorialHarm.LOW} and finding.confidence < 0.95:
            return _suppress(
                finding,
                verdict=AdjudicationVerdict.SUPPRESS,
                reason="uncertain_subjective",
                quotation_status=q_status,
                publisher_voice=publisher_voice,
                editorial_harm_if_ignored=harm,
                rule_applicability=applicability,
                would_interrupt_editor=False,
            )

    # Category confidence threshold
    thr = confidence_threshold_for_category(finding.category, finding.severity)
    if finding.confidence < thr:
        return _suppress(
            finding,
            verdict=AdjudicationVerdict.SUPPRESS,
            reason=f"confidence_below_{thr}",
            quotation_status=q_status,
            publisher_voice=publisher_voice,
            editorial_harm_if_ignored=harm,
            rule_applicability=applicability,
            would_interrupt_editor=False,
        )

    # Needs context when model is unsure but harm is medium+
    if applicability == RuleApplicability.UNCERTAIN and harm in {
        EditorialHarm.MEDIUM,
        EditorialHarm.HIGH,
    }:
        return _show(
            finding,
            verdict=AdjudicationVerdict.NEEDS_CONTEXT,
            quotation_status=q_status,
            publisher_voice=publisher_voice,
            editorial_harm_if_ignored=harm,
            rule_applicability=applicability,
            would_interrupt_editor=True,
            decision=Decision.NEEDS_EDITOR_REVIEW,
            requires_editor_review=True,
        )

    return _show(
        finding,
        quotation_status=q_status,
        publisher_voice=publisher_voice,
        editorial_harm_if_ignored=harm,
        rule_applicability=applicability,
        article_context_resolves_issue=False if resolves is None else resolves,
        would_interrupt_editor=True if interrupt is None else interrupt,
    )


def adjudicate_findings(
    *,
    findings: list[Finding],
    context: ArticleContext,
    segments: list[Segment],
    mechanical: list[Finding],
) -> tuple[list[Finding], list[Finding]]:
    """Return (show, suppressed). Only SHOW / NEEDS_CONTEXT interrupt editors."""
    by_id = {s.segment_id: s for s in segments}
    shown: list[Finding] = []
    suppressed: list[Finding] = []
    for finding in findings:
        if finding.source not in {FindingSource.GEMINI, FindingSource.MOCK}:
            shown.append(finding)
            continue
        result = adjudicate_finding(
            finding,
            context=context,
            segments_by_id=by_id,
            mechanical=mechanical,
            shown_so_far=shown,
        )
        if result.adjudication_verdict in {
            AdjudicationVerdict.SHOW,
            AdjudicationVerdict.NEEDS_CONTEXT,
        }:
            shown.append(result)
        else:
            suppressed.append(result)
    return shown, suppressed
