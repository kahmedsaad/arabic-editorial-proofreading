"""Clean-article / silence FP metrics with editorial vs punctuation split."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

EDITORIAL_REPORT_CATEGORIES = (
    "punctuation",
    "attribution",
    "clarity",
    "headline_mismatch",
    "quote_voice",
    "loaded_framing",
    "entity_consistency",
    "numeric_consistency",
    "temporal_consistency",
)

_CATEGORY_BUCKET: dict[str, str] = {
    "punctuation": "punctuation",
    "attribution": "attribution",
    "attribution_strength": "attribution",
    "source_quality": "attribution",
    "source_misrepresentation": "attribution",
    "clarity": "clarity",
    "headline_body_mismatch": "headline_mismatch",
    "headline_framing": "headline_mismatch",
    "publisher_voice": "headline_mismatch",
    "quote_voice": "quote_voice",
    "loaded_framing": "loaded_framing",
    "entity_name": "entity_consistency",
    "entity_confusion": "entity_consistency",
    "numeric_contradiction": "numeric_consistency",
    "temporal_contradiction": "temporal_consistency",
}


def bucket_category(category: str) -> str:
    return _CATEGORY_BUCKET.get((category or "").lower(), (category or "other").lower())


def is_punctuation(category: str) -> bool:
    return (category or "").lower() == "punctuation"


def compute_clean_fp_metrics(
    *,
    article_finding_categories: Iterable[list[str]],
) -> dict[str, Any]:
    """Compute clean-article FP metrics from per-article category lists.

    Preserves legacy keys where practical and adds split metrics.
    """
    articles = list(article_finding_categories)
    n = len(articles) or 1
    all_counts = [len(cats) for cats in articles]
    punct_counts = [sum(1 for c in cats if is_punctuation(c)) for cats in articles]
    editorial_counts = [a - p for a, p in zip(all_counts, punct_counts)]

    articles_with_any = sum(1 for c in all_counts if c > 0)
    articles_with_editorial = sum(1 for c in editorial_counts if c > 0)
    articles_with_punct = sum(1 for c in punct_counts if c > 0)
    zero_finding = sum(1 for c in all_counts if c == 0)
    zero_editorial = sum(1 for c in editorial_counts if c == 0)

    cat_counter: Counter[str] = Counter()
    bucket_counter: Counter[str] = Counter()
    for cats in articles:
        for c in cats:
            cat_counter[c] += 1
            bucket_counter[bucket_category(c)] += 1

    total_all = sum(all_counts)
    total_editorial = sum(editorial_counts)
    total_punct = sum(punct_counts)

    report_cats = {
        name: {
            "count": bucket_counter.get(name, 0),
            "rate_per_article": round(bucket_counter.get(name, 0) / n, 4),
        }
        for name in EDITORIAL_REPORT_CATEGORIES
    }

    return {
        # Legacy-compatible
        "n_articles": len(articles),
        "articles_with_fp": articles_with_any,
        "clean_article_fp_rate": round(articles_with_any / n, 4),
        "total_findings": total_all,
        "findings_per_article": round(total_all / n, 4),
        "fp_by_category": dict(cat_counter.most_common()),
        # New split metrics
        "clean_fp_rate_all": round(articles_with_any / n, 4),
        "clean_fp_rate_editorial_only": round(articles_with_editorial / n, 4),
        "clean_fp_rate_punctuation_only": round(articles_with_punct / n, 4),
        "findings_per_article_all": round(total_all / n, 4),
        "findings_per_article_editorial_only": round(total_editorial / n, 4),
        "findings_per_article_punctuation_only": round(total_punct / n, 4),
        "zero_finding_clean_article_rate": round(zero_finding / n, 4),
        "zero_editorial_finding_clean_article_rate": round(zero_editorial / n, 4),
        "category_report": report_cats,
        "total_findings_editorial": total_editorial,
        "total_findings_punctuation": total_punct,
    }
