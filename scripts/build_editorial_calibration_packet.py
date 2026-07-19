#!/usr/bin/env python3
"""Build a deterministic 30-item editorial-label calibration packet."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3" / "expert_labels.jsonl"
)
DEFAULT_OUTPUT = (
    ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3" / "calibration_packet.md"
)

KEEP_STRATA = [
    (("headline_body_mismatch", "publisher_voice", "headline_framing"), 4),
    (("numeric_contradiction",), 3),
    (("spelling",), 1),
    (("repetition",), 1),
    (("grammar", "consistency"), 1),
]
DROP_STRATA = [
    (("attribution", "attribution_strength"), 3),
    (("clarity",), 3),
    (("loaded_framing",), 2),
    (("entity_name",), 2),
    (("headline_body_mismatch", "publisher_voice", "headline_framing"), 2),
    (("spelling",), 2),
    (("repetition",), 1),
]
UNCERTAIN_STRATA = [
    (("numeric_contradiction",), 3),
    (("entity_confusion",), 1),
    (("headline_body_mismatch", "publisher_voice", "headline_framing"), 1),
]


def load_rows(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def duplicate_groups(rows: list[dict]) -> dict[tuple[str, str, str, str], list[int]]:
    groups: dict[tuple[str, str, str, str], list[int]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("article_id") or ""),
            str(row.get("category") or ""),
            str(row.get("original_text") or "").strip(),
            str(row.get("explanation_ar") or "").strip(),
        )
        groups[key].append(int(row["source_index"]))
    return {key: indices for key, indices in groups.items() if len(indices) > 1}


def _take_strata(rows: list[dict], decision: str, strata: list[tuple[tuple[str, ...], int]]) -> list[dict]:
    selected: list[dict] = []
    used: set[int] = set()
    for categories, count in strata:
        candidates = [
            row
            for row in rows
            if row.get("decision") == decision
            and row.get("category") in categories
            and int(row["source_index"]) not in used
        ]
        candidates.sort(key=lambda row: int(row["source_index"]))
        if len(candidates) < count:
            raise ValueError(
                f"insufficient {decision} rows for {categories}: need {count}, got {len(candidates)}"
            )
        chosen = candidates[:count]
        selected.extend(chosen)
        used.update(int(row["source_index"]) for row in chosen)
    return selected


def _take_drop_strata(rows: list[dict]) -> list[dict]:
    """Select drop strata while forcing one auditable exact-duplicate pair."""
    by_index = {int(row["source_index"]): row for row in rows}
    attribution_pair: list[int] | None = None
    for indices in sorted(duplicate_groups(rows).values(), key=lambda values: values[0]):
        pair_rows = [by_index[index] for index in indices[:2]]
        if all(
            row.get("decision") == "drop"
            and row.get("category") in {"attribution", "attribution_strength"}
            for row in pair_rows
        ):
            attribution_pair = indices[:2]
            break
    if attribution_pair is None:
        raise ValueError("no dropped attribution duplicate pair available")

    selected = [by_index[index] for index in attribution_pair]
    extra = next(
        row
        for row in sorted(rows, key=lambda item: int(item["source_index"]))
        if row.get("decision") == "drop"
        and row.get("category") in {"attribution", "attribution_strength"}
        and int(row["source_index"]) not in attribution_pair
    )
    selected.append(extra)
    selected.extend(_take_strata(rows, "drop", DROP_STRATA[1:]))
    return selected


def select_rows(rows: list[dict]) -> list[dict]:
    selected = [
        *_take_strata(rows, "keep", KEEP_STRATA),
        *_take_drop_strata(rows),
        *_take_strata(rows, "uncertain", UNCERTAIN_STRATA),
    ]
    counts = {decision: sum(row["decision"] == decision for row in selected) for decision in ("keep", "drop", "uncertain")}
    if counts != {"keep": 10, "drop": 15, "uncertain": 5} or len(selected) != 30:
        raise AssertionError(f"unexpected sample composition: {counts}, total={len(selected)}")
    return selected


def _clean(value: object, limit: int | None = None) -> str:
    text = " ".join(str(value or "").split())
    if limit and len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text.replace("|", r"\|")


def _source_context(row: dict) -> str:
    body = " ".join(str(row.get("body_excerpt") or "").split())
    needle = " ".join(str(row.get("original_text") or "").split())
    if needle and needle in body:
        start = max(0, body.index(needle) - 140)
        end = min(len(body), body.index(needle) + len(needle) + 180)
        excerpt = body[start:end]
        if start:
            excerpt = "…" + excerpt
        if end < len(body):
            excerpt += "…"
    else:
        excerpt = body[:360] + ("…" if len(body) > 360 else "")
    return _clean(excerpt)


def render(rows: list[dict], all_rows: list[dict], input_path: Path) -> str:
    duplicates = duplicate_groups(all_rows)
    duplicate_index: dict[int, list[int]] = {}
    for indices in duplicates.values():
        for index in indices:
            duplicate_index[index] = indices

    lines = [
        "# Arabic editorial calibration packet",
        "",
        "> AI labels are calibration evidence, not editorial truth. Reviewer fields are intentionally blank.",
        "",
        "## Deterministic selection method",
        "",
        f"- Input: `{input_path.as_posix()}` (163 rows, source order by `source_index`).",
        "- Fixed decision quotas: 10 `keep`, 15 `drop`, 5 `uncertain`.",
        "- Within each fixed category stratum below, select the lowest available `source_index`; no random seed or manual substitution.",
        "- Keep strata: headline 4, numeric 3, spelling 1, repetition 1, grammar/consistency 1.",
        "- Drop strata: attribution 3, clarity 3, loaded framing 2, entity 2, headline 2, spelling 2, repetition 1.",
        "- Uncertain strata: numeric 3, entity confusion 1, headline 1.",
        "- Duplicate markers use exact article + category + original span + explanation groups across all 163 rows.",
        "",
        "## Reviewer instructions",
        "",
        "For each item, choose exactly one: `agree | change_to_keep | change_to_drop | change_to_uncertain`.",
        "Do not edit the current AI decision in this packet; record a proposed change and evidence in reviewer notes.",
        "",
    ]

    for number, row in enumerate(rows, start=1):
        index = int(row["source_index"])
        duplicate_note = (
            ", ".join(str(value) for value in duplicate_index[index])
            if index in duplicate_index
            else "none detected"
        )
        proposed = _clean(row.get("suggested_text")) or "—"
        lines.extend(
            [
                f"## {number}. `{_clean(row.get('label_id'))}`",
                "",
                f"- **Source index / category:** `{index}` / `{_clean(row.get('category'))}`",
                f"- **Headline:** {_clean(row.get('headline'), 220) or '—'}",
                f"- **Necessary source context:** {_source_context(row) or '—'}",
                f"- **Model finding:** {_clean(row.get('explanation_ar'), 420) or '—'}",
                f"- **Original span → proposed edit:** `{_clean(row.get('original_text'), 180) or '—'}` → `{proposed}`",
                f"- **Current AI decision:** `{row.get('decision')}`",
                f"- **AI rationale / confidence:** {_clean(row.get('rationale'), 260)} / `{row.get('label_confidence')}`",
                f"- **Duplicate-pattern source indices:** `{duplicate_note}`",
                "- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`",
                "- **Reviewer notes:**",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    rows = load_rows(args.input)
    if len(rows) != 163:
        raise ValueError(f"expected 163 expert labels, got {len(rows)}")
    selected = select_rows(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(selected, rows, args.input), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "total": len(selected),
                "keep": sum(row["decision"] == "keep" for row in selected),
                "drop": sum(row["decision"] == "drop" for row in selected),
                "uncertain": sum(row["decision"] == "uncertain" for row in selected),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
