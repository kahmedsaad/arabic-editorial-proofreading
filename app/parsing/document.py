from __future__ import annotations

import re
from dataclasses import dataclass

from app.dataset.importer import strip_html
from app.models.schemas import Document
from app.segmentation.article import segment_article


@dataclass
class ParseResult:
    document: Document
    segments: list
    headline: str
    body: str


def split_headline_body(text: str) -> tuple[str, str]:
    cleaned = strip_html(text).strip()
    if not cleaned:
        return "", ""
    lines = [ln.strip() for ln in cleaned.split("\n") if ln.strip()]
    if not lines:
        return "", ""
    headline = lines[0]
    body = "\n".join(lines[1:]).strip()
    # If first line looks like a short title
    if len(headline) > 180 and not body:
        parts = re.split(r"(?<=[.!?؟])\s+", cleaned, maxsplit=1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
    return headline, body


def parse_document_text(
    *,
    text: str = "",
    headline: str = "",
    body: str = "",
    document_id: str = "DOC-PARSE",
    source: str = "manual",
    metadata: dict | None = None,
) -> ParseResult:
    if text and not (headline or body):
        headline, body = split_headline_body(text)
    document = Document(
        document_id=document_id,
        language="ar",
        source=source,
        headline=headline,
        body=body or text,
        metadata=metadata or {},
    )
    # Prefer explicit headline; if body was set to full text accidentally, re-split
    if document.headline and document.body == text and text:
        _, body_only = split_headline_body(text)
        if body_only:
            document.body = body_only
    segments = segment_article(document)
    return ParseResult(
        document=document,
        segments=segments,
        headline=document.headline,
        body=document.body,
    )
