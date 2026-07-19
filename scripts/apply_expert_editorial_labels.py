#!/usr/bin/env python3
"""Expert editorial labels for run3 non-punctuation findings (silence-set FP pass).

Writes a SEPARATE artifact; does not modify run3 or source JSONL templates.
Canonical source keys come from the priority JSONL (same 163 IDs as working/src).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "local" / "sprint2" / "non_punctuation_priority_to_label.jsonl"
OUT_DIR = ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3"
OUT_LABELS = OUT_DIR / "expert_labels.jsonl"
OUT_FOR_SCORER = OUT_DIR / "labeled_for_scoring.jsonl"

_LONG_PARA = re.compile(r"مقطع طويل")
_CONFIRMED_VERB = re.compile(r"أكد أن|أكدت أن")
_FIGHTER = re.compile(r"مقاتل")
_VAGUE_SRC = re.compile(r"مصادر")
_MILITIA = re.compile(r"ميليش|مليش")
_DUP_WORD = re.compile(r"تكرار كلمة متجاورة")


def _label_one(row: dict, index: int) -> dict:
    cat = (row.get("category") or "").lower()
    expl = row.get("explanation_ar") or ""
    orig = row.get("original_text") or ""
    sug = row.get("suggested_text")
    headline = row.get("headline") or ""
    body = row.get("body_excerpt") or ""
    fid = row.get("finding_id") or ""

    decision = "uncertain"
    drop_reason = None
    rationale = ""
    confidence = "medium"

    # --- clarity ---
    if cat == "clarity":
        if _LONG_PARA.search(expl):
            decision, drop_reason = "drop", "too_low_impact"
            rationale = "Long-paragraph split preference; no concrete ambiguity."
            confidence = "high"
        elif "عنوان" in expl and sug:
            decision, drop_reason = "drop", "optional_style"
            rationale = "Headline rewrite preference without a concrete comprehension failure."
            confidence = "high"
        elif "غير مكتمل" in expl or "غامض" in expl or "التباس" in expl:
            decision = "keep"
            rationale = "Concrete incompleteness/ambiguity claimed; keep for editor."
            confidence = "medium"
        else:
            decision, drop_reason = "drop", "optional_style"
            rationale = "Clarity suggestion without a specific defect."
            confidence = "medium"

    # --- attribution_strength (mechanical أكد→قال) ---
    elif cat == "attribution_strength":
        decision, drop_reason = "drop", "optional_style"
        rationale = "Confirmation-verb softening is stylistic on published news; low interrupt value."
        confidence = "high"

    # --- attribution (vague sources) ---
    elif cat == "attribution":
        # On silence-set public corpora, vague-source nags are typically FPs for non-AJ outlets.
        # Keep only when finding invents a problem unsupported by text, else drop as optional.
        if _VAGUE_SRC.search(orig) or _VAGUE_SRC.search(expl):
            decision, drop_reason = "drop", "too_low_impact"
            rationale = (
                "Vague-source phrasing is common published journalism; "
                "not a clear defect on silence-set external corpora (not AJ house style)."
            )
            confidence = "high"
        else:
            decision, drop_reason = "drop", "optional_style"
            rationale = "Attribution nag without a demonstrated unsupported factual leap."
            confidence = "medium"

    # --- headline / publisher voice ---
    elif cat in {"headline_body_mismatch", "publisher_voice", "headline_framing"}:
        contradiction_claim = any(k in expl for k in ("يتناقض", "تناقض", "يتعارض", "تضارب"))
        certainty_only = any(
            k in expl
            for k in (
                "مستوى اليقين",
                "تصعيدًا في اليقين",
                "تصعيدا في اليقين",
                "تصعيد في اليقين",
                "ربما",
            )
        ) and not any(
            k in expl
            for k in (
                "موقع",
                "جغراف",
                "هولندا",
                "النمسا",
                "إطلاق سراح",
                "محتجز",
                "انتهت",
                "نفي",
                "نفى",
                "قتل",
            )
        )
        # Truncated body cannot prove unsupported headline claim → uncertain, not keep.
        if "ANAD-336524" in (row.get("label_id") or "") or (
            contradiction_claim and len(body.strip()) < 120 and "لا يحتوي" in expl
        ):
            decision = "uncertain"
            rationale = "Headline claim may be unsupported, but excerpt is too short to adjudicate."
            confidence = "low"
        elif contradiction_claim and certainty_only:
            decision, drop_reason = "drop", "headline_compression"
            rationale = "Certainty/hedging mismatch is ordinary news headline compression, not a material fact conflict."
            confidence = "high"
        elif contradiction_claim:
            decision = "keep"
            rationale = "Material contradiction claimed between headline/body (or internal spans)."
            confidence = "high"
        elif "جديدة كليا" in orig or "جديدة كليا" in expl:
            decision = "keep"
            rationale = "Headline overstates 'entirely new' vs body 'new or updated'."
            confidence = "medium"
        elif cat == "publisher_voice" and ("مصادر" in body or "مصادر" in expl):
            decision, drop_reason = "drop", "headline_compression"
            rationale = "Headline states figure that body attributes; normal news compression."
            confidence = "high"
        elif "إسكات الشائعات" in expl or ("تحليل" in expl and "صوت الناشر" in expl):
            decision = "keep"
            rationale = "Publisher voice presents analysis as fact without attribution."
            confidence = "medium"
        else:
            decision, drop_reason = "drop", "headline_compression"
            rationale = "Ordinary headline compression/angle without material contradiction."
            confidence = "medium"

    # --- entity ---
    elif cat == "entity_name":
        if _FIGHTER.search(orig) or _FIGHTER.search(expl):
            decision, drop_reason = "drop", "incorrect_rule"
            rationale = "مقاتل→عناصر is AJ house-style; not applicable as hard FP on SANAD/ANAD silence set."
            confidence = "high"
        elif "تهجئة غير متسقة" in expl or "طهران" in orig:
            # طهران vs إيران is not always inconsistency — often DROP
            decision, drop_reason = "drop", "acceptable_arabic"
            rationale = "طهران/إيران metonym or dual naming often acceptable; not a clear error."
            confidence = "medium"
        else:
            decision, drop_reason = "drop", "optional_style"
            rationale = "Entity naming preference without clear wrong form."
            confidence = "medium"

    elif cat == "entity_confusion":
        decision = "uncertain"
        drop_reason = None
        rationale = "Possible referent confusion; excerpt insufficient to confirm mix-up."
        confidence = "low"

    # --- loaded framing ---
    elif cat == "loaded_framing":
        # Applying AJ militia rules to external corpora → usually drop for silence FP measurement
        if _MILITIA.search(orig) or _MILITIA.search(expl):
            decision, drop_reason = "drop", "incorrect_rule"
            rationale = (
                "Militia/loaded label rule is AJ house-style policy; "
                "external published copy on silence set should not be treated as FP-worthy by default."
            )
            confidence = "high"
        else:
            decision, drop_reason = "drop", "optional_style"
            rationale = "Framing preference without clear neutrality breach on this corpus."
            confidence = "medium"

    # --- numeric ---
    elif cat == "numeric_contradiction":
        if any(k in expl for k in ("يتعارض", "تناقض", "تضارب")):
            decision = "keep"
            rationale = "Internal numeric contradiction claimed between spans."
            confidence = "high"
        elif "يجب التحقق" in expl or "article_context.numbers" in expl:
            decision = "uncertain"
            rationale = "Model cites context numbers needing verification; not proven from excerpt."
            confidence = "low"
        else:
            decision = "uncertain"
            rationale = "Numeric issue not fully verifiable from supplied excerpt."
            confidence = "low"

    # --- spelling ---
    elif cat == "spelling":
        if "مليشيات" in orig and sug and "ميليشيات" in str(sug):
            decision, drop_reason = "drop", "acceptable_arabic"
            rationale = "مليشيات/ميليشيات both attested; optional orthography."
            confidence = "high"
        elif "اقتباس" in expl and (sug is None or sug == ""):
            decision = "keep"
            rationale = "Flags possible typo inside quote without rewriting quote — useful editor note."
            confidence = "medium"
        elif "استبدال إملائي معروف" in expl:
            # dictionary replacements can be house-style
            decision, drop_reason = "drop", "optional_style"
            rationale = "Known-replacement lexicon hit; often optional on external corpora."
            confidence = "medium"
        else:
            decision = "keep"
            rationale = "Apparent orthographic error with concrete correction."
            confidence = "medium"

    # --- unsupported certainty ---
    elif cat == "unsupported_certainty":
        if "توقع" in expl or "ستاندرد" in expl or "يتجاوز" in orig:
            decision = "keep"
            rationale = "Headline presents forecast/claim as settled fact vs hedged body."
            confidence = "high"
        else:
            decision, drop_reason = "drop", "headline_compression"
            rationale = "Certainty/attribution nuance often acceptable headline compression."
            confidence = "medium"

    # --- repetition ---
    elif cat == "repetition":
        if _DUP_WORD.search(expl) or re.search(r"^(\S+) \1$", orig.strip()):
            decision = "keep"
            rationale = "Objective adjacent duplicate word."
            confidence = "high"
        elif "تكرار غير ضروري للجملة" in expl:
            decision, drop_reason = "drop", "optional_style"
            rationale = "Lead/headline echo is common news structure, not a hard error."
            confidence = "high"
        else:
            decision = "keep"
            rationale = "Repetition finding appears objective."
            confidence = "medium"

    # --- consistency ---
    elif cat == "consistency":
        if "تضارب في اسم" in expl or "يُشار إليه" in expl:
            decision = "keep"
            rationale = "Name inconsistency across article is editorially actionable."
            confidence = "high"
        else:
            decision = "uncertain"
            rationale = "Consistency claim needs fuller article text."
            confidence = "low"

    # --- grammar ---
    elif cat == "grammar":
        if "غير مكتمل" in expl or "…" in orig or "..." in orig:
            decision = "keep"
            rationale = "Incomplete sentence/truncated is a concrete defect."
            confidence = "medium"
        else:
            decision = "uncertain"
            rationale = "Grammar claim not fully checkable from excerpt."
            confidence = "low"

    else:
        decision = "uncertain"
        rationale = f"Unmapped category '{cat}' — insufficient policy mapping."
        confidence = "low"

    # Safety: drops must have reasons
    if decision == "drop" and not drop_reason:
        drop_reason = "other"

    label = {
        "source_index": index,
        "label_id": row.get("label_id"),
        "article_id": row.get("article_id"),
        "finding_id": row.get("finding_id"),
        "category": row.get("category"),
        "fp_family": row.get("fp_family"),
        "severity": row.get("severity"),
        "original_text": row.get("original_text"),
        "suggested_text": row.get("suggested_text"),
        "explanation_ar": row.get("explanation_ar"),
        "headline": row.get("headline"),
        "body_excerpt": row.get("body_excerpt"),
        "confidence_engine": row.get("confidence"),
        "decision": decision,
        "drop_reason": drop_reason,
        "rationale": rationale,
        "editor_notes": rationale,
        "label_confidence": confidence,
        "labeler": "cursor_expert_silence_fp_v1",
        "source_file": str(SOURCE.as_posix()),
    }
    return label


def main() -> int:
    rows = [
        json.loads(line)
        for line in SOURCE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 163, f"expected 163, got {len(rows)}"

    labels = [_label_one(row, i) for i, row in enumerate(rows)]
    assert len(labels) == 163
    assert all(l["decision"] in {"keep", "drop", "uncertain"} for l in labels)
    assert all(l["decision"] != "drop" or l.get("drop_reason") for l in labels)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_LABELS.open("w", encoding="utf-8") as fh:
        for lab in labels:
            fh.write(json.dumps(lab, ensure_ascii=False) + "\n")

    # Scorer-compatible merge: source fields + decision fields
    with OUT_FOR_SCORER.open("w", encoding="utf-8") as fh:
        for row, lab in zip(rows, labels):
            merged = dict(row)
            merged["decision"] = lab["decision"]
            merged["drop_reason"] = lab["drop_reason"]
            merged["rationale"] = lab["rationale"]
            merged["editor_notes"] = lab["editor_notes"]
            merged["label_confidence"] = lab["label_confidence"]
            merged["labeler"] = lab["labeler"]
            fh.write(json.dumps(merged, ensure_ascii=False) + "\n")

    from collections import Counter

    c = Counter(l["decision"] for l in labels)
    print(json.dumps({"n": len(labels), "decisions": dict(c), "out": str(OUT_LABELS)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
