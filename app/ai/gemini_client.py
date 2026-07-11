from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from app.ai.fewshot import MUST_CHECK_RULES, load_golden_fewshots
from app.config import ROOT_DIR, settings
from app.models.schemas import (
    Decision,
    EditorialRule,
    Finding,
    FindingSource,
    Segment,
    Severity,
)

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
    ) -> None:
        self.model = model or settings.gemini_model
        self.timeout_seconds = timeout_seconds
        self.prompt_dir = prompt_dir or PROMPT_DIR
        self.last_latency_ms: float | None = None
        self.last_token_usage: dict[str, Any] | None = None
        self._fewshots = load_golden_fewshots(settings.golden_editorial_path)

    def _system_prompt(self) -> str:
        path = self.prompt_dir / "system.txt"
        if path.exists():
            return path.read_text(encoding="utf-8")
        fallback = ROOT_DIR / "GEMINI_SYSTEM_PROMPT.txt"
        return fallback.read_text(encoding="utf-8") if fallback.exists() else ""

    def _user_payload(
        self,
        *,
        document_id: str,
        segments: list[Segment],
        mechanical_findings: list[Finding],
        rules: list[EditorialRule],
        entities: list[dict[str, Any]] | None = None,
    ) -> str:
        template_path = self.prompt_dir / "user_template.json"
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
                }
            ]
        }
        payload = {
            "document_id": document_id,
            "segments": [s.model_dump() for s in segments],
            "mechanical_findings": [f.model_dump() for f in mechanical_findings],
            "rules": [r.model_dump() for r in rules],
            "entities": entities or [],
            "must_check_rules": MUST_CHECK_RULES,
            "golden_examples": self._fewshots,
            "output_schema": schema_hint,
            "instructions": (
                "Return JSON only with key findings. Prefer an empty findings list over "
                "speculative warnings. Do not rewrite the full article. "
                "Offsets are segment-local and must match original_text exactly. "
                "Scan every must_check_rules item. Use golden_examples as style guidance. "
                "For quoted loaded language use needs_editor_review and suggested_text=null. "
                "Do not flag correctly attributed quotations unless a separate rule violation "
                "exists outside the quote. Skip issues already listed in mechanical_findings. "
                "decision must be one of: acceptable, suggest, replace, soft_warning, "
                "hard_warning, ban, needs_editor_review."
            ),
        }
        if template_path.exists():
            payload["template_version"] = "v1"
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
            item["finding_id"] = f"FND-AI-{index:04d}"
            item["decision"] = self._normalize_decision(item.get("decision"))
            if "severity" in item and item["severity"] is not None:
                sev = str(item["severity"]).strip().lower()
                if sev not in {s.value for s in Severity}:
                    item["severity"] = Severity.MEDIUM.value
            try:
                findings.append(Finding.model_validate(item))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping invalid Gemini finding: %s (%s)", exc, item)
        return findings

    async def discover_candidates(
        self,
        *,
        document_id: str,
        segments: list[Segment],
        mechanical_findings: list[Finding],
        rules: list[EditorialRule],
        entities: list[dict[str, Any]] | None = None,
    ) -> list[Finding]:
        started = time.perf_counter()
        try:
            from google import genai  # type: ignore
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini SDK unavailable: %s", exc)
            return self._fallback_finding(document_id, segments, "sdk_unavailable")

        if (
            not settings.gemini_api_key
            and not settings.google_application_credentials
            and not (settings.use_gcp and settings.gcp_project_id)
        ):
            return self._fallback_finding(document_id, segments, "missing_credentials")

        prompt = self._user_payload(
            document_id=document_id,
            segments=segments,
            mechanical_findings=mechanical_findings,
            rules=rules,
            entities=entities,
        )
        try:
            if settings.use_gcp and settings.gcp_project_id:
                # Vertex AI — billed via linked Cloud Billing (not AI Studio prepaid).
                if settings.google_application_credentials:
                    import os

                    os.environ.setdefault(
                        "GOOGLE_APPLICATION_CREDENTIALS",
                        str(settings.google_application_credentials),
                    )
                client = genai.Client(
                    vertexai=True,
                    project=settings.gcp_project_id,
                    location=settings.gcp_location,
                )
            else:
                client = genai.Client(api_key=settings.gemini_api_key or None)

            response = None
            last_exc: Exception | None = None
            for attempt in range(1, 6):
                try:
                    response = client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config={
                            "system_instruction": self._system_prompt(),
                            "response_mime_type": "application/json",
                            "temperature": 0.2,
                        },
                    )
                    last_exc = None
                    break
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    msg = str(exc)
                    retryable = "429" in msg or "RESOURCE_EXHAUSTED" in msg or "UNAVAILABLE" in msg
                    if not retryable or attempt >= 5:
                        raise
                    sleep_s = min(60.0, 2.0 ** attempt)
                    logger.warning(
                        "Gemini transient error (attempt %s/5): %s; sleeping %.1fs",
                        attempt,
                        msg[:160],
                        sleep_s,
                    )
                    time.sleep(sleep_s)
            if response is None:
                raise last_exc or RuntimeError("Gemini returned no response")

            self.last_latency_ms = (time.perf_counter() - started) * 1000
            usage = getattr(response, "usage_metadata", None)
            if usage is not None:
                self.last_token_usage = {
                    "prompt_tokens": getattr(usage, "prompt_token_count", None),
                    "candidates_tokens": getattr(usage, "candidates_token_count", None),
                    "total_tokens": getattr(usage, "total_token_count", None),
                }
                logger.info(
                    "gemini latency_ms=%.1f usage=%s",
                    self.last_latency_ms,
                    self.last_token_usage,
                )
            raw_text = getattr(response, "text", None) or ""
            if not raw_text and getattr(response, "candidates", None):
                parts = response.candidates[0].content.parts
                raw_text = "".join(getattr(p, "text", "") for p in parts)
            return self._parse_findings(raw_text, document_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini discover failed: %s", str(exc)[:240])
            self.last_latency_ms = (time.perf_counter() - started) * 1000
            return self._fallback_finding(document_id, segments, str(exc)[:180])

    async def judge_candidates(self, *, candidates: list[Finding]) -> list[Finding]:
        """Lightweight deterministic judgment over model candidates."""
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
            # Prefer editor review when suggestion equals original
            if (
                finding.suggested_text is not None
                and finding.suggested_text.strip() == finding.original_text.strip()
            ):
                update["decision"] = Decision.NEEDS_EDITOR_REVIEW
                update["suggested_text"] = None
                update["requires_editor_review"] = True
            judged.append(finding.model_copy(update=update) if update else finding)
        return judged


def build_ai_client():
    from app.ai.mock_client import MockEditorialAIClient

    if settings.ai_client.lower() == "gemini":
        return GeminiEditorialAIClient()
    return MockEditorialAIClient()
