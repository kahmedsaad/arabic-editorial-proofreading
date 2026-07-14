"""Pydantic models for POC datasets.

NOTE: External / public news corpora are not Al Jazeera editorial policy.
Synthetic records must keep source_type=synthetic_mutation (or similar).
AI-generated labels must not be marked editor_approved unless human-reviewed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class BaseDatasetRecord(BaseModel):
    record_id: str
    language: str = "ar"
    source_type: str
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CleanArticleRecord(BaseDatasetRecord):
    """Clean published/licensed news — expected silence (or near-silence)."""

    source_type: str = "external_public"
    headline: str = ""
    body: str = ""
    expected_findings: list[Any] = Field(default_factory=list)
    reason: str = "acceptable_published_copy"
    # Legal / provenance — never claim AJ house style
    license: str | None = None
    notes: str = "Not Al Jazeera house-style data"


class SyntheticIssueRecord(BaseDatasetRecord):
    """Controlled mutation of a clean article for regression / deterministic gold."""

    source_type: str = "synthetic_mutation"
    original_text: str
    mutated_text: str
    segment_id: str = ""
    issue_span: str
    issue_category: str
    severity: str = "major"
    expected_action: Literal["show", "suppress"] = "show"
    acceptable_suggestions: list[str] = Field(default_factory=list)
    must_preserve_quote: bool = False
    headline: str = ""
    body: str = ""


class EditorFeedbackRecord(BaseDatasetRecord):
    """Editor keep/drop adjudication — highest-value precision data."""

    source_type: str = "editor_feedback"
    article_id: str
    finding_id: str
    decision: Literal["keep", "drop", "modify"]
    category: str | None = None
    severity: str | None = None
    reason: str | None = None
    drop_reason: str | None = None
    suggestion_safe: bool | None = None
    quote_preserved: bool | None = None
    annotator_role: str | None = None


class BeforeAfterRecord(BaseDatasetRecord):
    """Real editorial before/after pair (prefer AJ-approved package; store in GCS private/)."""

    source_type: str = "before_after"
    before_text: str
    after_text: str
    changed_span: str | None = None
    editorial_reason: str | None = None
    change_required: bool | None = None
    applicable_rule: str | None = None
    is_quoted: bool | None = None
    headline_before: str = ""
    headline_after: str = ""


class DatasetManifest(BaseModel):
    dataset_id: str
    name: str
    version: str = "1.0.0"
    storage_path: str
    format: str = "jsonl"
    language: str = "ar"
    record_count: int = 0
    size_bytes: int = 0
    license: str = "documented-separately"
    source_type: str = "external_public"
    contains_full_text: bool = True
    contains_personal_data: bool = False
    contains_private_gold: bool = False
    created_at: datetime | None = None
    checksum_sha256: str = ""
    notes: str = "Not Al Jazeera house-style data"
