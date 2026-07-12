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
        segments: list[Segment] | None = None,
        rules: list[EditorialRule] | None = None,
        entities: list[dict[str, Any]] | None = None,
    ) -> list[Finding]: ...

    async def repair_findings(
        self,
        *,
        findings: list[Finding],
        segments: list[Segment],
        validation_errors: dict[str, list[str]],
    ) -> list[Finding]: ...

    async def author_rules(self, *, text: str) -> list[EditorialRule]: ...
