from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from app.ai.fewshot import MUST_CHECK_RULES, load_golden_fewshots
from app.config import ROOT_DIR, settings
from app.models.schemas import (
    ArticleContext,
    Decision,
    EditorialRule,
    Finding,
    FindingSource,
    Segment,
    Severity,
    ValidationStatus,
)
from app.rules.bulk import free_text_to_rule_stub, parse_rules_paste

logger = logging.getLogger(__name__)

PROMPT_DIR = ROOT_DIR / "prompts" / "gemini" / "v1"


class GeminiEditorialAIClient:
    """Gemini client with structured JSON output. Falls back safely on errors."""

    def __init__(
        self,
        *,
        model: str | None = None,
        timeout_seconds: float = 30.0,
        prompt_dir: Path | None = None,
        prompt_provider: Any | None = None,
    ) -> None:
        self.model = model or settings.gemini_model
        self.timeout_seconds = timeout_seconds
        self.prompt_dir = prompt_dir or PROMPT_DIR
        self.prompt_provider = prompt_provider
        self.last_latency_ms: float | None = None
        self.last_token_usage: dict[str, Any] | None = None
        self.last_call_trace: dict[str, Any] | None = None
        self._fewshots = load_golden_fewshots(settings.golden_editorial_path)

    def _phase_prompt(self, phase: str) -> str:
        if self.prompt_provider is not None:
            try:
                body = self.prompt_provider.prompt_body(phase)
                if body:
                    return body
            except Exception as exc:  # noqa: BLE001
                logger.warning("prompt store read failed for %s: %s", phase, exc)
        if phase == "discover":
            path = self.prompt_dir / "system.txt"
            if path.exists():
                return path.read_text(encoding="utf-8")
            fallback = ROOT_DIR / "GEMINI_SYSTEM_PROMPT.txt"
            return fallback.read_text(encoding="utf-8") if fallback.exists() else ""
        return ""

    def _system_prompt(self) -> str:
        return self._phase_prompt("discover")

    def _user_payload(
        self,
        *,
        document_id: str,
        segments: list[Segment],
        mechanical_findings: list[Finding],
        rules: list[EditorialRule],
        entities: list[dict[str, Any]] | None = None,
        article_context: ArticleContext | None = None,
    ) -> str:
        schema_hint = {
            "findings": [
                {
                    "finding_id": "FND-AI-...",
                    "document_id": document_id,
                    "segment_id": "SEG-001",
                    "source": "gemini",
                    "category": "attribution",
                    "decision": "needs_editor_review",
                    "severity": "medium",
                    "original_text": "...",
                    "suggested_text": "...",
                    "start_offset": 0,
                    "end_offset": 1,
                    "rule_ids": [],
                    "entity_ids": [],
                    "explanation_ar": "...",
                    "confidence": 0.5,
                    "requires_editor_review": True,
                    "editorial_harm_if_ignored": "low",
                    "rule_applicability": "uncertain",
                    "article_context_resolves_issue": False,
                    "would_interrupt_editor": False,
                    "quotation_status": "not_quote",
                    "publisher_voice": True,
                }
            ]
        }
        payload = {
            "document_id": document_id,
            "article_context": (
                article_context.model_dump(mode="json") if article_context else None
            ),
            "segments": [s.model_dump() for s in segments],
            "mechanical_findings": [f.model_dump() for f in mechanical_findings],
            "rules": [r.model_dump() for r in rules],
            "entities": entities or [],
            "must_check_rules": MUST_CHECK_RULES,
            "golden_examples": self._fewshots,
            "output_schema": schema_hint,
            "instructions": (
                "Discovery only: return candidate findings with category, exact span, "
                "segment_id, concern, rule_ids. Prefer empty list over speculative "
                "warnings. Do not rewrite the full article. "
                "Use article_context for quotes/speakers/attribution. "
                "Stay silent on headline compression when body attributes. "
                "Offsets are segment-local and must match original_text exactly. "
                "decision must be one of: acceptable, suggest, replace, soft_warning, "
                "hard_warning, ban, needs_editor_review."
            ),
        }
        return json.dumps(payload, ensure_ascii=False)

    def _fallback_finding(
        self, document_id: str, segments: list[Segment], reason: str
    ) -> list[Finding]:
        if not segments:
            return []
        segment = segments[0]
        span = segment.text[: min(12, len(segment.text))] or segment.text
        end = len(span)
        return [
            Finding(
                finding_id="FND-AI-FALLBACK",
                document_id=document_id,
                segment_id=segment.segment_id,
                source=FindingSource.GEMINI,
                category="clarity",
                decision=Decision.NEEDS_EDITOR_REVIEW,
                severity=Severity.MEDIUM,
                original_text=span,
                suggested_text=None,
                start_offset=0,
                end_offset=end,
                rule_ids=[],
                explanation_ar=f"تعذر إكمال تحليل النموذج: {reason}",
                confidence=0.0,
                requires_editor_review=True,
            )
        ]

    _DECISION_ALIASES = {
        "suggestion": Decision.SUGGEST,
        "suggested": Decision.SUGGEST,
        "warn": Decision.SOFT_WARNING,
        "warning": Decision.SOFT_WARNING,
        "soft": Decision.SOFT_WARNING,
        "hard": Decision.HARD_WARNING,
        "review": Decision.NEEDS_EDITOR_REVIEW,
        "editor_review": Decision.NEEDS_EDITOR_REVIEW,
        "needs_review": Decision.NEEDS_EDITOR_REVIEW,
    }

    def _normalize_decision(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
        if raw in {d.value for d in Decision}:
            return raw
        aliased = self._DECISION_ALIASES.get(raw)
        return aliased.value if aliased else Decision.NEEDS_EDITOR_REVIEW.value

    def _parse_findings(self, raw: str, document_id: str) -> list[Finding]:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        data = json.loads(text)
        items = data.get("findings", data if isinstance(data, list) else [])
        findings: list[Finding] = []
        for index, item in enumerate(items, start=1):
            item = dict(item)
            item["document_id"] = item.get("document_id") or document_id
            item["source"] = FindingSource.GEMINI
            item["finding_id"] = item.get("finding_id") or f"FND-AI-{index:04d}"
            item["decision"] = self._normalize_decision(item.get("decision"))
            # Models sometimes invent validation_status values; reset to pending.
            vs = str(item.get("validation_status") or "pending").strip().lower()
            if vs not in {s.value for s in ValidationStatus}:
                item["validation_status"] = "pending"
            if "severity" in item and item["severity"] is not None:
                sev = str(item["severity"]).strip().lower()
                if sev not in {s.value for s in Severity}:
                    item["severity"] = Severity.MEDIUM.value
            try:
                findings.append(Finding.model_validate(item))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping invalid Gemini finding: %s (%s)", exc, item)
        return findings

    def _client(self):
        from google import genai  # type: ignore

        if settings.use_gcp and settings.gcp_project_id:
            if settings.google_application_credentials:
                import os

                os.environ.setdefault(
                    "GOOGLE_APPLICATION_CREDENTIALS",
                    str(settings.google_application_credentials),
                )
            return genai.Client(
                vertexai=True,
                project=settings.gcp_project_id,
                location=settings.gcp_location,
            )
        return genai.Client(api_key=settings.gemini_api_key or None)

    def _has_credentials(self) -> bool:
        return bool(
            settings.gemini_api_key
            or settings.google_application_credentials
            or (settings.use_gcp and settings.gcp_project_id)
        )

    def _generate(self, *, system: str, user: str) -> str:
        client = self._client()
        response = None
        last_exc: Exception | None = None
        for attempt in range(1, 6):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=user,
                    config={
                        "system_instruction": system,
                        "response_mime_type": "application/json",
                        "temperature": 0.2,
                    },
                )
                last_exc = None
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                msg = str(exc)
                retryable = (
                    "429" in msg or "RESOURCE_EXHAUSTED" in msg or "UNAVAILABLE" in msg
                )
                if not retryable or attempt >= 5:
                    raise
                sleep_s = min(60.0, 2.0**attempt)
                logger.warning(
                    "Gemini transient error (attempt %s/5): %s; sleeping %.1fs",
                    attempt,
                    msg[:160],
                    sleep_s,
                )
                time.sleep(sleep_s)
        if response is None:
            raise last_exc or RuntimeError("Gemini returned no response")
        raw_text = getattr(response, "text", None) or ""
        if not raw_text and getattr(response, "candidates", None):
            parts = response.candidates[0].content.parts
            raw_text = "".join(getattr(p, "text", "") for p in parts)
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            self.last_token_usage = {
                "prompt_tokens": getattr(usage, "prompt_token_count", None),
                "candidates_tokens": getattr(usage, "candidates_token_count", None),
                "total_tokens": getattr(usage, "total_token_count", None),
            }
        self.last_call_trace = {
            "system_prompt": system,
            "user_payload": user,
            "raw_response": raw_text,
            "token_usage": self.last_token_usage,
        }
        return raw_text

    async def discover_candidates(
        self,
        *,
        document_id: str,
        segments: list[Segment],
        mechanical_findings: list[Finding],
        rules: list[EditorialRule],
        entities: list[dict[str, Any]] | None = None,
        article_context: ArticleContext | None = None,
    ) -> list[Finding]:
        started = time.perf_counter()
        try:
            from google import genai  # noqa: F401
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini SDK unavailable: %s", exc)
            return self._fallback_finding(document_id, segments, "sdk_unavailable")

        if not self._has_credentials():
            return self._fallback_finding(document_id, segments, "missing_credentials")

        prompt = self._user_payload(
            document_id=document_id,
            segments=segments,
            mechanical_findings=mechanical_findings,
            rules=rules,
            entities=entities,
            article_context=article_context,
        )
        try:
            raw_text = self._generate(system=self._system_prompt(), user=prompt)
            self.last_latency_ms = (time.perf_counter() - started) * 1000
            return self._parse_findings(raw_text, document_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini discover failed: %s", str(exc)[:240])
            self.last_latency_ms = (time.perf_counter() - started) * 1000
            return self._fallback_finding(document_id, segments, str(exc)[:180])

    def _heuristic_judge(self, candidates: list[Finding]) -> list[Finding]:
        judged: list[Finding] = []
        for finding in candidates:
            update: dict[str, Any] = {}
            if not finding.explanation_ar.strip():
                update["decision"] = Decision.NEEDS_EDITOR_REVIEW
                update["requires_editor_review"] = True
                update["explanation_ar"] = "تعذر التحقق من التفسير؛ تحتاج مراجعة المحرر."
            if finding.confidence < 0.35:
                update["decision"] = Decision.NEEDS_EDITOR_REVIEW
                update["requires_editor_review"] = True
            if finding.severity in {Severity.HIGH, Severity.CRITICAL}:
                update["requires_editor_review"] = True
            if finding.decision in {
                Decision.BAN,
                Decision.HARD_WARNING,
                Decision.NEEDS_EDITOR_REVIEW,
            }:
                update["requires_editor_review"] = True
            if (
                finding.suggested_text is not None
                and finding.suggested_text.strip() == finding.original_text.strip()
            ):
                update["decision"] = Decision.NEEDS_EDITOR_REVIEW
                update["suggested_text"] = None
                update["requires_editor_review"] = True
            judged.append(finding.model_copy(update=update) if update else finding)
        return judged

    async def judge_candidates(
        self,
        *,
        candidates: list[Finding],
        segments: list[Segment] | None = None,
        rules: list[EditorialRule] | None = None,
        entities: list[dict[str, Any]] | None = None,
        article_context: ArticleContext | None = None,
    ) -> list[Finding]:
        if not candidates:
            return []
        if not self._has_credentials():
            judged = self._heuristic_judge(candidates)
            self.last_call_trace = {
                "system_prompt": self._phase_prompt("judge"),
                "user_payload": "(heuristic — no credentials)",
                "raw_response": json.dumps(
                    {"findings": [f.model_dump(mode="json") for f in judged]},
                    ensure_ascii=False,
                ),
            }
            return judged
        try:
            from google import genai  # noqa: F401
        except Exception:
            judged = self._heuristic_judge(candidates)
            self.last_call_trace = {
                "system_prompt": self._phase_prompt("judge"),
                "user_payload": "(heuristic — SDK unavailable)",
                "raw_response": json.dumps(
                    {"findings": [f.model_dump(mode="json") for f in judged]},
                    ensure_ascii=False,
                ),
            }
            return judged

        document_id = candidates[0].document_id
        user = json.dumps(
            {
                "candidates": [c.model_dump(mode="json") for c in candidates],
                "article_context": (
                    article_context.model_dump(mode="json") if article_context else None
                ),
                "segments": [s.model_dump(mode="json") for s in (segments or [])],
                "rules": [r.model_dump(mode="json") for r in (rules or [])],
                "entities": entities or [],
                "instructions": (
                    "Precision adjudication: keep only candidates that deserve to "
                    "interrupt an editor. Suppress headline attribution when body "
                    "attributes; never rewrite quotes; set silence fields. "
                    "Return {\"findings\":[...]}."
                ),
            },
            ensure_ascii=False,
        )
        try:
            raw = self._generate(system=self._phase_prompt("judge"), user=user)
            parsed = self._parse_findings(raw, document_id)
            return parsed or self._heuristic_judge(candidates)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini judge failed: %s", str(exc)[:200])
            return self._heuristic_judge(candidates)

    async def repair_findings(
        self,
        *,
        findings: list[Finding],
        segments: list[Segment],
        validation_errors: dict[str, list[str]],
    ) -> list[Finding]:
        if not findings:
            return []
        if not self._has_credentials():
            return self._local_repair(findings, segments, validation_errors)
        try:
            from google import genai  # noqa: F401
        except Exception:
            return self._local_repair(findings, segments, validation_errors)

        document_id = findings[0].document_id
        payload = {
            "findings": [
                {
                    **f.model_dump(mode="json"),
                    "validation_errors": validation_errors.get(f.finding_id, []),
                }
                for f in findings
            ],
            "segments": [s.model_dump(mode="json") for s in segments],
            "instructions": (
                "Repair only listed validation errors. Drop irreparable findings. "
                "Return {\"findings\":[...]}."
            ),
        }
        try:
            raw = self._generate(
                system=self._phase_prompt("repair"),
                user=json.dumps(payload, ensure_ascii=False),
            )
            return self._parse_findings(raw, document_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini repair failed: %s", str(exc)[:200])
            return self._local_repair(findings, segments, validation_errors)

    def _local_repair(
        self,
        findings: list[Finding],
        segments: list[Segment],
        validation_errors: dict[str, list[str]],
    ) -> list[Finding]:
        by_id = {s.segment_id: s for s in segments}
        repaired: list[Finding] = []
        for finding in findings:
            if finding.finding_id not in validation_errors:
                repaired.append(finding)
                continue
            segment = by_id.get(finding.segment_id)
            if segment is None or finding.original_text not in segment.text:
                continue
            idx = segment.text.find(finding.original_text)
            repaired.append(
                finding.model_copy(
                    update={
                        "start_offset": idx,
                        "end_offset": idx + len(finding.original_text),
                        "validation_errors": [],
                    }
                )
            )
        return repaired

    async def author_rules(self, *, text: str) -> list[EditorialRule]:
        pasted = parse_rules_paste(text)
        looks_tabular = "\t" in text or (text.count("\n") > 1 and ("," in text or ";" in text))
        if pasted and looks_tabular:
            return pasted
        if not self._has_credentials():
            return pasted or [free_text_to_rule_stub(text)]
        try:
            from google import genai  # noqa: F401
        except Exception:
            return pasted or [free_text_to_rule_stub(text)]

        user = json.dumps(
            {
                "input_text": text,
                "instructions": "Return {\"rules\":[...]} matching EditorialRule schema.",
            },
            ensure_ascii=False,
        )
        try:
            raw = self._generate(system=self._phase_prompt("rule_author"), user=user)
            data = json.loads(raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))
            items = data.get("rules", data if isinstance(data, list) else [])
            rules: list[EditorialRule] = []
            for item in items:
                try:
                    rules.append(EditorialRule.model_validate(item))
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Skipping invalid authored rule: %s", exc)
            return rules or pasted or [free_text_to_rule_stub(text)]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini rule author failed: %s", str(exc)[:200])
            return pasted or [free_text_to_rule_stub(text)]


def build_ai_client(*, prompt_provider: Any | None = None):
    from app.ai.mock_client import MockEditorialAIClient

    if settings.ai_client.lower() == "gemini":
        return GeminiEditorialAIClient(prompt_provider=prompt_provider)
    return MockEditorialAIClient()
