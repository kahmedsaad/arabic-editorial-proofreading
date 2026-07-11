from app.models.schemas import Document, Segment, Zone
from app.normalization.arabic import normalize_arabic


def _paragraphs(text: str) -> list[str]:
    if not text:
        return []
    parts = [p.strip() for p in text.replace("\r\n", "\n").split("\n")]
    return [p for p in parts if p]


def segment_article(document: Document) -> list[Segment]:
    """Build stable headline/body segments. Offsets are segment-local (0..len(text))."""
    segments: list[Segment] = []
    sequence = 1

    headline = document.headline.strip()
    if headline:
        segments.append(
            Segment(
                segment_id=f"SEG-{sequence:03d}",
                document_id=document.document_id,
                zone=Zone.HEADLINE,
                text=headline,
                normalized_text=normalize_arabic(headline),
                start_offset=0,
                end_offset=len(headline),
                sequence=sequence,
            )
        )
        sequence += 1

    for paragraph in _paragraphs(document.body):
        segments.append(
            Segment(
                segment_id=f"SEG-{sequence:03d}",
                document_id=document.document_id,
                zone=Zone.BODY,
                text=paragraph,
                normalized_text=normalize_arabic(paragraph),
                start_offset=0,
                end_offset=len(paragraph),
                sequence=sequence,
            )
        )
        sequence += 1

    return segments
