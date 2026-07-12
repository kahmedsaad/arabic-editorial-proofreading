from __future__ import annotations

import csv
import io
import re
from uuid import uuid4

from app.models.schemas import EditorialRule, Entity, RuleExample, Severity, Zone


def _split_list(value: str) -> list[str]:
    if not value or not str(value).strip():
        return []
    parts = re.split(r"[;|،,/]", str(value))
    return [p.strip() for p in parts if p.strip()]


def _detect_delimiter(text: str) -> str:
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    if "\t" in first:
        return "\t"
    if first.count(";") >= 2:
        return ";"
    if first.count(",") >= 2:
        return ","
    return "\t"


def _rows_from_paste(text: str, delimiter: str | None = None) -> list[dict[str, str]]:
    text = text.strip()
    if not text:
        return []
    delim = delimiter or _detect_delimiter(text)
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    if reader.fieldnames:
        # Normalize headers
        fieldmap = {h: h.strip().lower().replace(" ", "_") for h in reader.fieldnames}
        rows: list[dict[str, str]] = []
        for raw in reader:
            rows.append({fieldmap.get(k, k): (v or "").strip() for k, v in raw.items() if k})
        if rows:
            return rows
    # Headerless: treat as columns by position
    reader2 = csv.reader(io.StringIO(text), delimiter=delim)
    rows2: list[dict[str, str]] = []
    for parts in reader2:
        parts = [p.strip() for p in parts]
        if not any(parts):
            continue
        rows2.append({"col0": parts[0] if parts else "", "col1": parts[1] if len(parts) > 1 else "", "col2": parts[2] if len(parts) > 2 else "", "col3": parts[3] if len(parts) > 3 else ""})
    return rows2


def bump_version(version: str) -> str:
    m = re.match(r"^(\d+)\.(\d+)$", version.strip())
    if not m:
        return "1.1"
    major, minor = int(m.group(1)), int(m.group(2))
    return f"{major}.{minor + 1}"


def parse_entities_paste(text: str, delimiter: str | None = None) -> list[Entity]:
    rows = _rows_from_paste(text, delimiter)
    entities: list[Entity] = []
    for i, row in enumerate(rows, start=1):
        canonical = (
            row.get("canonical_ar")
            or row.get("approved_ar")
            or row.get("entity")
            or row.get("name")
            or row.get("col0")
            or ""
        ).strip()
        if not canonical:
            continue
        entity_id = (
            row.get("entity_id") or row.get("id") or f"E_PASTE_{uuid4().hex[:6].upper()}"
        ).strip()
        aliases = _split_list(row.get("aliases") or row.get("alias") or row.get("col1") or "")
        category = (
            row.get("category") or row.get("type") or row.get("col2") or "general"
        ).strip() or "general"
        current_title = (row.get("current_title") or row.get("title") or "").strip() or None
        profiles = _split_list(
            row.get("policy_profiles") or row.get("profiles") or row.get("col3") or ""
        )
        entities.append(
            Entity(
                entity_id=entity_id,
                canonical_ar=canonical,
                aliases=aliases,
                category=category,
                current_title=current_title,
                policy_profiles=profiles,
                version="1.0",
                active=True,
            )
        )
    return entities


def parse_rules_paste(text: str, delimiter: str | None = None) -> list[EditorialRule]:
    rows = _rows_from_paste(text, delimiter)
    rules: list[EditorialRule] = []
    for i, row in enumerate(rows, start=1):
        title = (
            row.get("title_ar")
            or row.get("title")
            or row.get("name")
            or row.get("col0")
            or ""
        ).strip()
        description = (
            row.get("description_ar")
            or row.get("description")
            or row.get("rule")
            or row.get("col1")
            or title
        ).strip()
        if not title and not description:
            continue
        rule_id = (row.get("rule_id") or row.get("id") or f"R_PASTE_{uuid4().hex[:6].upper()}").strip()
        category = (row.get("category") or row.get("col2") or "terminology").strip() or "terminology"
        rule_type = (row.get("rule_type") or row.get("type") or "mechanical").strip()
        if rule_type not in {"mechanical", "relational", "lexical"}:
            rule_type = "mechanical"
        keywords = _split_list(row.get("keywords") or row.get("col3") or "")
        severity_raw = (row.get("severity") or "medium").strip().lower()
        try:
            severity = Severity(severity_raw)
        except ValueError:
            severity = Severity.MEDIUM
        zones_raw = _split_list(row.get("zones") or row.get("applies_to_zones") or "")
        zones: list[Zone] = []
        for z in zones_raw:
            try:
                zones.append(Zone(z))
            except ValueError:
                continue
        rules.append(
            EditorialRule(
                rule_id=rule_id,
                version="1.0",
                title_ar=title or description[:40],
                category=category,
                rule_type=rule_type,
                description_ar=description or title,
                applies_to_zones=zones or [Zone.BODY, Zone.HEADLINE],
                severity=severity,
                keywords=keywords,
                examples=[],
                active=True,
            )
        )
    return rules


def free_text_to_rule_stub(text: str) -> EditorialRule:
    """Fallback when LLM author is unavailable."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = lines[0][:80] if lines else "قاعدة جديدة"
    return EditorialRule(
        rule_id=f"R_AUTO_{uuid4().hex[:6].upper()}",
        version="1.0",
        title_ar=title,
        category="terminology",
        rule_type="relational" if any(w in text for w in ("سياق", "اقتباس", "كيان", "relational")) else "mechanical",
        description_ar=text.strip()[:500],
        applies_to_zones=[Zone.BODY, Zone.HEADLINE],
        severity=Severity.MEDIUM,
        keywords=[],
        examples=[RuleExample(input="", preferred="", reason="")] if False else [],
        active=True,
    )
