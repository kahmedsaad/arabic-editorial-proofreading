#!/usr/bin/env python3
"""Adjudicate proposed editorial-label corrections into derived artifacts.

This script never overwrites expert_labels.jsonl, source templates, or proposals.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3"

# Human-review substitute explicitly delegated to the AI expert for this POC.
# "uncertain" means the proposal cannot be decided from supplied context and is
# therefore not applied; the original label is retained.
ADJUDICATIONS: dict[int, tuple[str, str, str]] = {
    117: ("accept", "Rationale template names طهران/إيران although the span is قطري; keep drop decision, correct rationale.", "high"),
    118: ("accept", "Rationale template names طهران/إيران although the span is تونسية; keep drop decision, correct rationale.", "high"),
    119: ("accept", "Rationale template names طهران/إيران although the span is وكالة رويترز; keep drop decision, correct rationale.", "high"),
    120: ("accept", "Rationale template names طهران/إيران although the span is تونسية; keep drop decision, correct rationale.", "high"),
    121: ("accept", "Rationale template names طهران/إيران although the span is قطري; keep drop decision, correct rationale.", "high"),
    123: ("accept", "Rationale template names طهران/إيران although the span is قطري; keep drop decision, correct rationale.", "high"),
    126: ("accept", "Rationale template names طهران/إيران although the span is قطري; keep drop decision, correct rationale.", "high"),
    127: ("accept", "Rationale template names طهران/إيران although the span is تونسية; keep drop decision, correct rationale.", "high"),
    40: ("accept", "Body says access was formerly invite-only and now available to Passport members; the claimed contradiction is invented.", "high"),
    128: ("accept", "Three wins are required to break the record while eight are already achieved; these are different quantities.", "high"),
    129: ("accept", "Three wins are required to break the record while eight are already achieved; these are different quantities.", "high"),
    47: ("accept", "The cited player denial is absent from supplied context, so keep is not supportable; uncertain preserves missing evidence.", "high"),
    49: ("accept", "The cited stopped-deportation fact is absent from supplied context, so keep is not supportable; uncertain preserves missing evidence.", "high"),
    50: ("uncertain", "The cited span is absent from the excerpt, but may occur in truncated article context; retain original rather than guess.", "medium"),
    59: ("uncertain", "Europe/world aggregates do not disprove a ranking among countries, and supplied text lacks country-by-country evidence.", "high"),
    60: ("uncertain", "The claimed earlier exceptions are not present in supplied excerpt; retain original drop pending fuller context.", "medium"),
    104: ("uncertain", "Publisher-voice wording may be loaded, but intended house-style policy is unavailable; retain original drop.", "medium"),
}


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def adjudicate(
    proposals: list[dict],
    expert_labels: list[dict],
    scoring_rows: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    if len(proposals) != 17:
        raise ValueError(f"expected 17 proposals, got {len(proposals)}")
    proposal_indices = {int(row["source_index"]) for row in proposals}
    if proposal_indices != set(ADJUDICATIONS):
        raise ValueError(
            f"proposal/adjudication mismatch: missing={proposal_indices - set(ADJUDICATIONS)}, "
            f"extra={set(ADJUDICATIONS) - proposal_indices}"
        )
    if len(expert_labels) != 163 or len(scoring_rows) != 163:
        raise ValueError("expected 163 expert/scoring rows")

    expert_by_index = {int(row["source_index"]): dict(row) for row in expert_labels}
    score_by_label = {row["label_id"]: dict(row) for row in scoring_rows}
    records: list[dict] = []

    for proposal in proposals:
        source_index = int(proposal["source_index"])
        outcome, rationale, confidence = ADJUDICATIONS[source_index]
        original = expert_by_index[source_index]
        applied = outcome == "accept"
        record = {
            "source_index": source_index,
            "label_id": proposal["label_id"],
            "adjudication": outcome,
            "adjudication_rationale": rationale,
            "adjudication_confidence": confidence,
            "applied": applied,
            "original_decision": original["decision"],
            "proposed_decision": proposal["proposed_decision"],
            "final_decision": proposal["proposed_decision"] if applied else original["decision"],
            "proposal": proposal,
            "artifact_status": "final_ai_expert_adjudication",
        }
        records.append(record)
        if not applied:
            continue

        for row in (original, score_by_label[proposal["label_id"]]):
            row["decision"] = proposal["proposed_decision"]
            row["drop_reason"] = proposal.get("proposed_drop_reason")
            row["rationale"] = proposal["proposed_rationale"]
            row["editor_notes"] = proposal["proposed_rationale"]
            row["label_confidence"] = proposal["confidence"]
            row["adjudication_source"] = "correction_adjudications.jsonl"
            row["adjudication_outcome"] = "accept"
        expert_by_index[source_index] = original

    final_expert = [expert_by_index[index] for index in range(163)]
    final_scoring = [score_by_label[row["label_id"]] for row in scoring_rows]
    return records, final_expert, final_scoring


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposals", type=Path, default=BASE / "proposed_label_corrections.jsonl")
    parser.add_argument("--expert-labels", type=Path, default=BASE / "expert_labels.jsonl")
    parser.add_argument("--scoring-input", type=Path, default=BASE / "labeled_for_scoring.jsonl")
    parser.add_argument("--out-dir", type=Path, default=BASE)
    args = parser.parse_args(argv)

    records, final_expert, final_scoring = adjudicate(
        _read_jsonl(args.proposals),
        _read_jsonl(args.expert_labels),
        _read_jsonl(args.scoring_input),
    )
    _write_jsonl(args.out_dir / "correction_adjudications.jsonl", records)
    _write_jsonl(args.out_dir / "final_adjudicated_labels.jsonl", final_expert)
    _write_jsonl(args.out_dir / "final_adjudicated_for_scoring.jsonl", final_scoring)
    counts = {
        outcome: sum(row["adjudication"] == outcome for row in records)
        for outcome in ("accept", "reject", "uncertain")
    }
    print(json.dumps({"adjudications": counts, "out_dir": str(args.out_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
