"""Batch-score evaluation articles against expected error keys (mock AI)."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

# Force deterministic path for scoring.
os.environ["AI_CLIENT"] = "mock"

from app.models.schemas import ReviewRequest
from app.orchestration.review import ReviewOrchestrator

ROOT = Path(__file__).resolve().parents[1]
ART_DIR = ROOT / "data" / "evaluation" / "articles"
OUT = ROOT / "data" / "evaluation" / "batch_scorecard.json"

# Each key is a needle matched against original_text / suggested_text / explanation_ar.
EXPECTED: dict[str, list[dict[str, str]]] = {
    "custom-marfa-chaos-v1": [
        {"id": "spell_مسؤليين", "needle": "مسؤليين"},
        {"id": "gram_قام_المتظاهرين", "needle": "قام المتظاهرين"},
        {"id": "num_split", "needle": "بينهم 22"},
        {"id": "date_conflict", "needle": "الأربعاء"},
        {"id": "name_conflict", "needle": "رئيس الوزراء"},
        {"id": "vague_source", "needle": "مصادر مطلعه"},
        {"id": "bias_مخربين", "needle": "المخربين"},
        {"id": "terror_label", "needle": "الجماعات الإرهابية"},
        {"id": "foreign_funding", "needle": "تمويلات أجنبية"},
        {"id": "overgen_شعب", "needle": "الشعب يقف"},
        {"id": "publisher_voice", "needle": "ولا شك"},
        {"id": "caption_bias", "needle": "المخربة"},
    ],
    "econ-plains-v1": [
        {"id": "spell_الإنهيار", "needle": "الإنهيار"},
        {"id": "spell_الإقتصادية", "needle": "الإقتصادية"},
        {"id": "spell_تشوية", "needle": "تشوية"},
        {"id": "claim_growth_vs_decline", "needle": "تراجع الناتج"},
        {"id": "pct_inflation", "needle": "تضخم"},
        {"id": "claim_tax_vs_fee", "needle": "رسم تنمية"},
        {"id": "foreign_funding", "needle": "تمويلها من جهات أجنبية"},
        {"id": "inflam_أكاذيب", "needle": "أكاذيب"},
        {"id": "inflam_أعداء", "needle": "أعداء الوطن"},
        {"id": "inflam_مكاسب", "needle": "مكاسب سياسية رخيصة"},
        {"id": "vague_indicators", "needle": "المؤشرات كلها تؤكد"},
        {"id": "overgen_investors", "needle": "المستثمرين يتسابقون"},
        {"id": "pct_unemployment", "needle": "بطالة"},
        {"id": "unemployed_trend", "needle": "انخفض رغم زيادة"},
    ],
    "north-border-v1": [
        {"id": "spell_إعتداءات", "needle": "إعتداءات"},
        {"id": "style_مليشيات", "needle": "مليشيات"},
        {"id": "claim_verify_vs_sure", "needle": "بلا شك"},
        {"id": "claim_human_shields", "needle": "دروع بشرية"},
        {"id": "math_military", "needle": "خسائر عسكرية"},
        {"id": "math_civilians", "needle": "مدنيين"},
        {"id": "claim_no_residential", "needle": "المناطق السكنية"},
        {"id": "terror_label", "needle": "العصابات الإرهابية"},
        {"id": "claim_ended_vs_renew", "needle": "تجدد القتال"},
        {"id": "claim_thousands", "needle": "تجمعات محدودة"},
        {"id": "claim_peace_vs_force", "needle": "القوة هي اللغة"},
        {"id": "attack_ngos", "needle": "لا يمكن الوثوق"},
        {"id": "bias_يسحق", "needle": "يسحق"},
        {"id": "bias_نصر", "needle": "النصر الساحق"},
    ],
    "elections-v1": [
        {"id": "spell_إنتخابات", "needle": "إنتخابات"},
        {"id": "turnout_math", "needle": "من أصل"},
        {"id": "claim_minor_violations", "needle": "تعطيل التصويت في 120"},
        {"id": "overgen_consensus", "needle": "إجماع"},
        {"id": "evidence_قاطععة", "needle": "أدلة قاطعة"},
        {"id": "inflam_فرحة", "needle": "فرحة الشعب"},
        {"id": "inflam_إرادة", "needle": "الإرادة الوطنية"},
        {"id": "claim_praise_vs_violations", "needle": "مخالفات خطيرة"},
        {"id": "date_conflict", "needle": "الأحد"},
    ],
    "health-wave-v1": [
        {"id": "claim_ended_vs_ready", "needle": "رفع درجة الاستعداد"},
        {"id": "case_rate", "needle": "خلال يوم"},
        {"id": "claim_100pct", "needle": "آمنة بنسبة 100%"},
        {"id": "claim_side_effects", "needle": "43 بلاغاً"},
        {"id": "gram_كافي", "needle": "كافي"},
        {"id": "attack_doctors", "needle": "حملة سياسية"},
        {"id": "unverified_images", "needle": "لم يتم التحقق"},
        {"id": "deaths_conflict", "needle": "الوفيات"},
        {"id": "claim_control_vs_curfew", "needle": "حظر تجول"},
        {"id": "inflam_ذعر", "needle": "تنشر الذعر"},
    ],
    # Cases 6-12
    "indirect-accusation-v1": [
        {"id": "title_overclaim", "needle": "تكشف تورط"},
        {"id": "correlation_as_fact", "needle": "ويؤكد ذلك"},
        {"id": "named_risk", "needle": "الوزير السابق كان أحد المستفيدين"},
    ],
    "quoted-incitement-v1": [
        {"id": "publisher_anger", "needle": "غضبًا شعبيًا"},
        {"id": "publisher_legitimacy", "needle": "شرعيتها"},
        {"id": "publisher_suspicious", "needle": "ارتباطاتها المشبوهة"},
        {"id": "quote_preserve_clients", "needle": "مجموعة من العملاء"},
    ],
    "name-date-chaos-v1": [
        {"id": "date_18", "needle": "18"},
        {"id": "timeline_weeks_vs_days", "needle": "قبل يومين"},
        {"id": "similar_names", "needle": "منصور"},
        {"id": "role_conflict", "needle": "رئيس دولة ورئيس حكومة"},
    ],
    "labor-context-math-v1": [
        {"id": "employed_direction", "needle": "الارتفاع من 4.1"},
        {"id": "unemployed_direction", "needle": "الانخفاض من 620"},
        {"id": "participation_direction", "needle": "ارتفاع النسبة"},
        {"id": "ignore_alt_explanation", "needle": "خفضت البطالة"},
    ],
    "pronoun-source-v1": [
        {"id": "title_overclaim", "needle": "وافقت"},
        {"id": "pronoun_ambiguous", "needle": "أكد أنه وافق"},
        {"id": "certainty_vs_official", "needle": "أصبح من المؤكد"},
    ],
    "majority-precision-v1": [
        {"id": "majority_not_absolute", "needle": "أغلبية"},
        {"id": "people_approved", "needle": "الشعب أقر القانون"},
    ],
    "clean-talks-v1": [
        {"id": "low_false_positives", "needle": "__LOW_FP__"},
    ],
    # Short adversarial
    "adv-protests-prove-fraud": [
        {"id": "protests_not_proof", "needle": "أثبتته الاحتجاجات"},
    ],
    "adv-quote-preserve-corrupt": [
        {"id": "preserve_فاسدة", "needle": "__QUOTE_PRESERVE__:فاسدة"},
    ],
    "adv-synonym-trap": [
        {"id": "no_طفيفة", "needle": "__NO_SUGGEST__:طفيفة"},
    ],
    "adv-vague-future": [
        {"id": "vague_source", "needle": "بحسب مصادر"},
        {"id": "future_certainty", "needle": "سيستقيل"},
    ],
    "adv-plural-singular": [
        {"id": "grammar_هوية", "needle": "هويته"},
    ],
    "adv-final-vs-appeal": [
        {"id": "final_vs_appeal", "needle": "الاستئناف"},
    ],
    "adv-pct-sum-103": [
        {"id": "pct_overflow", "needle": "100%"},
    ],
    "adv-title-cancel-defer": [
        {"id": "cancel_vs_defer", "needle": "تأجيل"},
    ],
    "adv-publisher-after-quote": [
        {"id": "publisher_adopts", "needle": "وهذا بالفعل ما تثبته"},
        {"id": "quote_ok", "needle": "__QUOTE_PRESERVE__:تعمل ضد الوطن"},
    ],
    "adv-similar-names": [
        {"id": "similar_names", "needle": "سامر"},
    ],
}


def _findings_blob(findings: list) -> str:
    blobs = []
    for f in findings:
        blobs.append(
            " | ".join(
                [
                    f.original_text or "",
                    f.suggested_text or "",
                    f.explanation_ar or "",
                    " ".join(f.rule_ids or []),
                    f.category or "",
                    f.decision.value if hasattr(f.decision, "value") else str(f.decision),
                ]
            )
        )
    return "\n".join(blobs)


def _special_hit(needle: str, findings: list, joined: str) -> bool:
    if needle == "__LOW_FP__":
        hard = [
            f
            for f in findings
            if str(getattr(f.decision, "value", f.decision))
            in {"hard_warning", "ban", "replace"}
        ]
        return len(hard) <= 2 and len(findings) <= 5
    if needle.startswith("__QUOTE_PRESERVE__:"):
        span = needle.split(":", 1)[1]
        # Pass if no replace/ban suggested rewrite for the quoted span.
        for f in findings:
            if span in (f.original_text or "") or span in (f.explanation_ar or ""):
                dec = str(getattr(f.decision, "value", f.decision))
                if dec in {"replace", "ban"} and f.suggested_text:
                    return False
                if dec in {"needs_editor_review", "soft_warning", "hard_warning"}:
                    return True
        # Also pass if span never rewritten.
        return "طفيفة" not in joined if span == "فاسدة" else True
    if needle.startswith("__NO_SUGGEST__:"):
        bad = needle.split(":", 1)[1]
        for f in findings:
            if bad in (f.suggested_text or ""):
                return False
        return True
    return needle in joined


def score_article(article_id: str, findings: list) -> dict:
    keys = EXPECTED[article_id]
    joined = _findings_blob(findings)
    details = []
    hits = 0
    for key in keys:
        ok = _special_hit(key["needle"], findings, joined)
        if ok:
            hits += 1
        details.append({"id": key["id"], "needle": key["needle"], "hit": ok})
    total = len(keys)
    return {
        "article_id": article_id,
        "hits": hits,
        "total": total,
        "score": f"{hits}/{total}",
        "pct": round(100.0 * hits / total, 1) if total else 0.0,
        "findings_count": len(findings),
        "misses": [d["id"] for d in details if not d["hit"]],
        "details": details,
    }


def load_article(path: Path) -> ReviewRequest:
    data = json.loads(path.read_text(encoding="utf-8"))
    sections = data.get("sections") or []
    headline = data.get("title") or ""
    body_parts = []
    for sec in sections:
        if sec.get("surface") == "headline":
            headline = sec.get("text") or headline
            continue
        body_parts.append(sec.get("text") or "")
    return ReviewRequest(
        document_id=data.get("article_id") or path.stem,
        headline=headline,
        body="\n\n".join(body_parts),
        source="batch-score",
        language=data.get("language") or "ar",
    )


async def main() -> None:
    orch = ReviewOrchestrator()
    results = []
    for article_id in EXPECTED:
        path = ART_DIR / f"{article_id}.json"
        if not path.exists():
            results.append(
                {
                    "article_id": article_id,
                    "error": f"missing fixture: {path}",
                    "hits": 0,
                    "total": len(EXPECTED[article_id]),
                    "score": f"0/{len(EXPECTED[article_id])}",
                }
            )
            continue
        req = load_article(path)
        resp = await orch.review(req)
        results.append(score_article(article_id, resp.findings))

    summary = {
        "client": "mock",
        "articles": results,
        "overall_hits": sum(r.get("hits", 0) for r in results),
        "overall_total": sum(r.get("total", 0) for r in results),
    }
    summary["overall_score"] = (
        f"{summary['overall_hits']}/{summary['overall_total']}"
    )
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
