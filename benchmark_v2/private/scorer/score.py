"""Core scoring logic for benchmark_v2 (gold stays private)."""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Iterable

from benchmark_v2.private.scorer.matching import (
    hits_forbidden,
    score_gold_against_engine,
)
from benchmark_v2.private.scorer.schemas import (
    BenchmarkReport,
    CaseScore,
    EngineCaseOutput,
    EngineFinding,
    GoldCase,
    MatchDetail,
)


MATCH_THRESHOLD = 5.0


def load_gold_cases(gold_dir: Path) -> list[GoldCase]:
    cases: list[GoldCase] = []
    for path in sorted(gold_dir.glob("*.gold.json")):
        cases.append(GoldCase.model_validate_json(path.read_text(encoding="utf-8")))
    return cases


def load_engine_outputs(path: Path) -> dict[str, EngineCaseOutput]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "outputs" in raw:
        raw = raw["outputs"]
    outs: dict[str, EngineCaseOutput] = {}
    for item in raw:
        out = EngineCaseOutput.model_validate(item)
        outs[out.case_id] = out
    return outs


def _safe_div(num: float, den: float, default: float = 0.0) -> float:
    return num / den if den else default


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def score_case(gold: GoldCase, output: EngineCaseOutput) -> CaseScore:
    used: set[int] = set()
    matches: list[MatchDetail] = []
    tp = fn = 0
    critical_hits = critical_total = 0
    unsafe = 0

    clean = bool(gold.metadata.get("clean_case"))
    contains_critical = bool(gold.metadata.get("contains_critical_issue"))

    for gi, gf in enumerate(gold.expected_findings):
        is_critical = bool(gf.critical) or contains_critical
        if is_critical:
            critical_total += 1

        best_score = -999.0
        best_idx: int | None = None
        best_detail: dict | None = None
        for ei, ef in enumerate(output.findings):
            if ei in used:
                continue
            detail = score_gold_against_engine(gf, ef)
            if detail["score"] > best_score:
                best_score = detail["score"]
                best_idx = ei
                best_detail = detail

        if best_detail and best_detail["matched"] and best_idx is not None:
            used.add(best_idx)
            tp += 1
            if is_critical:
                critical_hits += 1
            if not best_detail["suggestion_safe"]:
                unsafe += 1
            matches.append(
                MatchDetail(
                    gold_index=gi,
                    matched=True,
                    engine_index=best_idx,
                    score=best_detail["score"],
                    exact_span=best_detail["exact_span"],
                    partial_span=best_detail["partial_span"],
                    category_match=best_detail["category_match"],
                    severity_band_match=best_detail["severity_band_match"],
                    decision_match=best_detail["decision_match"],
                    explanation_keyword_match=best_detail["explanation_keyword_match"],
                    suggestion_safe=best_detail["suggestion_safe"],
                )
            )
        else:
            fn += 1
            matches.append(
                MatchDetail(
                    gold_index=gi,
                    matched=False,
                    score=max(0.0, best_score) if best_score > -999 else 0.0,
                )
            )

    # False positives: unmatched engine findings + forbidden hits
    unmatched = [i for i in range(len(output.findings)) if i not in used]
    fp = len(unmatched)

    forbidden_hits = 0
    attribution_ok = True
    for fi, ff in enumerate(gold.forbidden_findings):
        for ei in unmatched:
            ef = output.findings[ei]
            if hits_forbidden(ff, ef):
                forbidden_hits += 1
                # Extra FP penalty for forbidden behavior
                fp += 1
                if "quote" in (ff.reason or "").lower() or "attribution" in (
                    ff.reason or ""
                ).lower():
                    attribution_ok = False
                if ef.suggested_text and ef.decision in {"replace", "ban"}:
                    unsafe += 1
                break

    # Clean-case: any finding is FP (already counted as unmatched)
    precision = _safe_div(tp, tp + fp, default=1.0)
    recall = _safe_div(tp, tp + fn, default=1.0)
    suggestion_safety = 1.0 - _safe_div(unsafe, max(1, len(output.findings) or 1))

    return CaseScore(
        case_id=gold.case_id,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        forbidden_hits=forbidden_hits,
        unsafe_suggestions=unsafe,
        attribution_preserved=attribution_ok,
        suggestion_safety=round(max(0.0, suggestion_safety), 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(_f1(precision, recall), 4),
        critical_hits=critical_hits,
        critical_total=critical_total,
        latency_ms=output.latency_ms,
        clean_case=clean,
        matches=matches,
    )


def aggregate_case_scores(
    case_scores: list[CaseScore],
    *,
    run_count: int = 1,
    consistency_score: float | None = None,
    metadata: dict | None = None,
) -> BenchmarkReport:
    tp = sum(c.true_positives for c in case_scores)
    fp = sum(c.false_positives for c in case_scores)
    fn = sum(c.false_negatives for c in case_scores)
    precision = _safe_div(tp, tp + fp, default=1.0)
    recall = _safe_div(tp, tp + fn, default=1.0)

    crit_hits = sum(c.critical_hits for c in case_scores)
    crit_total = sum(c.critical_total for c in case_scores)

    clean_cases = [c for c in case_scores if c.clean_case]
    clean_fp_cases = sum(1 for c in clean_cases if c.false_positives > 0)

    # FPR over all predicted findings
    fpr = _safe_div(fp, tp + fp, default=0.0)

    attr_ok = sum(1 for c in case_scores if c.attribution_preserved)
    sug_safe = statistics.mean([c.suggestion_safety for c in case_scores]) if case_scores else 1.0

    lats = [c.latency_ms for c in case_scores if c.latency_ms is not None]

    return BenchmarkReport(
        total_cases=len(case_scores),
        tp=tp,
        fp=fp,
        fn=fn,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(_f1(precision, recall), 4),
        critical_recall=round(_safe_div(crit_hits, crit_total), 4),
        false_positive_rate=round(fpr, 4),
        clean_case_false_positive_rate=round(
            _safe_div(clean_fp_cases, len(clean_cases)), 4
        ),
        attribution_preservation=round(_safe_div(attr_ok, len(case_scores), default=1.0), 4),
        suggestion_safety=round(sug_safe, 4),
        average_latency_ms=round(statistics.mean(lats), 2) if lats else None,
        consistency_score=None if consistency_score is None else round(consistency_score, 4),
        run_count=run_count,
        cases=case_scores,
        metadata=metadata or {},
    )


def score_outputs(
    *,
    gold_dir: Path,
    outputs: Path | list[EngineCaseOutput] | dict[str, EngineCaseOutput],
) -> BenchmarkReport:
    gold_cases = load_gold_cases(Path(gold_dir))
    if isinstance(outputs, Path):
        outs = load_engine_outputs(outputs)
    elif isinstance(outputs, list):
        outs = {o.case_id: o for o in outputs}
    else:
        outs = outputs

    case_scores = [
        score_case(g, outs.get(g.case_id, EngineCaseOutput(case_id=g.case_id, findings=[])))
        for g in gold_cases
    ]
    return aggregate_case_scores(case_scores)


def _finding_signature(finding: EngineFinding) -> tuple[str, str, str]:
    from benchmark_v2.private.scorer.matching import normalize_text

    return (
        normalize_text(finding.category),
        normalize_text(finding.decision),
        normalize_text(finding.original_text),
    )


def consistency_across_runs(run_outputs: list[dict[str, EngineCaseOutput]]) -> float:
    """Fraction of case finding-signature agreement across runs (Jaccard mean)."""
    if len(run_outputs) < 2:
        return 1.0
    case_ids = sorted({cid for run in run_outputs for cid in run})
    scores: list[float] = []
    for case_id in case_ids:
        sets = []
        for run in run_outputs:
            out = run.get(case_id) or EngineCaseOutput(case_id=case_id, findings=[])
            sets.append({_finding_signature(f) for f in out.findings})
        # Average pairwise Jaccard
        pair_scores = []
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                a, b = sets[i], sets[j]
                if not a and not b:
                    pair_scores.append(1.0)
                else:
                    pair_scores.append(_safe_div(len(a & b), len(a | b)))
        if pair_scores:
            scores.append(statistics.mean(pair_scores))
    return statistics.mean(scores) if scores else 1.0


def score_repeated_runs(
    *,
    gold_dir: Path,
    output_paths: Iterable[Path],
) -> BenchmarkReport:
    """Score each run, average metrics, and attach consistency_score."""
    paths = [Path(p) for p in output_paths]
    reports: list[BenchmarkReport] = []
    run_maps: list[dict[str, EngineCaseOutput]] = []
    for path in paths:
        outs = load_engine_outputs(path)
        run_maps.append(outs)
        reports.append(score_outputs(gold_dir=gold_dir, outputs=outs))

    if not reports:
        return BenchmarkReport()

    consistency = consistency_across_runs(run_maps)

    # Average aggregate metrics; keep last run's case details for inspection.
    def avg(attr: str) -> float:
        vals = [getattr(r, attr) for r in reports]
        return round(statistics.mean(vals), 4)

    lats = [r.average_latency_ms for r in reports if r.average_latency_ms is not None]
    base = reports[-1]
    return BenchmarkReport(
        total_cases=base.total_cases,
        tp=int(round(statistics.mean([r.tp for r in reports]))),
        fp=int(round(statistics.mean([r.fp for r in reports]))),
        fn=int(round(statistics.mean([r.fn for r in reports]))),
        precision=avg("precision"),
        recall=avg("recall"),
        f1=avg("f1"),
        critical_recall=avg("critical_recall"),
        false_positive_rate=avg("false_positive_rate"),
        clean_case_false_positive_rate=avg("clean_case_false_positive_rate"),
        attribution_preservation=avg("attribution_preservation"),
        suggestion_safety=avg("suggestion_safety"),
        average_latency_ms=round(statistics.mean(lats), 2) if lats else None,
        consistency_score=round(consistency, 4),
        run_count=len(reports),
        cases=base.cases,
        metadata={"per_run_f1": [r.f1 for r in reports]},
    )


def write_json_report(report: BenchmarkReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        report.model_dump_json(indent=2, exclude_none=False) + "\n",
        encoding="utf-8",
    )
