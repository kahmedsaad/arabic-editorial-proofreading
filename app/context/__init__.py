"""Context package exports."""

from app.context.article_context import (
    body_has_attribution_nearby,
    extract_article_context,
    quotation_status_for_span,
)

__all__ = [
    "body_has_attribution_nearby",
    "extract_article_context",
    "quotation_status_for_span",
]
