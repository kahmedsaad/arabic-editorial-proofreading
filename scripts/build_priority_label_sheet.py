#!/usr/bin/env python3
"""Build priority-ordered editorial labeling sheet (read source, write local copy)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CATEGORY_RANK = {
    "attribution": 0,
    "attribution_strength": 0,
    "source_quality": 0,
    "source_misrepresentation": 0,
    "headline_body_mismatch": 1,
    "headline_framing": 1,
    "publisher_voice": 1,
    "clarity": 2,
    "quote_voice": 3,
    "loaded_framing": 4,
    "entity_name": 5,
    "entity_confusion": 5,
    "numeric_contradiction": 6,
    "temporal_contradiction": 7,
}

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _load(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _sort_key(row: dict) -> tuple:
    cat = (row.get("category") or "").lower()
    return (
        CATEGORY_RANK.get(cat, 99),
        -SEVERITY_RANK.get((row.get("severity") or "low").lower(), 0),
        -(float(row.get("confidence") or 0.0)),
        str(row.get("article_id") or ""),
        str(row.get("segment_id") or ""),
        str(row.get("finding_id") or ""),
    )


def _ensure_label_fields(row: dict, *, preserve_existing: bool) -> dict:
    out = dict(row)
    if preserve_existing and not _is_blank(out.get("decision")):
        # Keep completed labels; still normalize editor_notes key
        if "editor_notes" not in out and "notes" in out:
            out["editor_notes"] = out.get("notes")
        return out
    out["decision"] = None
    out["drop_reason"] = None
    out["editor_notes"] = None
    return out


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build priority editorial label sheet")
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT
        / "data"
        / "evaluation"
        / "analysis"
        / "gemini_run3_precision"
        / "non_punctuation_todo.jsonl",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=ROOT / "data" / "local" / "sprint2" / "non_punctuation_to_label.jsonl",
        help="Working label file; completed decisions are preserved into priority view",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "local" / "sprint2" / "non_punctuation_priority_to_label.jsonl",
    )
    args = parser.parse_args(argv)

    if not args.source.exists():
        raise SystemExit(f"Missing source: {args.source}")

    source_rows = _load(args.source)
    # Prefer working labels if present (may contain completed decisions)
    label_by_key: dict[tuple, dict] = {}
    if args.labels.exists():
        for row in _load(args.labels):
            key = (
                row.get("article_id"),
                row.get("finding_id"),
                row.get("label_id"),
            )
            label_by_key[key] = row

    merged: list[dict] = []
    for row in source_rows:
        key = (row.get("article_id"), row.get("finding_id"), row.get("label_id"))
        base = dict(row)
        if key in label_by_key:
            # Overlay label fields from working copy when present
            overlay = label_by_key[key]
            for field in ("decision", "drop_reason", "editor_notes", "notes", "annotator_decision"):
                if field in overlay and not _is_blank(overlay.get(field)):
                    # Map legacy annotator_decision → decision if needed
                    if field == "annotator_decision" and _is_blank(base.get("decision")):
                        base["decision"] = overlay[field]
                    elif field != "annotator_decision":
                        base[field] = overlay[field]
        merged.append(_ensure_label_fields(base, preserve_existing=True))

    merged.sort(key=_sort_key)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for row in merged:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(
        json.dumps(
            {
                "wrote": str(args.out),
                "n": len(merged),
                "labeled": sum(1 for r in merged if not _is_blank(r.get("decision"))),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
