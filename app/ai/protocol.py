from typing import Any, Protocol

from app.models.schemas import EditorialRule, Finding, Segment


class EditorialAIClient(Protocol):
    async def discover_candidates(
        self,
        *,
        document_id: str,
        segments: list[Segment],
        mechanical_findings: list[Finding],
        rules: list[EditorialRule],
        entities: list[dict[str, Any]] | None = None,
    ) -> list[Finding]: ...

    async def judge_candidates(
        self,
        *,
        candidates: list[Finding],
    ) -> list[Finding]: ...
