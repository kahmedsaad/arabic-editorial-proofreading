from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.ai.gemini_client import build_ai_client
from app.ai.protocol import EditorialAIClient
from app.config import settings
from app.entities.repository import EntityRepository, match_entities_in_text
from app.mechanical.checks import load_spelling_replacements, run_mechanical_checks
from app.mechanical.consistency import run_consistency_detectors
from app.mechanical.editorial_detectors import (
    dedupe_findings,
    load_editorial_phrases,
    run_editorial_detectors,
)
from app.models.schemas import (
    Document,
    FindingSource,
    PipelineLogStep,
    ReviewRequest,
    ReviewResponse,
    ReviewStage,
    Zone,
)
from app.parsing.document import parse_document_text
from app.postprocess.gemini_gate import gate_gemini_findings, segments_for_gemini
from app.rules.repository import JsonRuleRepository
from app.segmentation.article import segment_article
from app.validation.validator import FindingValidator


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReviewOrchestrator:
    def __init__(
        self,
        *,
        rule_repo: JsonRuleRepository | None = None,
        entity_repo: EntityRepository | None = None,
        ai_client: EditorialAIClient | None = None,
        prompt_provider=None,
        store=None,
    ) -> None:
        self.rule_repo = rule_repo or JsonRuleRepository(settings.rules_dir)
        self.entity_repo = entity_repo or EntityRepository(settings.entities_dir)
        self.prompt_provider = prompt_provider
        self.store = store
        self.ai_client = ai_client or build_ai_client(prompt_provider=prompt_provider)
        self.spelling = load_spelling_replacements(settings.spelling_replacements_path)
        self.editorial_phrases = load_editorial_phrases(settings.editorial_phrases_path)
        self.grammar_patterns = load_editorial_phrases(settings.grammar_patterns_path)
        self.validator = FindingValidator(
            known_rule_ids=self.rule_repo.known_rule_ids(),
            known_categories=self.rule_repo.known_categories(),
            known_entity_ids=self.entity_repo.known_ids(),
        )

    def _log_step(
        self,
        *,
        review_id: str,
        pipeline_log: list[PipelineLogStep],
        step_id: str,
        label: str,
        kind: str,
        started_at: str,
        system_prompt: str | None = None,
        user_payload: str | None = None,
        raw_response: str | None = None,
        context: dict[str, Any] | None = None,
        output_summary: dict[str, Any] | None = None,
    ) -> None:
        step = PipelineLogStep(
            step_id=step_id,
            label=label,
            kind=kind,
            system_prompt=system_prompt,
            user_payload=user_payload,
            raw_response=raw_response,
            context=context or {},
            output_summary=output_summary or {},
            started_at=started_at,
            finished_at=_now(),
        )
        pipeline_log.append(step)
        if self.store is not None:
            self.store.append_pipeline_step(review_id, step.model_dump(mode="json"))

    def _ai_trace(self) -> dict[str, Any]:
        return getattr(self.ai_client, "last_call_trace", None) or {}

    async def review(self, request: ReviewRequest) -> ReviewResponse:
        review_id = f"REV-{uuid4().hex[:10].upper()}"
        document_id = request.document_id or f"DOC-{uuid4().hex[:8].upper()}"
        pipeline_log: list[PipelineLogStep] = []
        stages: list[ReviewStage] = []

        if self.store is not None:
            self.store.init_pipeline_log(review_id, document_id)

        t0 = _now()
        headline = request.headline
        body = request.body
        if request.text and not (headline or body):
            parsed = parse_document_text(
                text=request.text,
                document_id=document_id,
                source=request.source,
                metadata=request.metadata,
            )
            document = parsed.document
            segments = parsed.segments
        else:
            document = Document(
                document_id=document_id,
                language=request.language,
                source=request.source,
                headline=headline,
                body=body,
                metadata=request.metadata,
            )
            segments = segment_article(document)

        self._log_step(
            review_id=review_id,
            pipeline_log=pipeline_log,
            step_id="ingest",
            label="Parse & segment article",
            kind="mechanical",
            started_at=t0,
            user_payload=(headline or "") + "\n\n" + (body or request.text or ""),
            context={"document_id": document.document_id, "source": request.source},
            output_summary={
                "segment_count": len(segments),
                "zones": [s.zone.value for s in segments],
            },
        )

        t1 = _now()
        mechanical = run_mechanical_checks(
            segments,
            self.spelling,
            entity_aliases=self.entity_repo.alias_map(),
            entity_forms=self.entity_repo.forms_by_entity(),
            enable_letter_variant_warnings=settings.enable_letter_variant_warnings,
        )
        editorial = run_editorial_detectors(
            segments,
            self.editorial_phrases,
            grammar_lexicon=self.grammar_patterns,
            counter_start=len(mechanical),
        )
        consistency = run_consistency_detectors(
            segments,
            counter_start=len(mechanical) + len(editorial),
        )
        prior_findings = [*mechanical, *editorial, *consistency]
        self._log_step(
            review_id=review_id,
            pipeline_log=pipeline_log,
            step_id="mechanical",
            label="Mechanical / editorial / consistency detectors",
            kind="mechanical",
            started_at=t1,
            context={"lexicons": ["spelling", "editorial_phrases", "grammar_patterns"]},
            output_summary={
                "mechanical": len(mechanical),
                "editorial": len(editorial),
                "consistency": len(consistency),
                "finding_ids": [f.finding_id for f in prior_findings],
            },
        )

        t2 = _now()
        retrieved_rules = []
        detected_entities = []
        for segment in segments:
            limit = 8 if segment.zone in {Zone.HEADLINE, Zone.CAPTION} else 5
            if "؟" in segment.text or "?" in segment.text:
                limit = min(10, limit + 2)
            retrieved_rules.extend(
                self.rule_repo.retrieve_for_segment(
                    zone=segment.zone,
                    normalized_text=segment.normalized_text,
                    limit=limit,
                )
            )
            detected_entities.extend(
                match_entities_in_text(segment.text, self.entity_repo.list_entities())
            )

        seen: set[str] = set()
        unique_rules = []
        for rule in retrieved_rules:
            if rule.rule_id not in seen:
                seen.add(rule.rule_id)
                unique_rules.append(rule)

        entity_seen: set[str] = set()
        unique_entities = []
        for entity in detected_entities:
            if entity.entity_id not in entity_seen:
                entity_seen.add(entity.entity_id)
                unique_entities.append(entity)

        stages.append(
            ReviewStage(
                stage_id="retrieve",
                label_ar="القواعد والكيانات ذات الصلة",
                summary={
                    "rule_ids": [r.rule_id for r in unique_rules],
                    "entity_ids": [e.entity_id for e in unique_entities],
                    "mechanical_count": len(prior_findings),
                },
            )
        )
        self._log_step(
            review_id=review_id,
            pipeline_log=pipeline_log,
            step_id="retrieve",
            label="Retrieve relevant rules & entities",
            kind="retrieve",
            started_at=t2,
            context={
                "per_segment_limits": "headline/caption=8 else 5 (+2 if question)",
            },
            output_summary={
                "rules": [r.model_dump(mode="json") for r in unique_rules],
                "entities": [e.model_dump(mode="json") for e in unique_entities],
            },
        )

        t3 = _now()
        gemini_segments = segments_for_gemini(segments, prior_findings)
        ai_candidates = await self.ai_client.discover_candidates(
            document_id=document.document_id,
            segments=gemini_segments,
            mechanical_findings=prior_findings,
            rules=unique_rules,
            entities=[e.model_dump() for e in unique_entities],
        )
        trace = self._ai_trace()
        stages.append(
            ReviewStage(
                stage_id="candidates",
                label_ar="المرشحات المكتشفة",
                summary={
                    "count": len(ai_candidates),
                    "spans": [
                        {
                            "finding_id": f.finding_id,
                            "original_text": f.original_text,
                            "rule_ids": f.rule_ids,
                        }
                        for f in ai_candidates[:40]
                    ],
                },
            )
        )
        self._log_step(
            review_id=review_id,
            pipeline_log=pipeline_log,
            step_id="discover",
            label="LLM candidate discovery (loaded framing / relational triggers)",
            kind="llm",
            started_at=t3,
            system_prompt=trace.get("system_prompt"),
            user_payload=trace.get("user_payload"),
            raw_response=trace.get("raw_response"),
            context={
                "rules_sent": [r.rule_id for r in unique_rules],
                "entities_sent": [e.entity_id for e in unique_entities],
                "segment_ids": [s.segment_id for s in gemini_segments],
            },
            output_summary={
                "candidate_count": len(ai_candidates),
                "finding_ids": [f.finding_id for f in ai_candidates],
            },
        )

        t4 = _now()
        ai_judged = await self.ai_client.judge_candidates(
            candidates=ai_candidates,
            segments=segments,
            rules=unique_rules,
            entities=[e.model_dump() for e in unique_entities],
        )
        trace = self._ai_trace()
        stages.append(
            ReviewStage(
                stage_id="judgment",
                label_ar="الحكم التحريري",
                summary={
                    "count": len(ai_judged),
                    "decisions": {
                        d: sum(1 for f in ai_judged if f.decision.value == d)
                        for d in {f.decision.value for f in ai_judged}
                    },
                },
            )
        )
        self._log_step(
            review_id=review_id,
            pipeline_log=pipeline_log,
            step_id="judge",
            label="LLM judgment over candidates",
            kind="llm",
            started_at=t4,
            system_prompt=trace.get("system_prompt"),
            user_payload=trace.get("user_payload"),
            raw_response=trace.get("raw_response"),
            context={"input_from": "discover", "candidate_count": len(ai_candidates)},
            output_summary={
                "judged_count": len(ai_judged),
                "decisions": [f.decision.value for f in ai_judged],
            },
        )

        t5 = _now()
        ai_kept, ai_gated = gate_gemini_findings(
            gemini_findings=ai_judged,
            mechanical_findings=prior_findings,
            segments=segments,
        )
        self._log_step(
            review_id=review_id,
            pipeline_log=pipeline_log,
            step_id="gate",
            label="Non-LLM gate (quote preserve / dedupe / confidence)",
            kind="gate",
            started_at=t5,
            context={"input_from": "judge"},
            output_summary={
                "kept": len(ai_kept),
                "gated": len(ai_gated),
                "kept_ids": [f.finding_id for f in ai_kept],
                "gated_ids": [f.finding_id for f in ai_gated],
            },
        )

        t6 = _now()
        all_findings = dedupe_findings([*prior_findings, *ai_kept])
        valid, rejected = self.validator.validate(
            all_findings, segments, document.document_id
        )

        if rejected:
            error_map = {
                f.finding_id: list(f.validation_errors)
                for f in rejected
                if f.validation_errors
            }
            for f in ai_gated:
                if f.finding_id not in error_map and f.validation_errors:
                    error_map[f.finding_id] = list(f.validation_errors)
            to_repair = [f for f in rejected if f.finding_id in error_map]
            if to_repair:
                t7 = _now()
                repaired = await self.ai_client.repair_findings(
                    findings=to_repair,
                    segments=segments,
                    validation_errors=error_map,
                )
                trace = self._ai_trace()
                self._log_step(
                    review_id=review_id,
                    pipeline_log=pipeline_log,
                    step_id="repair",
                    label="LLM repair of invalid findings",
                    kind="llm",
                    started_at=t7,
                    system_prompt=trace.get("system_prompt"),
                    user_payload=trace.get("user_payload"),
                    raw_response=trace.get("raw_response"),
                    context={"validation_errors": error_map},
                    output_summary={"repaired_returned": len(repaired)},
                )
                repaired_valid, repaired_rejected = self.validator.validate(
                    repaired, segments, document.document_id
                )
                repaired_ids = {f.finding_id for f in repaired}
                still_unrepaired = [
                    f for f in rejected if f.finding_id not in repaired_ids
                ]
                valid = dedupe_findings([*valid, *repaired_valid])
                rejected = [*still_unrepaired, *repaired_rejected]
                stages.append(
                    ReviewStage(
                        stage_id="validation",
                        label_ar="التحقق والتصحيح",
                        summary={
                            "repaired": len(repaired_valid),
                            "still_rejected": len(rejected),
                            "errors_sample": [
                                {"finding_id": fid, "errors": errs[:3]}
                                for fid, errs in list(error_map.items())[:8]
                            ],
                        },
                    )
                )
            else:
                stages.append(
                    ReviewStage(
                        stage_id="validation",
                        label_ar="التحقق والتصحيح",
                        summary={"repaired": 0, "still_rejected": len(rejected)},
                    )
                )
        else:
            stages.append(
                ReviewStage(
                    stage_id="validation",
                    label_ar="التحقق والتصحيح",
                    summary={"repaired": 0, "still_rejected": 0},
                )
            )

        self._log_step(
            review_id=review_id,
            pipeline_log=pipeline_log,
            step_id="validate",
            label="Schema validator (non-LLM)",
            kind="validate",
            started_at=t6,
            context={"input_from": "gate (+ repair if any)"},
            output_summary={
                "valid": len(valid),
                "rejected": len(rejected),
                "rejected_errors": {
                    f.finding_id: f.validation_errors for f in rejected if f.validation_errors
                },
            },
        )

        if ai_gated:
            rejected = [*rejected, *ai_gated]

        stages.append(
            ReviewStage(
                stage_id="final",
                label_ar="الحكم النهائي",
                summary={"findings": len(valid), "rejected": len(rejected)},
            )
        )
        self._log_step(
            review_id=review_id,
            pipeline_log=pipeline_log,
            step_id="final",
            label="Final findings for editor",
            kind="final",
            started_at=_now(),
            output_summary={
                "findings": [f.model_dump(mode="json") for f in valid],
                "rejected_count": len(rejected),
            },
        )

        return ReviewResponse(
            review_id=review_id,
            document=document,
            segments=segments,
            findings=valid,
            rejected_findings=rejected,
            mechanical_finding_count=sum(
                1 for f in valid if f.source == FindingSource.MECHANICAL
            ),
            ai_finding_count=sum(
                1 for f in valid if f.source in {FindingSource.MOCK, FindingSource.GEMINI}
            ),
            stages=stages,
            retrieved_rules=unique_rules,
            retrieved_entities=unique_entities,
            candidate_findings=ai_candidates,
            pipeline_log=pipeline_log,
        )
