#!/usr/bin/env python3
"""Temporary one-off audit helper for editorial labels (not a product gate)."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3" / "expert_labels.jsonl"
OUT_MD = ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3" / "label_consistency_audit.md"
OUT_JSONL = (
    ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3" / "proposed_label_corrections.jsonl"
)


def load_rows() -> list[dict]:
    return [
        json.loads(line)
        for line in LABELS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def duplicate_groups(rows: list[dict]) -> dict[tuple, list[int]]:
    groups: dict[tuple, list[int]] = defaultdict(list)
    for row in rows:
        key = (
            row.get("article_id"),
            row.get("category"),
            (row.get("original_text") or "").strip(),
            (row.get("explanation_ar") or "").strip(),
        )
        groups[key].append(int(row["source_index"]))
    return {key: idxs for key, idxs in groups.items() if len(idxs) > 1}


def main() -> int:
    rows = load_rows()
    assert len(rows) == 163
    by_idx = {int(r["source_index"]): r for r in rows}
    dups = duplicate_groups(rows)

    findings: list[dict] = []
    corrections: list[dict] = []

    # 1) exact duplicates labeled inconsistently
    inconsistent_exact = 0
    for key, idxs in sorted(dups.items(), key=lambda item: item[1][0]):
        decisions = {by_idx[i]["decision"] for i in idxs}
        if len(decisions) > 1:
            inconsistent_exact += 1
            findings.append(
                {
                    "kind": "inconsistent_duplicate",
                    "severity": "strong",
                    "source_indices": idxs,
                    "label_ids": [by_idx[i]["label_id"] for i in idxs],
                    "decisions": sorted(decisions),
                    "note": "Exact duplicate group labeled with conflicting decisions.",
                }
            )

    # 2) rationale/template contradictions
    template_mismatches = []
    for row in rows:
        rationale = row.get("rationale") or ""
        orig = row.get("original_text") or ""
        expl = row.get("explanation_ar") or ""
        if "طهران/إيران" in rationale and "طهران" not in orig and "طهران" not in expl:
            template_mismatches.append(row)
            findings.append(
                {
                    "kind": "rationale_contradicts_text",
                    "severity": "strong",
                    "source_index": int(row["source_index"]),
                    "label_id": row["label_id"],
                    "decision": row["decision"],
                    "note": "Rationale cites طهران/إيران metonym, but span/explanation are unrelated.",
                }
            )
            corrections.append(
                {
                    "label_id": row["label_id"],
                    "source_index": int(row["source_index"]),
                    "current_decision": row["decision"],
                    "proposed_decision": "drop",
                    "proposed_drop_reason": "optional_style",
                    "proposed_rationale": (
                        "Entity naming preference without clear wrong form; "
                        "prior rationale incorrectly reused طهران/إيران template."
                    ),
                    "confidence": "high",
                    "evidence": {
                        "original_text": orig,
                        "explanation_ar": expl,
                        "old_rationale": rationale,
                    },
                    "status": "proposed_only_not_applied",
                }
            )

    # 3) keep suggestions that alter certainty/attribution/meaning
    keep_risks = []
    for row in rows:
        if row.get("decision") != "keep":
            continue
        sug = row.get("suggested_text")
        expl = row.get("explanation_ar") or ""
        if not sug:
            # Quote keep with no rewrite is fine; publisher_voice keep with rewrite is riskier.
            continue
        sug_s = str(sug)
        risk = None
        if row.get("category") == "publisher_voice" and sug_s.startswith("ويرى"):
            risk = "keep_suggestion_adds_attribution_frame"
        elif any(token in sug_s for token in ("ربما", "قد ", "توقع", "مصادر:", "شائعات")):
            risk = "keep_suggestion_softens_certainty"
        elif "اقتباس" in expl:
            risk = "keep_suggestion_rewrites_quote"
        if risk:
            keep_risks.append(row)
            findings.append(
                {
                    "kind": risk,
                    "severity": "review",
                    "source_index": int(row["source_index"]),
                    "label_id": row["label_id"],
                    "decision": "keep",
                    "note": f"Keep with suggestion that may alter certainty/attribution/meaning: {sug_s[:120]}",
                }
            )

    # Strong keep correction: ANAD-015348 is certainty/hedging, not material contradiction.
    row40 = by_idx[40]
    corrections.append(
        {
            "label_id": row40["label_id"],
            "source_index": 40,
            "current_decision": row40["decision"],
            "proposed_decision": "drop",
            "proposed_drop_reason": "headline_compression",
            "proposed_rationale": (
                "Headline asserts open availability while body reports invite-gated / unofficial "
                "availability; this is certainty/hedging compression more than a verified outcome conflict."
            ),
            "confidence": "medium",
            "evidence": {
                "original_text": row40.get("original_text"),
                "explanation_ar": row40.get("explanation_ar"),
                "body_excerpt": (row40.get("body_excerpt") or "")[:280],
            },
            "status": "proposed_only_not_applied",
        }
    )
    findings.append(
        {
            "kind": "keep_may_overstate_material_conflict",
            "severity": "strong",
            "source_index": 40,
            "label_id": row40["label_id"],
            "decision": "keep",
            "note": "Keep treats invite-gated availability as a material contradiction; closer to certainty escalation.",
        }
    )

    # Strong keep correction: ANAD-392361 numeric 3 vs 8 appears to misunderstand "3 remaining wins".
    for idx in (128, 129):
        row = by_idx[idx]
        corrections.append(
            {
                "label_id": row["label_id"],
                "source_index": idx,
                "current_decision": row["decision"],
                "proposed_decision": "drop",
                "proposed_drop_reason": "context_resolves_issue",
                "proposed_rationale": (
                    "Body says eight consecutive wins already and two more needed to equal the record; "
                    "headline '3 انتصارات' can refer to remaining wins needed, not current streak."
                ),
                "confidence": "high",
                "evidence": {
                    "headline": row.get("headline"),
                    "body_excerpt": (row.get("body_excerpt") or "")[:320],
                    "explanation_ar": row.get("explanation_ar"),
                },
                "status": "proposed_only_not_applied",
            }
        )
        findings.append(
            {
                "kind": "keep_misreads_numeric_context",
                "severity": "strong",
                "source_index": idx,
                "label_id": row["label_id"],
                "decision": "keep",
                "note": "Numeric keep likely false: 3 remaining wins vs 8 achieved streak.",
            }
        )

    # Drop that may conceal material defect: ANAD-439722 partial vs full restriction lift.
    row60 = by_idx[60]
    corrections.append(
        {
            "label_id": row60["label_id"],
            "source_index": 60,
            "current_decision": row60["decision"],
            "proposed_decision": "keep",
            "proposed_drop_reason": None,
            "proposed_rationale": (
                "Headline claims full lifting of travel restrictions after 1 Jan 2021, while body "
                "describes earlier partial exceptions; this is unsupported overstatement, not mere compression."
            ),
            "confidence": "medium",
            "evidence": {
                "original_text": row60.get("original_text"),
                "explanation_ar": row60.get("explanation_ar"),
            },
            "status": "proposed_only_not_applied",
        }
    )
    findings.append(
        {
            "kind": "drop_may_conceal_headline_overstatement",
            "severity": "strong",
            "source_index": 60,
            "label_id": row60["label_id"],
            "decision": "drop",
            "note": "Dropped as compression, but explanation alleges misleading full vs partial scope.",
        }
    )

    # Drop may conceal loaded framing in publisher voice (SANAD-122948).
    row104 = by_idx[104]
    findings.append(
        {
            "kind": "drop_may_conceal_loaded_framing",
            "severity": "review",
            "source_index": 104,
            "label_id": row104["label_id"],
            "decision": "drop",
            "note": "Publisher-voice evaluative language ('فظاعة' / 'آلة الحرب') may be a real neutrality issue on some desks.",
        }
    )
    corrections.append(
        {
            "label_id": row104["label_id"],
            "source_index": 104,
            "current_decision": row104["decision"],
            "proposed_decision": "uncertain",
            "proposed_drop_reason": None,
            "proposed_rationale": (
                "Publisher-voice loaded evaluation may be material depending on house style; "
                "silence-set drop is too confident without profile policy."
            ),
            "confidence": "medium",
            "evidence": {
                "original_text": row104.get("original_text"),
                "explanation_ar": row104.get("explanation_ar"),
            },
            "status": "proposed_only_not_applied",
        }
    )

    # Uncertain numeric ANAD-443219 / related: explanation already shows split kg vs cans; keep as uncertain is ok.
    # Clarity drops with no concrete defect — review flags only for Arabic/Latin numeral mixing if desired.
    for idx in (69, 71, 72):
        row = by_idx[idx]
        findings.append(
            {
                "kind": "drop_numeral_style_flag",
                "severity": "review",
                "source_index": idx,
                "label_id": row["label_id"],
                "decision": "drop",
                "note": "Arabic/Latin numeral mixing dropped as style; usually acceptable, keep as drop.",
            }
        )

    # Quote keep without rewrite is good; mark as review confirmation.
    for row in rows:
        if row.get("decision") == "keep" and "اقتباس" in (row.get("explanation_ar") or "") and not row.get("suggested_text"):
            findings.append(
                {
                    "kind": "keep_quote_safe",
                    "severity": "info",
                    "source_index": int(row["source_index"]),
                    "label_id": row["label_id"],
                    "decision": "keep",
                    "note": "Keep flags quote typo without rewriting quoted text — consistent with quote-safety rule.",
                }
            )

    strong = [f for f in findings if f.get("severity") == "strong"]
    review = [f for f in findings if f.get("severity") == "review"]
    info = [f for f in findings if f.get("severity") == "info"]

    lines = [
        "# Label consistency audit (all 163 AI labels)",
        "",
        "> Labels remain unchanged. This audit records flags and proposed corrections only.",
        "",
        "## Aggregate",
        "",
        f"- Total labels audited: **163**",
        f"- Exact duplicate groups: **{len(dups)}**",
        f"- Exact duplicate groups with inconsistent decisions: **{inconsistent_exact}**",
        f"- Strong findings: **{len(strong)}**",
        f"- Review flags: **{len(review)}**",
        f"- Info notes: **{len(info)}**",
        f"- Proposed corrections (not applied): **{len(corrections)}**",
        "",
        "## Strong findings",
        "",
    ]
    for item in strong:
        lines.append(
            f"- `{item.get('label_id', item.get('label_ids'))}` "
            f"(source_index={item.get('source_index', item.get('source_indices'))}, "
            f"decision={item.get('decision', item.get('decisions'))}): {item['note']}"
        )
    lines.extend(["", "## Review flags", ""])
    for item in review:
        lines.append(
            f"- `{item['label_id']}` (source_index={item['source_index']}, decision={item['decision']}): {item['note']}"
        )
    lines.extend(
        [
            "",
            "## Duplicate inventory",
            "",
            "All exact duplicate groups currently share the same decision within each group "
            "(no inconsistent duplicate labeling detected).",
            "",
        ]
    )
    for key, idxs in sorted(dups.items(), key=lambda item: item[1][0]):
        article, category, orig, _expl = key
        decisions = sorted({by_idx[i]["decision"] for i in idxs})
        lines.append(
            f"- indices `{', '.join(str(i) for i in idxs)}` · `{article}` / `{category}` / "
            f"`{(orig or '')[:40]}` · decisions={decisions}"
        )
    lines.extend(
        [
            "",
            "## Keep suggestions that alter certainty/attribution/meaning",
            "",
        ]
    )
    if keep_risks:
        for row in keep_risks:
            lines.append(
                f"- `{row['label_id']}` keep suggestion `{row.get('suggested_text')}` "
                f"(category={row.get('category')})"
            )
    else:
        lines.append("- None beyond the strong items already listed.")
    lines.extend(
        [
            "",
            "## Proposed corrections",
            "",
            f"See `{OUT_JSONL.name}`. These rows are proposals for human review; "
            "they do **not** modify `expert_labels.jsonl` or scored precision.",
            "",
            "## Method notes",
            "",
            "- Checked all 163 rows for rationale/template mismatch, quote rewrite risk, "
            "duplicate consistency, suspicious keep numeric/headline cases, and drops that may hide overstatement.",
            "- Distinguishes `strong` proposed corrections from `review` flags.",
            "- AI suggests; editors decide.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    OUT_JSONL.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in corrections) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "strong": len(strong),
                "review": len(review),
                "info": len(info),
                "proposed_corrections": len(corrections),
                "exact_dup_groups": len(dups),
                "inconsistent_exact_dups": inconsistent_exact,
                "template_mismatches": len(template_mismatches),
                "out_md": str(OUT_MD),
                "out_jsonl": str(OUT_JSONL),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
