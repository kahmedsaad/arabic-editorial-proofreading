from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class Zone(StrEnum):
    HEADLINE = "headline"
    SUBHEADLINE = "subheadline"
    BODY = "body"
    QUOTE = "quote"
    CAPTION = "caption"
    SOURCE_ATTRIBUTION = "source_attribution"
    UNKNOWN = "unknown"


class FindingSource(StrEnum):
    MECHANICAL = "mechanical"
    GEMINI = "gemini"
    MOCK = "mock"


class Decision(StrEnum):
    ACCEPTABLE = "acceptable"
    SUGGEST = "suggest"
    REPLACE = "replace"
    SOFT_WARNING = "soft_warning"
    HARD_WARNING = "hard_warning"
    BAN = "ban"
    NEEDS_EDITOR_REVIEW = "needs_editor_review"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"


class Document(BaseModel):
    document_id: str
    language: str = "ar"
    source: str = "manual"
    headline: str = ""
    body: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class Segment(BaseModel):
    segment_id: str
    document_id: str
    zone: Zone
    text: str
    normalized_text: str
    start_offset: int
    end_offset: int
    sequence: int


class RuleExample(BaseModel):
    input: str
    preferred: str
    reason: str


class EditorialRule(BaseModel):
    rule_id: str
    version: str = "1.0"
    title_ar: str
    category: str
    rule_type: str = "lexical"
    description_ar: str
    applies_to_zones: list[Zone] = Field(default_factory=list)
    severity: Severity = Severity.MEDIUM
    keywords: list[str] = Field(default_factory=list)
    examples: list[RuleExample] = Field(default_factory=list)
    active: bool = True


class Entity(BaseModel):
    model_config = {"extra": "ignore"}

    entity_id: str
    canonical_ar: str = ""
    aliases: list[str] = Field(default_factory=list)
    category: str = "general"
    active: bool = True
    current_title: str | None = None
    policy_profiles: list[str] = Field(default_factory=list)
    preferred_descriptors: list[str] = Field(default_factory=list)
    discouraged_descriptors: list[str] = Field(default_factory=list)
    version: str = "1.0"
    last_verified: str | None = None

    @model_validator(mode="before")
    @classmethod
    def accept_approved_ar(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("canonical_ar") and data.get("approved_ar"):
                data = {**data, "canonical_ar": data["approved_ar"]}
            if data.get("type") and not data.get("category"):
                data = {**data, "category": data["type"]}
        return data


class Finding(BaseModel):
    finding_id: str
    document_id: str
    segment_id: str
    source: FindingSource
    category: str
    decision: Decision
    severity: Severity
    original_text: str
    suggested_text: str | None = None
    start_offset: int
    end_offset: int
    rule_ids: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    explanation_ar: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    requires_editor_review: bool = False
    validation_status: ValidationStatus = ValidationStatus.PENDING
    validation_errors: list[str] = Field(default_factory=list)


class ReviewStage(BaseModel):
    """Public-safe progressive stage (no prompts / internals)."""

    stage_id: str
    label_ar: str
    status: str = "complete"
    summary: dict[str, Any] = Field(default_factory=dict)


class PipelineLogStep(BaseModel):
    """Admin-only detailed step log (prompts, payloads, raw LLM)."""

    step_id: str
    label: str
    kind: str = "internal"  # mechanical | retrieve | llm | gate | validate | final
    system_prompt: str | None = None
    user_payload: str | None = None
    raw_response: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    started_at: str = ""
    finished_at: str = ""


class ReviewRequest(BaseModel):
    document_id: str | None = None
    language: str = "ar"
    source: str = "manual"
    headline: str = ""
    body: str = ""
    text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParseRequest(BaseModel):
    document_id: str | None = None
    text: str = ""
    headline: str = ""
    body: str = ""
    source: str = "manual"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParseResponse(BaseModel):
    document: Document
    segments: list[Segment]


class ReviewResponse(BaseModel):
    review_id: str
    document: Document
    segments: list[Segment]
    findings: list[Finding]
    rejected_findings: list[Finding] = Field(default_factory=list)
    mechanical_finding_count: int = 0
    ai_finding_count: int = 0
    stages: list[ReviewStage] = Field(default_factory=list)
    retrieved_rules: list[EditorialRule] = Field(default_factory=list)
    retrieved_entities: list[Entity] = Field(default_factory=list)
    candidate_findings: list[Finding] = Field(default_factory=list)
    # Admin-only; stripped from public GET /reviews/{id}
    pipeline_log: list[PipelineLogStep] = Field(default_factory=list)


class EvaluationRunRequest(BaseModel):
    dataset_path: str | None = None


class EvaluationRunResponse(BaseModel):
    run_id: str
    metrics: dict[str, Any]


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str


class PasswordUpdateRequest(BaseModel):
    password: str = Field(min_length=4)


class SystemPromptRecord(BaseModel):
    phase: str
    body: str
    version: int = 1
    updated_at: str = ""


class SystemPromptUpdate(BaseModel):
    body: str


class BulkPasteRequest(BaseModel):
    text: str
    delimiter: str | None = None  # auto: tab or comma


class RuleAuthorRequest(BaseModel):
    text: str
    confirm: bool = False


class RuleAuthorResponse(BaseModel):
    preview: list[EditorialRule]
    saved: list[EditorialRule] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    review_id: str
    finding_id: str
    action: str  # accept | reject | comment
    comment: str | None = None

    @field_validator("action")
    @classmethod
    def valid_action(cls, value: str) -> str:
        allowed = {"accept", "reject", "comment"}
        if value not in allowed:
            raise ValueError(f"action must be one of {allowed}")
        return value
