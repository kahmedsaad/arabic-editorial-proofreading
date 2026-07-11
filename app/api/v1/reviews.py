from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.deps import get_entity_repo, get_orchestrator, get_rule_repo, get_store
from app.config import ROOT_DIR, settings
from app.evaluation.metrics import metrics_to_dict, run_evaluation
from app.models.schemas import (
    EditorialRule,
    Entity,
    EvaluationRunRequest,
    EvaluationRunResponse,
    ParseRequest,
    ParseResponse,
    ReviewRequest,
    ReviewResponse,
)
from app.parsing.document import parse_document_text
from app.parsing.docx_intake import extract_text_from_upload

router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "arabic-editorial-proofreading",
        "ai_client": settings.ai_client,
        "use_gcp": settings.use_gcp,
        "phase7_ready": False,
    }


@router.post("/documents/parse", response_model=ParseResponse)
async def parse_document(request: ParseRequest) -> ParseResponse:
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
async def upload_document(file: UploadFile = File(...)) -> ParseResponse:  # noqa: B008
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
async def create_review(request: ReviewRequest) -> ReviewResponse:
    review = await get_orchestrator().review(request)
    get_store().save_review(review)
    return review


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: str) -> ReviewResponse:
    review = get_store().get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="review not found")
    # Editor view: hide rejected
    return review.model_copy(update={"rejected_findings": []})


@router.get("/reviews/{review_id}/debug", response_model=ReviewResponse)
async def get_review_debug(review_id: str) -> ReviewResponse:
    review = get_store().get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="review not found")
    return review


@router.get("/rules", response_model=list[EditorialRule])
async def list_rules() -> list[EditorialRule]:
    return get_rule_repo().list_rules(active_only=False)


@router.get("/rules/{rule_id}", response_model=EditorialRule)
async def get_rule(rule_id: str) -> EditorialRule:
    rule = get_rule_repo().get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    return rule


@router.post("/rules", response_model=EditorialRule)
async def create_rule(rule: EditorialRule) -> EditorialRule:
    saved = get_rule_repo().upsert(rule)
    get_rule_repo.cache_clear()
    get_orchestrator.cache_clear()
    return saved


@router.get("/entities", response_model=list[Entity])
async def list_entities() -> list[Entity]:
    return get_entity_repo().list_entities(active_only=False)


@router.post("/entities", response_model=Entity)
async def create_entity(entity: Entity) -> Entity:
    saved = get_entity_repo().upsert(entity)
    get_entity_repo.cache_clear()
    get_orchestrator.cache_clear()
    return saved


@router.post("/evaluations/run", response_model=EvaluationRunResponse)
async def run_evals(request: EvaluationRunRequest) -> EvaluationRunResponse:
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
