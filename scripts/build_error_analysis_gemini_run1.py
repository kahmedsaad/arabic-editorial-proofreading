"""Phase A: structured error analysis for Gemini run1 (read-only vs gold).

Does not modify engine, prompts, rules, cases, gold, or scorer.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark_v2.private.scorer.matching import (
    normalize_text,
    partial_span_match,
    score_gold_against_engine,
)
from benchmark_v2.private.scorer.schemas import (
    EngineCaseOutput,
    EngineFinding,
    GoldCase,
)
from benchmark_v2.private.scorer.score import score_case

RESULTS = ROOT / "benchmark_v2" / "results"
GOLD = ROOT / "benchmark_v2" / "private" / "gold"

# Soft taxonomy aliases: engine category → gold-compatible families
CATEGORY_ALIASES: dict[str, set[str]] = {
    "consistency": {
        "numeric_contradiction",
        "headline_body_mismatch",
        "claim_contradiction",
        "temporal_contradiction",
        "legal_contradiction",
        "majority_precision",
        "cross_paragraph_contradiction",
        "nuanced_contradiction",
    },
    "attribution": {
        "attribution",
        "attribution_strength",
        "source_quality",
        "source_misrepresentation",
    },
    "publisher_voice": {"publisher_voice", "headline_framing", "caption_framing"},
    "unsupported_certainty": {"unsupported_certainty", "certainty_escalation"},
    "quote_voice": {"quote_voice", "caption_framing"},
    "entity_confusion": {
        "entity_confusion",
        "temporal_entity_status",
        "pronoun_ambiguity",
    },
}


PROBLEM_TYPES = [
    "true_missed_issue",
    "real_false_positive",
    "duplicate_finding",
    "correct_wrong_category",
    "correct_wrong_span",
    "correct_wrong_severity",
    "scorer_mismatch",
    "unsafe_or_attribution_changing",
    "unnecessary_warning_clean_or_acceptable",
]


def _load_outputs(path: Path) -> dict[str, dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw["outputs"] if isinstance(raw, dict) else raw
    return {o["case_id"]: o for o in items}


def _to_engine_findings(raw_findings: list[dict]) -> list[EngineFinding]:
    out: list[EngineFinding] = []
    for f in raw_findings:
        out.append(
            EngineFinding(
                category=str(f.get("category") or "unknown"),
                decision=str(f.get("decision") or "needs_editor_review"),
                severity=str(f.get("severity") or "medium"),
                original_text=str(f.get("original_text") or ""),
                suggested_text=f.get("suggested_text"),
                explanation_ar=str(f.get("explanation_ar") or ""),
                segment_zone=str(f.get("segment_zone") or "body"),
                confidence=float(f.get("confidence") or 0.0),
            )
        )
    return out


def _categories_compatible(engine_cat: str, gold_cat: str) -> bool:
    ec, gc = normalize_text(engine_cat), normalize_text(gold_cat)
    if ec == gc:
        return True
    for base, aliases in CATEGORY_ALIASES.items():
        if ec == normalize_text(base) and gc in {normalize_text(a) for a in aliases}:
            return True
        if gc == normalize_text(base) and ec in {normalize_text(a) for a in aliases}:
            return True
    return False


def _severity_band_ok(engine_sev: str, band: list[str]) -> bool:
    if not band:
        return True
    return normalize_text(engine_sev) in {normalize_text(s) for s in band}


def classify_case(gold: GoldCase, raw_out: dict) -> dict:
    findings_raw = list(raw_out.get("findings") or [])
    engine_findings = _to_engine_findings(findings_raw)
    output = EngineCaseOutput(
        case_id=gold.case_id,
        findings=engine_findings,
        latency_ms=raw_out.get("latency_ms"),
    )
    scored = score_case(gold, output)
    used_engine: set[int] = {
        m.engine_index
        for m in scored.matches
        if m.matched and m.engine_index is not None
    }

    problems: list[dict] = []
    # Misses / near-misses on gold
    for m in scored.matches:
        gf = gold.expected_findings[m.gold_index]
        if m.matched:
            continue
        # Look for best near miss among unused findings
        best = None
        best_score = -1.0
        for ei, ef in enumerate(engine_findings):
            detail = score_gold_against_engine(gf, ef)
            if detail["score"] > best_score:
                best_score = detail["score"]
                best = (ei, ef, detail)
        if best and best[2]["partial_span"] and not best[2]["category_match"]:
            problems.append(
                {
                    "problem_type": "correct_wrong_category",
                    "gold_category": gf.category,
                    "engine_category": best[1].category,
                    "engine_source": findings_raw[best[0]].get("source"),
                    "span": best[1].original_text,
                    "notes": "span overlaps gold but category differs",
                }
            )
        elif best and best[2]["category_match"] and not (
            best[2]["exact_span"] or best[2]["partial_span"]
        ):
            problems.append(
                {
                    "problem_type": "correct_wrong_span",
                    "gold_category": gf.category,
                    "engine_category": best[1].category,
                    "engine_source": findings_raw[best[0]].get("source"),
                    "span": best[1].original_text,
                    "notes": "category matches but span weak",
                }
            )
        elif best and best[2]["category_match"] and best[2]["partial_span"] and not best[2]["severity_band_match"]:
            problems.append(
                {
                    "problem_type": "correct_wrong_severity",
                    "gold_category": gf.category,
                    "engine_category": best[1].category,
                    "engine_source": findings_raw[best[0]].get("source"),
                    "span": best[1].original_text,
                    "notes": f"severity={best[1].severity} band={gf.severity_band}",
                }
            )
        elif best and best_score >= 4 and _categories_compatible(best[1].category, gf.category):
            problems.append(
                {
                    "problem_type": "scorer_mismatch",
                    "gold_category": gf.category,
                    "engine_category": best[1].category,
                    "engine_source": findings_raw[best[0]].get("source"),
                    "span": best[1].original_text,
                    "notes": "conceptually close; taxonomy/scorer strictness likely",
                }
            )
        else:
            problems.append(
                {
                    "problem_type": "true_missed_issue",
                    "gold_category": gf.category,
                    "engine_category": None,
                    "engine_source": None,
                    "span": (gf.required_span_any or [""])[0],
                    "notes": "no adequate engine finding",
                }
            )

    # Unmatched engine findings → FP / duplicate / unnecessary
    # Detect duplicates among engine findings
    seen_spans: dict[str, int] = {}
    for ei, ef in enumerate(engine_findings):
        key = normalize_text(ef.original_text)
        src = str(findings_raw[ei].get("source") or "unknown")
        zone = ef.segment_zone
        if ei in used_engine:
            # check duplicate of another matched finding
            if key in seen_spans and seen_spans[key] != ei:
                problems.append(
                    {
                        "problem_type": "duplicate_finding",
                        "gold_category": None,
                        "engine_category": ef.category,
                        "engine_source": src,
                        "span": ef.original_text,
                        "segment_zone": zone,
                        "notes": "duplicate span among findings",
                    }
                )
            seen_spans.setdefault(key, ei)
            continue

        # unused
        if key in seen_spans:
            problems.append(
                {
                    "problem_type": "duplicate_finding",
                    "gold_category": None,
                    "engine_category": ef.category,
                    "engine_source": src,
                    "span": ef.original_text,
                    "segment_zone": zone,
                    "notes": "duplicate of earlier finding",
                }
            )
            continue

        # Near gold with alias category?
        near_gold = False
        for gf in gold.expected_findings:
            ok, ratio = partial_span_match(gf.required_span_any, ef.original_text)
            if ok and ratio >= 0.5 and _categories_compatible(ef.category, gf.category):
                near_gold = True
                problems.append(
                    {
                        "problem_type": "scorer_mismatch",
                        "gold_category": gf.category,
                        "engine_category": ef.category,
                        "engine_source": src,
                        "span": ef.original_text,
                        "segment_zone": zone,
                        "notes": "unmatched by scorer but compatible category+span",
                    }
                )
                break
        if near_gold:
            continue

        if not scored.attribution_preserved and src == "gemini":
            problems.append(
                {
                    "problem_type": "unsafe_or_attribution_changing",
                    "gold_category": None,
                    "engine_category": ef.category,
                    "engine_source": src,
                    "span": ef.original_text,
                    "segment_zone": zone,
                    "notes": "attribution preservation failed on case",
                }
            )
            continue

        if gold.metadata.get("clean_case"):
            problems.append(
                {
                    "problem_type": "unnecessary_warning_clean_or_acceptable",
                    "gold_category": None,
                    "engine_category": ef.category,
                    "engine_source": src,
                    "span": ef.original_text,
                    "segment_zone": zone,
                    "notes": "finding on clean case",
                }
            )
        else:
            problems.append(
                {
                    "problem_type": "real_false_positive",
                    "gold_category": None,
                    "engine_category": ef.category,
                    "engine_source": src,
                    "span": ef.original_text,
                    "segment_zone": zone,
                    "decision": ef.decision,
                    "severity": ef.severity,
                    "notes": "unmatched engine finding",
                }
            )
        seen_spans.setdefault(key, ei)

    if scored.unsafe_suggestions:
        problems.append(
            {
                "problem_type": "unsafe_or_attribution_changing",
                "gold_category": None,
                "engine_category": None,
                "engine_source": None,
                "span": None,
                "notes": f"unsafe_suggestions={scored.unsafe_suggestions}",
            }
        )

    return {
        "case_id": gold.case_id,
        "clean_case": bool(gold.metadata.get("clean_case")),
        "critical": bool(gold.metadata.get("contains_critical_issue")),
        "tags": list(gold.metadata.get("tags") or []),
        "tp": scored.true_positives,
        "fp": scored.false_positives,
        "fn": scored.false_negatives,
        "attribution_preserved": scored.attribution_preserved,
        "suggestion_safety": scored.suggestion_safety,
        "finding_sources": Counter(
            str(f.get("source") or "unknown") for f in findings_raw
        ),
        "problems": problems,
    }


def aggregate(cases: list[dict]) -> dict:
    by_type = Counter()
    by_source = Counter()
    by_category = Counter()
    by_severity = Counter()
    by_decision = Counter()
    by_zone = Counter()
    by_case_type = Counter()
    fp_causes = Counter()
    fn_causes = Counter()

    for case in cases:
        case_type = "clean" if case["clean_case"] else ("critical" if case["critical"] else "standard")
        for p in case["problems"]:
            pt = p["problem_type"]
            by_type[pt] += 1
            src = p.get("engine_source") or "n/a"
            by_source[f"{pt}|{src}"] += 1
            if p.get("engine_category"):
                by_category[f"{pt}|{p['engine_category']}"] += 1
            if p.get("severity"):
                by_severity[f"{pt}|{p['severity']}"] += 1
            if p.get("decision"):
                by_decision[f"{pt}|{p['decision']}"] += 1
            if p.get("segment_zone"):
                by_zone[f"{pt}|{p['segment_zone']}"] += 1
            by_case_type[f"{pt}|{case_type}"] += 1
            if pt in {
                "real_false_positive",
                "unnecessary_warning_clean_or_acceptable",
                "duplicate_finding",
            }:
                fp_causes[p.get("engine_category") or pt] += 1
            if pt == "true_missed_issue":
                fn_causes[p.get("gold_category") or "unknown"] += 1

    return {
        "problem_type_counts": dict(by_type.most_common()),
        "by_source": dict(by_source.most_common(40)),
        "by_category": dict(by_category.most_common(40)),
        "by_severity": dict(by_severity.most_common(20)),
        "by_decision": dict(by_decision.most_common(20)),
        "by_zone": dict(by_zone.most_common(20)),
        "by_case_type": dict(by_case_type.most_common(20)),
        "top5_false_positive_causes": dict(fp_causes.most_common(5)),
        "top5_false_negative_causes": dict(fn_causes.most_common(5)),
    }


def fairness_sample(cases: list[dict]) -> dict:
    fps = []
    fns = []
    cats = []
    for case in cases:
        for p in case["problems"]:
            row = {"case_id": case["case_id"], **p}
            if p["problem_type"] == "real_false_positive" and len(fps) < 10:
                fps.append(row)
            if p["problem_type"] == "true_missed_issue" and len(fns) < 10:
                fns.append(row)
            if p["problem_type"] in {"correct_wrong_category", "scorer_mismatch"} and len(cats) < 5:
                cats.append(row)
    return {
        "manual_review_false_positives_sample": fps,
        "manual_review_false_negatives_sample": fns,
        "manual_review_category_mismatch_sample": cats,
        "guidance": (
            "Review samples for genuine wrongness vs unfair scorer taxonomy. "
            "Do not change gold to inflate scores."
        ),
    }


def render_html(payload: dict) -> str:
    agg = payload["aggregates"]
    rows = []
    for case in payload["cases"]:
        probs = "<br/>".join(
            escape(f"{p['problem_type']}: {p.get('span') or ''} ({p.get('notes')})")
            for p in case["problems"][:8]
        )
        rows.append(
            "<tr>"
            f"<td>{escape(case['case_id'])}</td>"
            f"<td>{case['tp']}/{case['fp']}/{case['fn']}</td>"
            f"<td>{'clean' if case['clean_case'] else ('critical' if case['critical'] else 'std')}</td>"
            f"<td>{probs}</td>"
            "</tr>"
        )
    top_fp = "".join(
        f"<li>{escape(k)}: {v}</li>" for k, v in agg["top5_false_positive_causes"].items()
    )
    top_fn = "".join(
        f"<li>{escape(k)}: {v}</li>" for k, v in agg["top5_false_negative_causes"].items()
    )
    types = "".join(
        f"<li>{escape(k)}: {v}</li>" for k, v in agg["problem_type_counts"].items()
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>error analysis gemini run1</title>
<style>
body{{font-family:Georgia,serif;margin:2rem;background:#f7f4ef;color:#1c1a17}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
.card{{background:#fff;border:1px solid #ddd4c6;border-radius:8px;padding:1rem}}
table{{width:100%;border-collapse:collapse;margin-top:1rem;background:#fff}}
th,td{{border:1px solid #e2d8cb;padding:.45rem;vertical-align:top;font-size:.9rem}}
th{{background:#efe7db}}
</style></head><body>
<h1>Error analysis — Gemini run1</h1>
<p>Read-only analysis. Engine/prompt/gold/scorer unchanged.</p>
<div class="grid">
<div class="card"><h3>Problem types</h3><ul>{types}</ul></div>
<div class="card"><h3>Top 5 FP causes</h3><ul>{top_fp}</ul>
<h3>Top 5 FN causes</h3><ul>{top_fn}</ul></div>
</div>
<table><thead><tr><th>Case</th><th>TP/FP/FN</th><th>Type</th><th>Problems</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</body></html>"""


def main() -> int:
    outputs = _load_outputs(RESULTS / "engine_outputs_gemini_run1.json")
    cases = []
    for gp in sorted(GOLD.glob("*.gold.json")):
        gold = GoldCase.model_validate_json(gp.read_text(encoding="utf-8"))
        raw = outputs.get(gold.case_id, {"case_id": gold.case_id, "findings": []})
        case = classify_case(gold, raw)
        case["finding_sources"] = dict(case["finding_sources"])
        cases.append(case)

    payload = {
        "benchmark_id": "benchmark_v2",
        "run": "engine_outputs_gemini_run1",
        "aggregates": aggregate(cases),
        "fairness_sample": fairness_sample(cases),
        "cases": cases,
    }
    json_path = RESULTS / "error_analysis_gemini_run1.json"
    html_path = RESULTS / "error_analysis_gemini_run1.html"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_html(payload), encoding="utf-8")
    print(json.dumps({"wrote": [str(json_path), str(html_path)], "aggregates": payload["aggregates"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
