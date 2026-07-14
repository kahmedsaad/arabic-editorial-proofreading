"""Lightweight article context for precision-oriented adjudication."""

from __future__ import annotations

import regex as re

from app.models.schemas import (
    ArticleContext,
    ArticleType,
    AttributionLink,
    Document,
    Entity,
    QuotationSpan,
    QuotationStatus,
    Segment,
    Zone,
)

_QUOTE_OPEN = "«\"“‘'"
_QUOTE_CLOSE = "»\"”’'"
_ATTR_VERBS = (
    "قال",
    "قالت",
    "أكد",
    "أكدت",
    "أعلن",
    "أعلنت",
    "أضاف",
    "أضافت",
    "صرح",
    "صرحت",
    "بحسب",
    "وفقاً",
    "وفقا",
    "نقلاً",
    "نقلا",
    "أفاد",
    "أفادت",
    "نفى",
    "نفت",
    "اتهم",
    "اتهمت",
)


def _guess_article_type(headline: str, body: str) -> ArticleType:
    text = f"{headline}\n{body}"
    if any(k in text for k in ("رأي", "أرى أن", "في رأيي", "عمود")):
        return ArticleType.OPINION
    if any(k in text for k in ("تحليل", "في التحليل", "قراءة في")):
        return ArticleType.ANALYSIS
    if any(k in text for k in ("مباشر", "لحظة بلحظة", "تحديث:", "عاجل")):
        return ArticleType.LIVE_UPDATE
    if any(k in text for k in ("ما هو", "كيف", "شرح", "دليل")):
        return ArticleType.EXPLAINER
    if any(k in text for k in ("عاجل", "الآن", "قصف", "انفجار")) or len(body) < 400:
        if "عاجل" in headline or "الآن" in headline:
            return ArticleType.BREAKING_NEWS
    return ArticleType.NEWS_REPORT


def _extract_quote_spans(segments: list[Segment]) -> list[QuotationSpan]:
    spans: list[QuotationSpan] = []
    for segment in segments:
        text = segment.text
        i = 0
        while i < len(text):
            if text[i] in _QUOTE_OPEN:
                open_ch = text[i]
                close_ch = {
                    "«": "»",
                    '"': '"',
                    "“": "”",
                    "‘": "’",
                    "'": "'",
                }.get(open_ch, "»")
                j = text.find(close_ch, i + 1)
                if j < 0:
                    spans.append(
                        QuotationSpan(
                            segment_id=segment.segment_id,
                            start_offset=i,
                            end_offset=len(text),
                            text=text[i:],
                            status=QuotationStatus.UNCERTAIN,
                        )
                    )
                    break
                spans.append(
                    QuotationSpan(
                        segment_id=segment.segment_id,
                        start_offset=i,
                        end_offset=j + 1,
                        text=text[i : j + 1],
                        status=QuotationStatus.DIRECT_QUOTE,
                    )
                )
                i = j + 1
                continue
            i += 1
        # Indirect reported speech cues
        if any(v in text for v in ("قال إن", "قالت إن", "أعلن أن", "أكد أن")):
            spans.append(
                QuotationSpan(
                    segment_id=segment.segment_id,
                    start_offset=0,
                    end_offset=min(len(text), 40),
                    text=text[: min(len(text), 40)],
                    status=QuotationStatus.INDIRECT_SPEECH,
                )
            )
    return spans


def _extract_speakers(segments: list[Segment]) -> list[str]:
    speakers: list[str] = []
    seen: set[str] = set()
    pattern = re.compile(
        r"(?:قال|قالت|أكد|أكدت|أعلن|أعلنت|صرّح|صرح|صرحت)\s+([^،\.«»\"]{2,40})"
    )
    for segment in segments:
        for match in pattern.finditer(segment.text):
            name = match.group(1).strip()
            name = re.sub(r"^(إن|أن|إنه|إنها)\s+", "", name).strip()
            if name and name not in seen and len(name) >= 2:
                seen.add(name)
                speakers.append(name)
    return speakers[:20]


def _attribution_links(segments: list[Segment]) -> list[AttributionLink]:
    links: list[AttributionLink] = []
    for segment in segments:
        text = segment.text
        for verb in _ATTR_VERBS:
            idx = text.find(verb)
            if idx < 0:
                continue
            window = text[max(0, idx - 40) : min(len(text), idx + 80)]
            links.append(
                AttributionLink(
                    claim_span=window.strip()[:120],
                    speaker=None,
                    attribution_verb=verb,
                    source_org=None,
                    segment_id=segment.segment_id,
                )
            )
    return links[:40]


def _terminology(segments: list[Segment], entities: list[Entity]) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for entity in entities:
        for form in [entity.canonical_ar, *entity.aliases]:
            form = (form or "").strip()
            if form and form not in seen:
                seen.add(form)
                terms.append(form)
    # Light lexical harvest from headline
    for segment in segments:
        if segment.zone == Zone.HEADLINE:
            for token in re.findall(r"[\u0600-\u06FF]{3,}", segment.text):
                if token not in seen:
                    seen.add(token)
                    terms.append(token)
    return terms[:40]


def quotation_status_for_span(
    context: ArticleContext,
    *,
    segment_id: str,
    start: int,
    end: int,
) -> QuotationStatus:
    for q in context.quotation_spans:
        if q.segment_id != segment_id:
            continue
        if start >= q.start_offset and end <= q.end_offset:
            return q.status
        # Overlap
        if start < q.end_offset and end > q.start_offset:
            if q.status == QuotationStatus.DIRECT_QUOTE:
                return QuotationStatus.PARTIAL_QUOTE
            return q.status
    for q in context.quotation_spans:
        if q.segment_id == segment_id and q.status == QuotationStatus.INDIRECT_SPEECH:
            return QuotationStatus.INDIRECT_SPEECH
    return QuotationStatus.NOT_QUOTE


def body_has_attribution_nearby(
    context: ArticleContext,
    *,
    claim_hint: str | None = None,
) -> bool:
    if not context.attribution_links:
        return False
    if not claim_hint:
        return any(link.segment_id for link in context.attribution_links)
    hint = claim_hint.strip()[:20]
    for link in context.attribution_links:
        if hint and hint in (link.claim_span or ""):
            return True
        if link.attribution_verb:
            return True
    return bool(context.attribution_links)


def extract_article_context(
    document: Document,
    segments: list[Segment],
    entities: list[Entity] | None = None,
) -> ArticleContext:
    entities = entities or []
    headline_ids = [s.segment_id for s in segments if s.zone == Zone.HEADLINE]
    body_ids = [s.segment_id for s in segments if s.zone == Zone.BODY]
    quotes = _extract_quote_spans(segments)
    numbers = re.findall(
        r"\d+[%٪]?|\d+\s*(?:مليون|ألف|مليار)",
        f"{document.headline}\n{document.body}",
    )
    dates = re.findall(
        r"\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{2,4}|"
        r"(?:الأحد|الإثنين|الثلاثاء|الأربعاء|الخميس|الجمعة|السبت)|"
        r"(?:يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)",
        f"{document.headline}\n{document.body}",
    )
    central = (document.headline or "").strip() or (
        segments[0].text[:120] if segments else ""
    )
    return ArticleContext(
        article_type=_guess_article_type(document.headline, document.body),
        headline_segment_ids=headline_ids,
        body_segment_ids=body_ids,
        quotation_spans=quotes,
        speakers=_extract_speakers(segments),
        entity_ids=[e.entity_id for e in entities],
        dates=list(dict.fromkeys(dates))[:20],
        numbers=list(dict.fromkeys(numbers))[:20],
        locations=[],
        central_claim=central,
        terminology_used=_terminology(segments, entities),
        attribution_links=_attribution_links(segments),
    )
