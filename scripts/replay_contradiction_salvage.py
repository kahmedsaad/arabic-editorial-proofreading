from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.ai.gemini_client import GeminiEditorialAIClient
from app.models.schemas import Finding, ReviewRequest
from app.orchestration.review import ReviewOrchestrator


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "evaluation" / "ui_acceptance" / "arabic_ui_acceptance_v1.jsonl"


def _finding_payload(finding: Finding) -> dict[str, Any]:
    return finding.model_dump(mode="json")


class RecordingClient:
    def __init__(self) -> None:
        self.inner = GeminiEditorialAIClient()
        self.calls: list[dict[str, Any]] = []

    @property
    def last_call_trace(self) -> dict[str, Any] | None:
        return self.inner.last_call_trace

    async def discover_candidates(self, **kwargs: Any) -> list[Finding]:
        findings = await self.inner.discover_candidates(**kwargs)
        trace = self.last_call_trace or {}
        self.calls.append(
            {
                "stage": "candidate_generation",
                "findings": [_finding_payload(finding) for finding in findings],
                "category_canonicalization": trace.get(
                    "category_canonicalization", []
                ),
                "parser_diagnostic": trace.get("parser_diagnostic"),
            }
        )
        return findings

    async def judge_candidates(self, **kwargs: Any) -> list[Finding]:
        findings = await self.inner.judge_candidates(**kwargs)
        trace = self.last_call_trace or {}
        self.calls.append(
            {
                "stage": "judgment",
                "findings": [_finding_payload(finding) for finding in findings],
                "category_canonicalization": trace.get(
                    "category_canonicalization", []
                ),
                "parser_diagnostic": trace.get("parser_diagnostic"),
            }
        )
        return findings

    async def repair_findings(self, **kwargs: Any) -> list[Finding]:
        self.calls.append(
            {
                "stage": "repair_request",
                "findings": [
                    _finding_payload(finding) for finding in kwargs["findings"]
                ],
                "validation_errors": kwargs["validation_errors"],
            }
        )
        findings = await self.inner.repair_findings(**kwargs)
        trace = self.last_call_trace or {}
        self.calls.append(
            {
                "stage": "repair_response",
                "findings": [_finding_payload(finding) for finding in findings],
                "category_canonicalization": trace.get(
                    "category_canonicalization", []
                ),
                "parser_diagnostic": trace.get("parser_diagnostic"),
            }
        )
        return findings

    async def author_rules(self, **kwargs: Any) -> Any:
        return await self.inner.author_rules(**kwargs)


def _load_cases(case_ids: set[str]) -> list[dict[str, Any]]:
    cases = [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [case for case in cases if case["id"] in case_ids]


def _safe_pipeline_steps(response: Any) -> list[dict[str, Any]]:
    step_ids = {
        "gate",
        "adjudicate",
        "editorial_gate",
        "punctuation_gate",
        "repair",
        "validate",
        "final",
    }
    safe_steps = []
    for step in response.pipeline_log:
        if step.step_id not in step_ids:
            continue
        context = step.context
        if step.step_id == "repair":
            context = {"validation_errors": context.get("validation_errors", {})}
        safe_steps.append(
            {
                "step_id": step.step_id,
                "context": context,
                "output_summary": step.output_summary,
            }
        )
    return safe_steps


async def _run(case_ids: set[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for case in _load_cases(case_ids):
        client = RecordingClient()
        response = await ReviewOrchestrator(ai_client=client).review(
            ReviewRequest(
                document_id=f"UI-{case['id']}",
                headline=case["title"],
                body=case["body"],
            )
        )
        results.append(
            {
                "case_id": case["id"],
                "segments": [
                    segment.model_dump(mode="json") for segment in response.segments
                ],
                "model_calls": client.calls,
                "pipeline_steps": _safe_pipeline_steps(response),
                "findings": [
                    _finding_payload(finding) for finding in response.findings
                ],
                "rejected_findings": [
                    _finding_payload(finding)
                    for finding in response.rejected_findings
                ],
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases",
        default="D01,D06",
        help="Comma-separated UI acceptance case IDs.",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    case_ids = {case_id.strip() for case_id in args.cases.split(",") if case_id.strip()}
    results = asyncio.run(_run(case_ids))
    output = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
