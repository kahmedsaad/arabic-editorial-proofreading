from app.models.schemas import Decision, Finding, FindingSource, Segment, Severity, ValidationStatus

ALLOWED_DECISIONS = set(Decision)
ALLOWED_SEVERITIES = set(Severity)
ALLOWED_SOURCES = set(FindingSource)


class FindingValidator:
    """Deterministic validator. Rejects invalid findings; no LLM repair."""

    def __init__(
        self,
        *,
        known_rule_ids: set[str],
        known_categories: set[str],
        known_entity_ids: set[str] | None = None,
    ) -> None:
        self.known_rule_ids = known_rule_ids | {
            "MECH-DUP-WORD",
            "MECH-WS",
            "MECH-PUNCT-SPACE",
            "MECH-PUNCT-AFTER",
            "MECH-PUNCT-DUP",
            "MECH-SPELL",
            "MECH-LETTER-VAR",
            "MECH-QUOTE",
            "MECH-DIGITS",
            "MECH-MALFORMED",
            "MECH-ENTITY",
            "MECH-ENTITY-INCONSISTENT",
            "MECH-GRAMMAR",
            "CONS-NUMBER",
            "CONS-DATE",
            "CONS-NAME",
        }
        self.known_categories = known_categories
        self.known_entity_ids = known_entity_ids or set()

    def validate(
        self,
        findings: list[Finding],
        segments: list[Segment],
        document_id: str,
    ) -> tuple[list[Finding], list[Finding]]:
        by_id = {s.segment_id: s for s in segments}
        valid: list[Finding] = []
        rejected: list[Finding] = []

        for finding in findings:
            finding = self._realign_offsets(finding, by_id)
            errors = self._errors(finding, by_id, document_id)
            updated = finding.model_copy(
                update={
                    "validation_status": (
                        ValidationStatus.INVALID if errors else ValidationStatus.VALID
                    ),
                    "validation_errors": errors,
                    "requires_editor_review": finding.requires_editor_review
                    or finding.severity in {Severity.HIGH, Severity.CRITICAL},
                }
            )
            if errors:
                rejected.append(updated)
            else:
                valid.append(updated)
        return valid, rejected

    def _realign_offsets(
        self, finding: Finding, segments: dict[str, Segment]
    ) -> Finding:
        """Repair LLM offset drift when original_text is present in the segment."""
        segment = segments.get(finding.segment_id)
        if segment is None or not finding.original_text:
            return finding
        span = segment.text[finding.start_offset : finding.end_offset]
        if finding.original_text == span:
            return finding
        idx = segment.text.find(finding.original_text)
        if idx < 0:
            return finding
        return finding.model_copy(
            update={
                "start_offset": idx,
                "end_offset": idx + len(finding.original_text),
            }
        )

    def _errors(
        self,
        finding: Finding,
        segments: dict[str, Segment],
        document_id: str,
    ) -> list[str]:
        errors: list[str] = []

        if finding.document_id != document_id:
            errors.append("document_id mismatch")
        if finding.segment_id not in segments:
            errors.append("unknown segment_id")
            return errors

        segment = segments[finding.segment_id]
        if finding.start_offset < 0 or finding.end_offset > len(segment.text):
            errors.append("offsets outside segment bounds")
        if finding.start_offset >= finding.end_offset:
            errors.append("invalid offset range")

        span = segment.text[finding.start_offset : finding.end_offset]
        if finding.original_text != span:
            errors.append("original_text does not match segment span")
        if finding.original_text not in segment.text:
            errors.append("original_text not found in segment")

        if finding.category not in self.known_categories:
            errors.append(f"unknown category: {finding.category}")
        if finding.decision not in ALLOWED_DECISIONS:
            errors.append(f"unknown decision: {finding.decision}")
        if finding.severity not in ALLOWED_SEVERITIES:
            errors.append(f"unknown severity: {finding.severity}")
        if finding.source not in ALLOWED_SOURCES:
            errors.append(f"unknown source: {finding.source}")

        for rule_id in finding.rule_ids:
            if rule_id not in self.known_rule_ids:
                errors.append(f"unknown rule_id: {rule_id}")
        for entity_id in finding.entity_ids:
            if entity_id not in self.known_entity_ids:
                errors.append(f"unknown entity_id: {entity_id}")

        if not finding.explanation_ar.strip():
            errors.append("missing explanation_ar")

        if (
            finding.decision in {Decision.SUGGEST, Decision.REPLACE}
            and finding.suggested_text is not None
            and finding.suggested_text == finding.original_text
        ):
            errors.append("suggested_text identical to original_text")

        if finding.suggested_text is not None and len(finding.suggested_text) > max(
            500, len(finding.original_text) * 5
        ):
            errors.append("suggested_text unreasonably long")

        return errors
