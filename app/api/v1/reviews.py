from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import (
    get_entity_repo,
    get_orchestrator,
    get_rule_repo,
    get_store,
    require_admin,
    require_user,
)
from app.config import ROOT_DIR, settings
from app.evaluation.metrics import metrics_to_dict, run_evaluation
from app.models.schemas import (
    BulkPasteRequest,
    EditorialRule,
    Entity,
    EvaluationRunRequest,
    EvaluationRunResponse,
    FeedbackRequest,
    LoginRequest,
    LoginResponse,
    PasswordUpdateRequest,
    ParseRequest,
    ParseResponse,
    ReviewRequest,
    ReviewResponse,
    RuleAuthorRequest,
    RuleAuthorResponse,
    SystemPromptRecord,
    SystemPromptUpdate,
)
from app.parsing.document import parse_document_text
from app.parsing.docx_intake import extract_text_from_upload
from app.rules.bulk import bump_version, parse_entities_paste, parse_rules_paste

router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "arabic-editorial-proofreading",
        "ai_client": settings.ai_client,
        "use_gcp": settings.use_gcp,
        "auth_required": settings.demo_auth_required,
        "phase7_ready": False,
    }


# ---- auth -----------------------------------------------------------------


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    result = get_store().login(request.username, request.password)
    if not result:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return LoginResponse(**result)


@router.post("/auth/logout")
async def logout(session: dict = Depends(require_user)) -> dict[str, str]:  # noqa: B008
    token = session.get("token")
    if token:
        get_store().logout(token)
    return {"status": "ok"}


@router.get("/auth/me")
async def me(session: dict = Depends(require_user)) -> dict[str, str]:  # noqa: B008
    return {
        "username": session.get("username", ""),
        "role": session.get("role", "user"),
    }


@router.post("/admin/public-password")
async def set_public_password(
    body: PasswordUpdateRequest,
    session: dict = Depends(require_admin),  # noqa: B008
) -> dict[str, str]:
    del session
    get_store().set_public_password(body.password)
    return {"status": "ok"}


# ---- prompts (admin only; never expose to public clients via UI) ----------


@router.get("/admin/prompts", response_model=list[SystemPromptRecord])
async def list_prompts(session: dict = Depends(require_admin)) -> list[SystemPromptRecord]:  # noqa: B008
    del session
    return [SystemPromptRecord(**row) for row in get_store().list_prompts()]


@router.put("/admin/prompts/{phase}", response_model=SystemPromptRecord)
async def update_prompt(
    phase: str,
    body: SystemPromptUpdate,
    session: dict = Depends(require_admin),  # noqa: B008
) -> SystemPromptRecord:
    del session
    if phase not in get_store().PROMPT_PHASES:
        raise HTTPException(status_code=400, detail=f"unknown phase: {phase}")
    saved = get_store().set_prompt(phase, body.body, bump_version=True)
    get_orchestrator.cache_clear()
    return SystemPromptRecord(**saved)


# ---- documents / reviews --------------------------------------------------


@router.post("/documents/parse", response_model=ParseResponse)
async def parse_document(
    request: ParseRequest,
    session: dict = Depends(require_user),  # noqa: B008
) -> ParseResponse:
    del session
    parsed = parse_document_text(
        text=request.text,
        headline=request.headline,
        body=request.body,
        document_id=request.document_id or f"DOC-{uuid4().hex[:8].upper()}",
        source=request.source,
        metadata=request.metadata,
    )
    return ParseResponse(document=parsed.document, segments=parsed.segments)


@router.post("/documents/upload", response_model=ParseResponse)
async def upload_document(
    file: UploadFile = File(...),  # noqa: B008
    session: dict = Depends(require_user),  # noqa: B008
) -> ParseResponse:
    del session
    data = await file.read()
    filename = file.filename or "upload.txt"
    try:
        text = extract_text_from_upload(filename, data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"failed to read upload: {exc}") from exc
    parsed = parse_document_text(
        text=text,
        document_id=f"DOC-{uuid4().hex[:8].upper()}",
        source="upload",
        metadata={"filename": filename},
    )
    return ParseResponse(document=parsed.document, segments=parsed.segments)


@router.post("/reviews", response_model=ReviewResponse)
async def create_review(
    request: ReviewRequest,
    session: dict = Depends(require_user),  # noqa: B008
) -> ReviewResponse:
    review = await get_orchestrator().review(request)
    get_store().save_review(review)
    if session.get("role") != "admin":
        return review.model_copy(update={"pipeline_log": [], "rejected_findings": []})
    return review


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: str,
    session: dict = Depends(require_user),  # noqa: B008
) -> ReviewResponse:
    del session
    review = get_store().get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="review not found")
    # Editor view: hide rejected internals and admin pipeline log
    return review.model_copy(update={"rejected_findings": [], "pipeline_log": []})


@router.get("/reviews/{review_id}/debug", response_model=ReviewResponse)
async def get_review_debug(
    review_id: str,
    session: dict = Depends(require_admin),  # noqa: B008
) -> ReviewResponse:
    del session
    review = get_store().get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="review not found")
    return review


@router.get("/admin/pipeline-logs")
async def list_pipeline_logs(
    session: dict = Depends(require_admin),  # noqa: B008
) -> list[dict]:
    del session
    return get_store().list_pipeline_logs()


@router.get("/admin/pipeline-logs/{review_id}")
async def get_pipeline_log(
    review_id: str,
    session: dict = Depends(require_admin),  # noqa: B008
) -> dict:
    del session
    log = get_store().get_pipeline_log(review_id)
    if not log:
        review = get_store().get_review(review_id)
        if review and review.pipeline_log:
            return {
                "review_id": review_id,
                "document_id": review.document.document_id,
                "steps": [s.model_dump(mode="json") for s in review.pipeline_log],
                "updated_at": "",
                "created_at": "",
            }
        raise HTTPException(status_code=404, detail="pipeline log not found")
    return log


@router.post("/reviews/feedback")
async def save_feedback(
    body: FeedbackRequest,
    session: dict = Depends(require_user),  # noqa: B008
) -> dict[str, str]:
    get_store().save_feedback(
        review_id=body.review_id,
        finding_id=body.finding_id,
        action=body.action,
        comment=body.comment,
        actor=session.get("username", "user"),
    )
    return {"status": "ok"}


# ---- rules ----------------------------------------------------------------


@router.get("/rules", response_model=list[EditorialRule])
async def list_rules(session: dict = Depends(require_user)) -> list[EditorialRule]:  # noqa: B008
    del session
    return get_rule_repo().list_rules(active_only=False)


@router.get("/rules/{rule_id}", response_model=EditorialRule)
async def get_rule(
    rule_id: str,
    session: dict = Depends(require_user),  # noqa: B008
) -> EditorialRule:
    del session
    rule = get_rule_repo().get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    return rule


@router.post("/rules", response_model=EditorialRule)
async def create_rule(
    rule: EditorialRule,
    session: dict = Depends(require_user),  # noqa: B008
) -> EditorialRule:
    del session
    existing = get_rule_repo().get(rule.rule_id)
    if existing:
        get_store().archive_rule(
            existing.rule_id, existing.version, existing.model_dump(mode="json")
        )
        rule = rule.model_copy(update={"version": bump_version(existing.version)})
    saved = get_rule_repo().upsert(rule)
    get_store().archive_rule(saved.rule_id, saved.version, saved.model_dump(mode="json"))
    get_rule_repo.cache_clear()
    get_orchestrator.cache_clear()
    return saved


@router.post("/rules/bulk", response_model=list[EditorialRule])
async def bulk_rules(
    body: BulkPasteRequest,
    session: dict = Depends(require_user),  # noqa: B008
) -> list[EditorialRule]:
    del session
    parsed = parse_rules_paste(body.text, body.delimiter)
    if not parsed:
        raise HTTPException(status_code=400, detail="no rules parsed from paste")
    saved: list[EditorialRule] = []
    for rule in parsed:
        existing = get_rule_repo().get(rule.rule_id)
        if existing:
            get_store().archive_rule(
                existing.rule_id, existing.version, existing.model_dump(mode="json")
            )
            rule = rule.model_copy(update={"version": bump_version(existing.version)})
        item = get_rule_repo().upsert(rule)
        get_store().archive_rule(item.rule_id, item.version, item.model_dump(mode="json"))
        saved.append(item)
    get_rule_repo.cache_clear()
    get_orchestrator.cache_clear()
    return saved


@router.post("/rules/author", response_model=RuleAuthorResponse)
async def author_rules(
    body: RuleAuthorRequest,
    session: dict = Depends(require_user),  # noqa: B008
) -> RuleAuthorResponse:
    del session
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="empty text")
    preview = await get_orchestrator().ai_client.author_rules(text=body.text)
    saved: list[EditorialRule] = []
    if body.confirm:
        for rule in preview:
            existing = get_rule_repo().get(rule.rule_id)
            if existing:
                get_store().archive_rule(
                    existing.rule_id, existing.version, existing.model_dump(mode="json")
                )
                rule = rule.model_copy(update={"version": bump_version(existing.version)})
            item = get_rule_repo().upsert(rule)
            get_store().archive_rule(
                item.rule_id, item.version, item.model_dump(mode="json")
            )
            saved.append(item)
        get_rule_repo.cache_clear()
        get_orchestrator.cache_clear()
    return RuleAuthorResponse(preview=preview, saved=saved)


@router.get("/rules/{rule_id}/versions")
async def rule_versions(
    rule_id: str,
    session: dict = Depends(require_user),  # noqa: B008
) -> list[dict]:
    del session
    return get_store().list_rule_versions(rule_id)


# ---- entities -------------------------------------------------------------


@router.get("/entities", response_model=list[Entity])
async def list_entities(session: dict = Depends(require_user)) -> list[Entity]:  # noqa: B008
    del session
    return get_entity_repo().list_entities(active_only=False)


@router.post("/entities", response_model=Entity)
async def create_entity(
    entity: Entity,
    session: dict = Depends(require_user),  # noqa: B008
) -> Entity:
    del session
    existing = get_entity_repo().get(entity.entity_id)
    if existing:
        get_store().archive_entity(
            existing.entity_id, existing.version, existing.model_dump(mode="json")
        )
        entity = entity.model_copy(update={"version": bump_version(existing.version)})
    saved = get_entity_repo().upsert(entity)
    get_store().archive_entity(
        saved.entity_id, saved.version, saved.model_dump(mode="json")
    )
    get_entity_repo.cache_clear()
    get_orchestrator.cache_clear()
    return saved


@router.post("/entities/bulk", response_model=list[Entity])
async def bulk_entities(
    body: BulkPasteRequest,
    session: dict = Depends(require_user),  # noqa: B008
) -> list[Entity]:
    del session
    parsed = parse_entities_paste(body.text, body.delimiter)
    if not parsed:
        raise HTTPException(status_code=400, detail="no entities parsed from paste")
    saved: list[Entity] = []
    for entity in parsed:
        existing = get_entity_repo().get(entity.entity_id)
        if existing:
            get_store().archive_entity(
                existing.entity_id, existing.version, existing.model_dump(mode="json")
            )
            entity = entity.model_copy(update={"version": bump_version(existing.version)})
        item = get_entity_repo().upsert(entity)
        get_store().archive_entity(
            item.entity_id, item.version, item.model_dump(mode="json")
        )
        saved.append(item)
    get_entity_repo.cache_clear()
    get_orchestrator.cache_clear()
    return saved


@router.post("/evaluations/run", response_model=EvaluationRunResponse)
async def run_evals(
    request: EvaluationRunRequest,
    session: dict = Depends(require_admin),  # noqa: B008
) -> EvaluationRunResponse:
    del session
    dataset = request.dataset_path or str(ROOT_DIR / "data" / "evaluation" / "golden.jsonl")
    orchestrator = get_orchestrator()

    async def review_fn(record):
        return await orchestrator.review(
            ReviewRequest(
                document_id=record.record_id,
                headline=record.headline,
                body=record.body,
                source="evaluation",
            )
        )

    metrics = await run_evaluation(Path(dataset), review_fn)
    run_id = f"EVAL-{uuid4().hex[:10].upper()}"
    payload = metrics_to_dict(metrics)
    get_store().save_evaluation(run_id, payload)
    return EvaluationRunResponse(run_id=run_id, metrics=payload)
