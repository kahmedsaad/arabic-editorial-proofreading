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
from app.models.schemas import Document, FindingSource, ReviewRequest, ReviewResponse, Zone
from app.parsing.document import parse_document_text
from app.postprocess.gemini_gate import gate_gemini_findings, segments_for_gemini
from app.rules.repository import JsonRuleRepository
from app.segmentation.article import segment_article
from app.validation.validator import FindingValidator


class ReviewOrchestrator:
    def __init__(
        self,
        *,
        rule_repo: JsonRuleRepository | None = None,
        entity_repo: EntityRepository | None = None,
        ai_client: EditorialAIClient | None = None,
    ) -> None:
        self.rule_repo = rule_repo or JsonRuleRepository(settings.rules_dir)
        self.entity_repo = entity_repo or EntityRepository(settings.entities_dir)
        self.ai_client = ai_client or build_ai_client()
        self.spelling = load_spelling_replacements(settings.spelling_replacements_path)
        self.editorial_phrases = load_editorial_phrases(settings.editorial_phrases_path)
        self.grammar_patterns = load_editorial_phrases(settings.grammar_patterns_path)
        self.validator = FindingValidator(
            known_rule_ids=self.rule_repo.known_rule_ids(),
            known_categories=self.rule_repo.known_categories(),
            known_entity_ids=self.entity_repo.known_ids(),
        )

    async def review(self, request: ReviewRequest) -> ReviewResponse:
        document_id = request.document_id or f"DOC-{uuid4().hex[:8].upper()}"
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

        # Pass deterministic findings to the model as prior candidates/context.
        prior_findings = [*mechanical, *editorial, *consistency]
        gemini_segments = segments_for_gemini(segments, prior_findings)
        ai_candidates = await self.ai_client.discover_candidates(
            document_id=document.document_id,
            segments=gemini_segments,
            mechanical_findings=prior_findings,
            rules=unique_rules,
            entities=[e.model_dump() for e in unique_entities],
        )
        ai_judged = await self.ai_client.judge_candidates(candidates=ai_candidates)
        ai_kept, ai_gated = gate_gemini_findings(
            gemini_findings=ai_judged,
            mechanical_findings=prior_findings,
            segments=segments,
        )

        all_findings = dedupe_findings([*prior_findings, *ai_kept])
        valid, rejected = self.validator.validate(
            all_findings, segments, document.document_id
        )
        if ai_gated:
            rejected = [*rejected, *ai_gated]

        return ReviewResponse(
            review_id=f"REV-{uuid4().hex[:10].upper()}",
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
        )
