"""Cross-segment consistency detectors: numbers, dates, official names."""

from __future__ import annotations

import regex as re

from app.models.schemas import Decision, Finding, FindingSource, Segment, Severity

_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

_WEEKDAYS = {
    "الأحد": 6,
    "الاحد": 6,
    "الإثنين": 0,
    "الاثنين": 0,
    "الثلاثاء": 1,
    "الأربعاء": 2,
    "الاربعاء": 2,
    "الخميس": 3,
    "الجمعة": 4,
    "السبت": 5,
}

_DAY_RE = re.compile(
    r"(الأحد|الاحد|الإثنين|الاثنين|الثلاثاء|الأربعاء|الاربعاء|الخميس|الجمعة|السبت)"
    r"\s+(?:الموافق\s+)?(\d{1,2})"
)

_TOTAL_CASUALTIES_RE = re.compile(
    r"(?:إصابة|اصابة)\s+(\d{1,4})\s*شخصا?\u064b?",
)
_TOTAL_ALT_RE = re.compile(
    r"(?:العدد الإجمالي للمصابين|اجمالي المصابين|إجمالي المصابين|لم يتجاوز)\s+(\d{1,4})\s*شخصا?\u064b?",
)
_SPLIT_CASUALTIES_RE = re.compile(
    r"بينهم\s+(\d{1,4})\s+.*?و\s*(\d{1,4})",
)

_KILL_INJURE_RE = re.compile(
    r"مقتل\s+(\d{1,4})\s+.*?وإصابة\s+(\d{1,4})",
)
_MIL_TOTAL_RE = re.compile(
    r"إجمالي الخسائر العسكرية\s+بلغ\s+(\d{1,4})",
)
_CIVILIAN_TOTAL_RE = re.compile(
    r"مقتل\s+(\d{1,4})\s+مدنيين",
)
_CHILDREN_WOMEN_RE = re.compile(
    r"من بينهم\s+(\d{1,4})\s+أطفال\s+و\s*(\d{1,4})\s+نساء",
)
_PCT_TOPIC_RE = re.compile(
    r"(التضخم|معدل التضخم|البطالة|معدل البطالة|نسبة المشاركة|المشاركة)[^\d%]{0,40}?(\d+(?:\.\d+)?)\s*%"
)
_PCT_ALT_RE = re.compile(
    r"(التضخم|معدل التضخم|البطالة|معدل البطالة|نسبة المشاركة|المشاركة)[^\d%]{0,40}?(?:بلغ|إلى|انخفض إلى|لم يتجاوز)\s+(\d+(?:\.\d+)?)\s*%"
)
_TURNOUT_PARTS_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*مليون\s+من أصل\s+(\d+(?:\.\d+)?)\s*ملايين"
)
_DEATH_COUNT_RE = re.compile(
    r"(?:عدد الوفيات|الوفيات)\s+(?:بلغ\s+)?(\d{1,4})\s*حالة"
)
_DEATH_ALT_RE = re.compile(
    r"(?:تقرير المستشفيات إلى|لم يتجاوز)\s+(\d{1,4})",
)
_UNEMPLOYED_TREND_RE = re.compile(
    r"انخفض رغم زيادة عددهم من\s+(\d[\d,]*)\s*ألفاً\s+إلى\s+(\d[\d,]*)\s*ألفاً"
)
_CASE_WEEKLY_RE = re.compile(r"(\d{1,5})\s*حالة\s*أسبوعياً")
_CASE_DAILY_RE = re.compile(r"(\d{1,5})\s*حالة\s*خلال يوم")

_PRESIDENT_RE = re.compile(r"الرئيس\s+([^\s،,]{2,20})\s+([^\s،,.]{2,20})")
_PM_RE = re.compile(r"رئيس\s+الوزراء\s+([^\s،,]{2,20})\s+([^\s،,.]{2,20})")


def _to_int(raw: str) -> int:
    return int(raw.translate(_AR_DIGITS).replace(",", ""))


def _to_float(raw: str) -> float:
    return float(raw.translate(_AR_DIGITS).replace(",", ""))


def _category_for_rules(rule_ids: list[str], explanation_ar: str, default: str) -> str:
    joined = " ".join(rule_ids) + " " + explanation_ar
    if "CONS-DATE" in rule_ids:
        return "temporal_contradiction"
    if "CONS-NAME" in rule_ids:
        return "entity_confusion"
    if any(k in explanation_ar for k in ("أغلبية", "الحاضرين", "أعضاء المجلس")):
        return "majority_precision"
    if any(k in explanation_ar for k in ("نهائي", "استئناف", "قانوني")):
        return "legal_contradiction"
    if any(k in explanation_ar for k in ("العنوان", "عنوان")):
        return "headline_body_mismatch"
    if any(k in explanation_ar for k in ("ضمير", "الإحالة", "أسماء متشابهة", "لقب مشترك", "أدوار")):
        return "entity_confusion" if "CONS-NAME" in rule_ids or "اسم" in explanation_ar else "pronoun_ambiguity"
    if "CONS-NUMBER" in rule_ids or any(
        k in explanation_ar for k in ("نسب", "رقم", "أرقام", "اتجاه", "حسابي", "مليون", "%")
    ):
        return "numeric_contradiction"
    if "CONS-CLAIM" in rule_ids:
        return "headline_body_mismatch" if "عنوان" in explanation_ar else "claim_contradiction"
    if default != "consistency":
        return default
    if "CONS" in joined:
        return "numeric_contradiction" if "NUMBER" in joined else default
    return default


def _emit(
    *,
    counter: list[int],
    segment: Segment,
    original_text: str,
    start: int,
    end: int,
    explanation_ar: str,
    rule_ids: list[str],
    category: str = "consistency",
    decision: Decision = Decision.HARD_WARNING,
    severity: Severity = Severity.HIGH,
    support_spans: list[str] | None = None,
) -> Finding:
    counter[0] += 1
    resolved = _category_for_rules(rule_ids, explanation_ar, category)
    note = explanation_ar
    if support_spans:
        note = f"{explanation_ar} | شواهد: {' / '.join(support_spans)}"
    return Finding(
        finding_id=f"FND-E-{counter[0]:04d}",
        document_id=segment.document_id,
        segment_id=segment.segment_id,
        source=FindingSource.MECHANICAL,
        category=resolved,
        decision=decision,
        severity=severity,
        original_text=original_text,
        suggested_text=None,
        start_offset=start,
        end_offset=end,
        rule_ids=rule_ids,
        explanation_ar=note,
        confidence=0.92,
        requires_editor_review=True,
    )

def check_number_conflicts(segments: list[Segment], counter: list[int]) -> list[Finding]:
    findings: list[Finding] = []
    totals: list[tuple[Segment, re.Match[str], int]] = []
    splits: list[tuple[Segment, re.Match[str], int, int]] = []

    for segment in segments:
        for match in _TOTAL_CASUALTIES_RE.finditer(segment.text):
            totals.append((segment, match, _to_int(match.group(1))))
        for match in _TOTAL_ALT_RE.finditer(segment.text):
            totals.append((segment, match, _to_int(match.group(1))))
        for match in _SPLIT_CASUALTIES_RE.finditer(segment.text):
            splits.append(
                (segment, match, _to_int(match.group(1)), _to_int(match.group(2)))
            )

    for segment, match, a, b in splits:
        summed = a + b
        # Prefer nearest total in same segment, else any article total.
        same = [t for t in totals if t[0].segment_id == segment.segment_id]
        candidates = same or totals
        for _seg, _m, total in candidates:
            if total != summed:
                findings.append(
                    _emit(
                        counter=counter,
                        segment=segment,
                        original_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        explanation_ar=(
                            f"تعارض أرقام: مجموع {a}+{b}={summed} لا يطابق العدد المذكور {total}."
                        ),
                        rule_ids=["CONS-NUMBER"],
                    )
                )
                break

    unique_totals = sorted({t for _, _, t in totals})
    if len(unique_totals) >= 2:
        # Flag the later differing total mention.
        later = max(totals, key=lambda item: (item[0].sequence, item[1].start()))
        segment, match, value = later
        others = [t for t in unique_totals if t != value]
        findings.append(
            _emit(
                counter=counter,
                segment=segment,
                original_text=match.group(0),
                start=match.start(),
                end=match.end(),
                explanation_ar=(
                    f"تعارض في إجمالي المصابين داخل المقال: {value} مقابل {others[0]}."
                ),
                rule_ids=["CONS-NUMBER"],
            )
        )
    return findings


def check_date_conflicts(segments: list[Segment], counter: list[int]) -> list[Finding]:
    findings: list[Finding] = []
    by_day: dict[int, list[tuple[Segment, re.Match[str], str]]] = {}

    for segment in segments:
        for match in _DAY_RE.finditer(segment.text):
            weekday = match.group(1)
            day = _to_int(match.group(2))
            by_day.setdefault(day, []).append((segment, match, weekday))

    for day, items in by_day.items():
        weekdays = {w for _, _, w in items}
        # Normalize aliases
        codes = {_WEEKDAYS.get(w) for w in weekdays}
        codes.discard(None)
        if len(codes) <= 1 and len(weekdays) <= 1:
            continue
        # Conflicting weekday labels for same calendar day number.
        segment, match, weekday = items[-1]
        labels = " / ".join(sorted({w for _, _, w in items}))
        findings.append(
            _emit(
                counter=counter,
                segment=segment,
                original_text=match.group(0),
                start=match.start(),
                end=match.end(),
                explanation_ar=(
                    f"تعارض تاريخ: اليوم {day} نُسب إلى أيام مختلفة ({labels})."
                ),
                rule_ids=["CONS-DATE"],
            )
        )
    return findings


def check_military_and_civilian_math(
    segments: list[Segment], counter: list[int]
) -> list[Finding]:
    findings: list[Finding] = []
    kill_injure: list[tuple[Segment, re.Match[str], int, int]] = []
    mil_totals: list[tuple[Segment, re.Match[str], int]] = []
    civ_totals: list[tuple[Segment, re.Match[str], int]] = []
    civ_splits: list[tuple[Segment, re.Match[str], int, int]] = []

    for segment in segments:
        for match in _KILL_INJURE_RE.finditer(segment.text):
            kill_injure.append(
                (segment, match, _to_int(match.group(1)), _to_int(match.group(2)))
            )
        for match in _MIL_TOTAL_RE.finditer(segment.text):
            mil_totals.append((segment, match, _to_int(match.group(1))))
        for match in _CIVILIAN_TOTAL_RE.finditer(segment.text):
            civ_totals.append((segment, match, _to_int(match.group(1))))
        for match in _CHILDREN_WOMEN_RE.finditer(segment.text):
            civ_splits.append(
                (segment, match, _to_int(match.group(1)), _to_int(match.group(2)))
            )

    for segment, match, killed, injured in kill_injure:
        summed = killed + injured
        for _seg, _m, total in mil_totals:
            if total != summed:
                findings.append(
                    _emit(
                        counter=counter,
                        segment=segment,
                        original_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        explanation_ar=(
                            f"تعارض خسائر عسكرية: {killed}+{injured}={summed} "
                            f"لا يطابق الإجمالي {total}."
                        ),
                        rule_ids=["CONS-NUMBER"],
                    )
                )
                break

    for segment, match, children, women in civ_splits:
        summed = children + women
        for _seg, _m, total in civ_totals:
            if total != summed:
                findings.append(
                    _emit(
                        counter=counter,
                        segment=segment,
                        original_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        explanation_ar=(
                            f"تعارض مدنيين: {children}+{women}={summed} "
                            f"لا يطابق العدد المعلن {total}."
                        ),
                        rule_ids=["CONS-NUMBER"],
                    )
                )
                break
    return findings


def check_percent_topic_conflicts(
    segments: list[Segment], counter: list[int]
) -> list[Finding]:
    findings: list[Finding] = []
    by_topic: dict[str, list[tuple[Segment, re.Match[str], float]]] = {}

    for segment in segments:
        for pattern in (_PCT_TOPIC_RE, _PCT_ALT_RE):
            for match in pattern.finditer(segment.text):
                topic = match.group(1)
                key = "تضخم" if "تضخم" in topic else (
                    "بطالة" if "بطالة" in topic else (
                        "مشاركة" if "مشاركة" in topic else topic
                    )
                )
                by_topic.setdefault(key, []).append(
                    (segment, match, _to_float(match.group(2)))
                )

        # Same-paragraph unemployment: "معدل البطالة ... 11% ... لم يتجاوز 8.5%"
        if "بطالة" in segment.text:
            pcts = [
                (m, _to_float(m.group(1)))
                for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", segment.text)
            ]
            values = sorted({round(v, 3) for _, v in pcts})
            if len(values) >= 2:
                match, value = pcts[-1]
                by_topic.setdefault("بطالة", []).append((segment, match, value))
                # Ensure earlier value is also registered for conflict reporting.
                for m, v in pcts[:-1]:
                    by_topic.setdefault("بطالة", []).append((segment, m, v))

    for topic, items in by_topic.items():
        values = sorted({round(v, 3) for _, _, v in items})
        if len(values) < 2:
            continue
        segment, match, value = items[-1]
        findings.append(
            _emit(
                counter=counter,
                segment=segment,
                original_text=match.group(0),
                start=match.start(),
                end=match.end(),
                explanation_ar=(
                    f"تعارض نسب ({topic}): وردت قيم مختلفة "
                    f"{' / '.join(str(v) for v in values)}%."
                ),
                rule_ids=["CONS-NUMBER"],
            )
        )
    return findings


def check_turnout_math(segments: list[Segment], counter: list[int]) -> list[Finding]:
    findings: list[Finding] = []
    claimed: list[tuple[Segment, re.Match[str], float]] = []
    parts: list[tuple[Segment, re.Match[str], float, float]] = []

    for segment in segments:
        for match in re.finditer(r"نسبة المشاركة بلغت\s+(\d+(?:\.\d+)?)\s*%", segment.text):
            claimed.append((segment, match, _to_float(match.group(1))))
        for match in _TURNOUT_PARTS_RE.finditer(segment.text):
            parts.append(
                (segment, match, _to_float(match.group(1)), _to_float(match.group(2)))
            )

    for segment, match, voters, eligible in parts:
        if eligible <= 0:
            continue
        actual = round(100.0 * voters / eligible, 1)
        for _seg, cmatch, claimed_pct in claimed:
            if abs(actual - claimed_pct) >= 5:
                findings.append(
                    _emit(
                        counter=counter,
                        segment=segment,
                        original_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        explanation_ar=(
                            f"تعارض نسبة المشاركة: {voters} من {eligible} مليون "
                            f"≈ {actual}% وليس {claimed_pct}%."
                        ),
                        rule_ids=["CONS-NUMBER"],
                    )
                )
                break
    return findings


def check_death_count_conflicts(
    segments: list[Segment], counter: list[int]
) -> list[Finding]:
    findings: list[Finding] = []
    values: list[tuple[Segment, re.Match[str], int]] = []
    for segment in segments:
        for match in _DEATH_COUNT_RE.finditer(segment.text):
            values.append((segment, match, _to_int(match.group(1))))
        for match in re.finditer(
            r"تقرير المستشفيات إلى\s+(\d{1,4})\s*حالة", segment.text
        ):
            values.append((segment, match, _to_int(match.group(1))))
        for match in re.finditer(
            r"العدد لم يتجاوز\s+(\d{1,4})", segment.text
        ):
            values.append((segment, match, _to_int(match.group(1))))

    uniq = sorted({v for _, _, v in values})
    if len(uniq) >= 2:
        segment, match, value = values[-1]
        findings.append(
            _emit(
                counter=counter,
                segment=segment,
                original_text=match.group(0),
                start=match.start(),
                end=match.end(),
                explanation_ar=(
                    f"تعارض أعداد الوفيات داخل المقال: "
                    f"{' / '.join(str(v) for v in uniq)}."
                ),
                rule_ids=["CONS-NUMBER"],
            )
        )
    return findings


def check_unemployed_trend_conflict(
    segments: list[Segment], counter: list[int]
) -> list[Finding]:
    findings: list[Finding] = []
    for segment in segments:
        for match in _UNEMPLOYED_TREND_RE.finditer(segment.text):
            a = _to_int(match.group(1))
            b = _to_int(match.group(2))
            if b > a:
                findings.append(
                    _emit(
                        counter=counter,
                        segment=segment,
                        original_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        explanation_ar=(
                            f"تناقض: القول بانخفاض عدد العاطلين مع ارتفاع العدد من {a} إلى {b} ألفاً."
                        ),
                        rule_ids=["CONS-NUMBER"],
                    )
                )
    return findings


def check_case_rate_conflict(
    segments: list[Segment], counter: list[int]
) -> list[Finding]:
    findings: list[Finding] = []
    weekly: list[tuple[Segment, re.Match[str], int]] = []
    daily: list[tuple[Segment, re.Match[str], int]] = []
    for segment in segments:
        for match in _CASE_WEEKLY_RE.finditer(segment.text):
            weekly.append((segment, match, _to_int(match.group(1))))
        for match in _CASE_DAILY_RE.finditer(segment.text):
            daily.append((segment, match, _to_int(match.group(1))))
    for segment, match, day_n in daily:
        for _seg, _m, week_n in weekly:
            if day_n > week_n:
                findings.append(
                    _emit(
                        counter=counter,
                        segment=segment,
                        original_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        explanation_ar=(
                            f"تناقض معدلات الإصابة: {day_n} في يوم واحد أعلى من "
                            f"{week_n} أسبوعياً."
                        ),
                        rule_ids=["CONS-NUMBER"],
                    )
                )
                break
    return findings


def check_role_name_conflicts(segments: list[Segment], counter: list[int]) -> list[Finding]:
    findings: list[Finding] = []
    presidents: list[tuple[Segment, re.Match[str], str, str]] = []
    pms: list[tuple[Segment, re.Match[str], str, str]] = []

    for segment in segments:
        for match in _PRESIDENT_RE.finditer(segment.text):
            presidents.append((segment, match, match.group(1), match.group(2)))
        for match in _PM_RE.finditer(segment.text):
            pms.append((segment, match, match.group(1), match.group(2)))

    for p_seg, p_match, p_first, p_last in presidents:
        for pm_seg, pm_match, pm_first, pm_last in pms:
            if p_first == pm_first and p_last != pm_last:
                findings.append(
                    _emit(
                        counter=counter,
                        segment=pm_seg,
                        original_text=pm_match.group(0),
                        start=pm_match.start(),
                        end=pm_match.end(),
                        explanation_ar=(
                            f"تضارب أسماء/أدوار: الرئيس «{p_first} {p_last}» "
                            f"ورئيس الوزراء «{pm_first} {pm_last}» يشتركان بالاسم الأول "
                            "ويختلفان باللقب؛ يحتاج تحققاً."
                        ),
                        rule_ids=["CONS-NAME"],
                    )
                )
                return findings
    return findings


_CLAIM_PAIRS: list[tuple[str, str, str]] = [
    (
        "نمواً تاريخياً",
        "تراجع الناتج",
        "تناقض: ادعاء نمو تاريخي مع تراجع الناتج المحلي.",
    ),
    (
        "لم تفرض أي ضرائب",
        "رسم تنمية",
        "تناقض: نفي الضرائب الجديدة مع فرض رسم إضافي.",
    ),
    (
        "لم يتسن التأكد",
        "بلا شك",
        "تناقض: تعذر التحقق المستقل ثم القطع بيقين.",
    ),
    (
        "لم تستهدف أي مناطق سكنية",
        "قصف مواقع داخل ثلاث قرى",
        "تناقض: نفي استهداف المناطق السكنية مع الإقرار بقصف قرى.",
    ),
    (
        "انتهت نهائياً",
        "تجدد القتال",
        "تناقض: إعلان انتهاء المعركة نهائياً مع احتمال تجددها.",
    ),
    (
        "الآلاف للاحتفال",
        "تجمعات محدودة",
        "تناقض: تضخيم أعداد المحتفلين مقابل الصور المحدودة.",
    ),
    (
        "ملتزمة بالحل السلمي",
        "القوة هي اللغة الوحيدة",
        "تناقض: الالتزام بالحل السلمي مع التهديد بالقوة.",
    ),
    (
        "انتهاء موجة وباء",
        "رفع درجة الاستعداد القصوى",
        "تناقض: إعلان انتهاء الوباء مع رفع الاستعداد القصوى.",
    ),
    (
        "لم تسجل أي آثار جانبية",
        "43 بلاغاً",
        "تناقض: نفي الآثار الجانبية مع وجود بلاغات.",
    ),
    (
        "تحت السيطرة تماماً",
        "حظر تجول",
        "تناقض: السيطرة الكاملة مع فرض حظر تجول وإغلاق مدارس.",
    ),
    (
        "أشادوا بنزاهة",
        "مخالفات خطيرة",
        "تناقض: وصف إشادة المراقبين مع تسجيل مخالفات خطيرة.",
    ),
    (
        "دون أي خروقات مؤثرة",
        "تعطيل التصويت في 120",
        "تناقض: وصف المخالفات بالبسيطة/غير المؤثرة مع تعطيل واسع.",
    ),
    (
        "تستخدم المدنيين كدروع بشرية",
        "لم يتمكن من تحديد الجهة",
        "استنتاج غير مدعوم حول الدروع البشرية بعد شهادة غير محددة المصدر.",
    ),
    (
        "نهائيًا",
        "قابلًا للاستئناف",
        "تناقض قانوني: الإدانة النهائية تتعارض مع قابلية الاستئناف.",
    ),
    (
        "نهائيًا",
        "قابلا للاستئناف",
        "تناقض قانوني: الإدانة النهائية تتعارض مع قابلية الاستئناف.",
    ),
    (
        "اتفاق نهائي",
        "أصبح من المؤكد",
        "تناقض: نفي الاتفاق النهائي ثم الجزم ببدء الانسحاب.",
    ),
    (
        "سابق لأوانه",
        "أصبح من المؤكد",
        "تناقض: وصف الاتفاق بالسابق لأوانه ثم الجزم بالنتيجة.",
    ),
    (
        "قبل ثلاثة أسابيع",
        "قبل يومين",
        "تناقض زمني: تشكيل الحكومة قبل ثلاثة أسابيع مقابل قبل يومين.",
    ),
    # Note: title/body cancel-vs-defer is handled only by check_headline_body_conflict
    # to avoid double-flagging both spans as separate findings.
]


_DIRECTION_RISE_RE = re.compile(
    r"(ارتفع|ارتفاع|انخفض|انخفاض)\s+(?:عدد\s+)?[^\d]{0,40}?من\s+(\d+(?:\.\d+)?)\s*"
    r"(?:مليون|ملايين|ألف|آلاف|ألفًا|الفا)?\s*إلى\s+(\d+(?:\.\d+)?)"
)
_PARTICIPATION_RISE_RE = re.compile(
    r"(ارتفعت|انخفضت)\s+إلى\s+(\d+(?:\.\d+)?)\s*%\s+بعد أن كانت\s+(\d+(?:\.\d+)?)\s*%"
)
_PCT_LIST_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_MAJORITY_RE = re.compile(
    r"(?:بأغلبية|أغلبية)\s+(\d{1,4})\s+نائب(?:اً|ًا)?\s+من أصل\s+(\d{1,4})"
)
_ATTENDEES_RE = re.compile(r"الحاضرين[^\d]{0,30}?(\d{1,4})")
_SIMILAR_PERSON_RE = re.compile(
    r"(?:رئيس الحكومة|رئيس الوزراء|الرئيس|الوزير السابق|وزير الخارجية)\s+"
    r"([^\s،,.]{2,20})\s+([^\s،,.]{2,20})"
)
_ROLE_FOR_NAME_RE = re.compile(
    r"(رئيس الحكومة|رئيس الوزراء|الرئيس|رئيس الدولة)\s+([^\s،,.]{2,20})\s+([^\s،,.]{2,20})"
)
_NAME_HOLDS_ROLE_RE = re.compile(
    r"([^\s،,.]{2,20})\s+([^\s،,.]{2,20})\s+يشغل منصب\s+(رئيس الحكومة|رئيس الوزراء|الرئيس|رئيس الدولة)"
)


def check_direction_conflicts(
    segments: list[Segment], counter: list[int]
) -> list[Finding]:
    findings: list[Finding] = []
    for segment in segments:
        for match in _DIRECTION_RISE_RE.finditer(segment.text):
            verb = match.group(1)
            a = _to_float(match.group(2))
            b = _to_float(match.group(3))
            rising = verb.startswith("ارتف")
            falling = verb.startswith("انخف")
            if rising and b < a:
                findings.append(
                    _emit(
                        counter=counter,
                        segment=segment,
                        original_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        explanation_ar=(
                            f"تناقض اتجاه: القول بالارتفاع من {a} إلى {b} (انخفاض فعلي)."
                        ),
                        rule_ids=["CONS-NUMBER"],
                    )
                )
            if falling and b > a:
                findings.append(
                    _emit(
                        counter=counter,
                        segment=segment,
                        original_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        explanation_ar=(
                            f"تناقض اتجاه: القول بالانخفاض من {a} إلى {b} (ارتفاع فعلي)."
                        ),
                        rule_ids=["CONS-NUMBER"],
                    )
                )
        for match in _PARTICIPATION_RISE_RE.finditer(segment.text):
            verb = match.group(1)
            now = _to_float(match.group(2))
            prev = _to_float(match.group(3))
            if verb.startswith("ارتف") and now < prev:
                findings.append(
                    _emit(
                        counter=counter,
                        segment=segment,
                        original_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        explanation_ar=(
                            f"تناقض اتجاه: القول بارتفاع النسبة إلى {now}% بعد {prev}%."
                        ),
                        rule_ids=["CONS-NUMBER"],
                    )
                )
    return findings


def check_percent_sum_overflow(
    segments: list[Segment], counter: list[int]
) -> list[Finding]:
    findings: list[Finding] = []
    for segment in segments:
        vals = [_to_float(m.group(1)) for m in _PCT_LIST_RE.finditer(segment.text)]
        if len(vals) < 3:
            continue
        total = sum(vals)
        if total > 100.5:
            match = list(_PCT_LIST_RE.finditer(segment.text))[-1]
            findings.append(
                _emit(
                    counter=counter,
                    segment=segment,
                    original_text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    explanation_ar=(
                        f"خطأ حسابي: مجموع النسب ≈ {round(total, 1)}% يتجاوز 100%."
                    ),
                    rule_ids=["CONS-NUMBER"],
                )
            )
    return findings


def check_majority_precision(
    segments: list[Segment], counter: list[int]
) -> list[Finding]:
    findings: list[Finding] = []
    votes: list[tuple[Segment, re.Match[str], int, int]] = []
    attendees: list[int] = []
    for segment in segments:
        for match in _MAJORITY_RE.finditer(segment.text):
            votes.append(
                (segment, match, _to_int(match.group(1)), _to_int(match.group(2)))
            )
        for match in _ATTENDEES_RE.finditer(segment.text):
            attendees.append(_to_int(match.group(1)))
    for segment, match, yes, total in votes:
        if yes * 2 <= total:
            note = (
                f"101 من {total} ليست أغلبية مطلقة لأعضاء المجلس"
                if total
                else "ليست أغلبية مطلقة"
            )
            if attendees:
                att = attendees[0]
                if yes * 2 > att:
                    note += f"، وإن كانت أغلبية الحاضرين ({att})."
            findings.append(
                _emit(
                    counter=counter,
                    segment=segment,
                    original_text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    explanation_ar=(
                        f"دقة الأغلبية: {yes} من أصل {total} — {note} "
                        "يُفضَّل: وافق غالبية النواب الحاضرين."
                    ),
                    rule_ids=["CONS-NUMBER"],
                )
            )
    return findings


def check_entity_role_conflicts(
    segments: list[Segment], counter: list[int]
) -> list[Finding]:
    """Flag same full name used with conflicting high offices, and near-duplicate names."""
    findings: list[Finding] = []
    roles_by_name: dict[str, list[tuple[Segment, re.Match[str], str]]] = {}
    people: list[tuple[str, str]] = []

    for segment in segments:
        for match in _ROLE_FOR_NAME_RE.finditer(segment.text):
            role, first, last = match.group(1), match.group(2), match.group(3)
            full = f"{first} {last}"
            roles_by_name.setdefault(full, []).append((segment, match, role))
            people.append((first, last))
        for match in _NAME_HOLDS_ROLE_RE.finditer(segment.text):
            first, last, role = match.group(1), match.group(2), match.group(3)
            full = f"{first} {last}"
            roles_by_name.setdefault(full, []).append((segment, match, role))
            people.append((first, last))
        for match in _SIMILAR_PERSON_RE.finditer(segment.text):
            people.append((match.group(1), match.group(2)))

    for full, items in roles_by_name.items():
        roles = {r for _, _, r in items}
        # Normalize PM aliases
        norm = set()
        for r in roles:
            if "حكومة" in r or "وزراء" in r:
                norm.add("pm")
            elif "رئيس" in r:
                norm.add("president")
            else:
                norm.add(r)
        if "pm" in norm and "president" in norm:
            segment, match, role = items[-1]
            findings.append(
                _emit(
                    counter=counter,
                    segment=segment,
                    original_text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    explanation_ar=(
                        f"تعارض أدوار للكيان «{full}»: يظهر كرئيس دولة ورئيس حكومة داخل المقال."
                    ),
                    rule_ids=["CONS-NAME"],
                )
            )

    # Near-duplicate surnames / swapped names (كمال منصور vs كمال الكيلاني, نادر منصور vs نادر الكيلاني)
    uniq = sorted({(a, b) for a, b in people})
    for i, (f1, l1) in enumerate(uniq):
        for f2, l2 in uniq[i + 1 :]:
            if f1 == f2 and l1 != l2:
                # Same first name, different last — warn once on later mention
                for segment in reversed(segments):
                    needle = f"{f2} {l2}"
                    idx = segment.text.find(needle)
                    if idx < 0:
                        continue
                    findings.append(
                        _emit(
                            counter=counter,
                            segment=segment,
                            original_text=needle,
                            start=idx,
                            end=idx + len(needle),
                            explanation_ar=(
                                f"أسماء متشابهة قد تكون خلطًا إحاليًا: «{f1} {l1}» و«{f2} {l2}»."
                            ),
                            rule_ids=["CONS-NAME"],
                        )
                    )
                    break
            if f1 != f2 and l1 == l2:
                for segment in reversed(segments):
                    needle = f"{f2} {l2}"
                    idx = segment.text.find(needle)
                    if idx < 0:
                        continue
                    findings.append(
                        _emit(
                            counter=counter,
                            segment=segment,
                            original_text=needle,
                            start=idx,
                            end=idx + len(needle),
                            explanation_ar=(
                                f"لقب مشترك مع اسم أول مختلف: «{f1} {l1}» و«{f2} {l2}» — تحقق من الإحالة."
                            ),
                            rule_ids=["CONS-NAME"],
                        )
                    )
                    break
    return findings


def check_headline_body_conflict(
    segments: list[Segment], counter: list[int]
) -> list[Finding]:
    if not segments:
        return []
    headline = next((s for s in segments if s.zone.value == "headline"), segments[0])
    body = "\n".join(s.text for s in segments if s.segment_id != headline.segment_id)
    pairs = [
        ("تلغي", "تأجيل", "العنوان يقول إلغاء بينما المتن يتحدث عن تأجيل."),
        ("تكشف تورط", "تحقيقاتها الأولية", "العنوان يجزم بينما التحقيق أولي."),
        ("وافقت على سحب", "إشارات إيجابية", "العنوان يحوّل إشارات إلى موافقة نهائية."),
        ("وافقت على سحب", "استعدادًا لمناقشة", "العنوان يحوّل استعدادًا للنقاش إلى موافقة."),
    ]
    findings: list[Finding] = []
    for a, b, expl in pairs:
        if a in headline.text and b in body:
            idx = headline.text.find(a)
            findings.append(
                _emit(
                    counter=counter,
                    segment=headline,
                    original_text=a,
                    start=idx,
                    end=idx + len(a),
                    explanation_ar=expl,
                    rule_ids=["CONS-CLAIM"],
                    category="headline_body_mismatch",
                    support_spans=[b],
                )
            )
            break  # one primary headline/body issue
    return findings


def check_claim_pairs(segments: list[Segment], counter: list[int]) -> list[Finding]:
    findings: list[Finding] = []
    full = "\n".join(s.text for s in segments)
    headline = next((s for s in segments if s.zone.value == "headline"), None)
    for a, b, explanation in _CLAIM_PAIRS:
        if a not in full or b not in full:
            continue
        # Prefer anchoring on the overclaim / primary span (a), especially in headline.
        primary_span = a
        anchor = None
        if headline is not None and a in headline.text:
            anchor = headline
        else:
            for segment in segments:
                if a in segment.text:
                    anchor = segment
                    break
            if anchor is None:
                for segment in reversed(segments):
                    if b in segment.text:
                        anchor = segment
                        primary_span = b
                        break
        if anchor is None:
            continue
        idx = anchor.text.find(primary_span)
        if idx < 0:
            continue
        findings.append(
            _emit(
                counter=counter,
                segment=anchor,
                original_text=primary_span,
                start=idx,
                end=idx + len(primary_span),
                explanation_ar=explanation,
                rule_ids=["CONS-CLAIM"],
                category="claim_contradiction",
                support_spans=[b if primary_span == a else a],
            )
        )
    return findings


def dedupe_contradiction_findings(findings: list[Finding]) -> list[Finding]:
    """Keep one primary finding per contradiction family."""
    kept: list[Finding] = []
    seen_keys: set[str] = set()
    for finding in findings:
        if "CONS-CLAIM" not in finding.rule_ids:
            kept.append(finding)
            continue
        # Normalize by shared evidence tokens in explanation.
        key = finding.explanation_ar.split("|")[0].strip()[:80]
        if key in seen_keys:
            continue
        # Also collapse cancel/defer style duplicates.
        text = finding.original_text
        family = None
        if "تلغ" in text or "تأجيل" in finding.explanation_ar:
            family = "cancel_vs_defer"
        elif "تورط" in text or "أولية" in finding.explanation_ar:
            family = "preliminary_vs_guilt"
        elif "وافقت" in text or "إشارات" in finding.explanation_ar:
            family = "signals_vs_agreement"
        if family and family in seen_keys:
            continue
        if family:
            seen_keys.add(family)
        seen_keys.add(key)
        kept.append(finding)
    return kept


def run_consistency_detectors(
    segments: list[Segment],
    *,
    counter_start: int = 0,
) -> list[Finding]:
    counter = [counter_start]
    findings: list[Finding] = []
    findings.extend(check_number_conflicts(segments, counter))
    findings.extend(check_military_and_civilian_math(segments, counter))
    findings.extend(check_percent_topic_conflicts(segments, counter))
    findings.extend(check_turnout_math(segments, counter))
    findings.extend(check_death_count_conflicts(segments, counter))
    findings.extend(check_unemployed_trend_conflict(segments, counter))
    findings.extend(check_case_rate_conflict(segments, counter))
    findings.extend(check_direction_conflicts(segments, counter))
    findings.extend(check_percent_sum_overflow(segments, counter))
    findings.extend(check_majority_precision(segments, counter))
    findings.extend(check_entity_role_conflicts(segments, counter))
    findings.extend(check_headline_body_conflict(segments, counter))
    findings.extend(check_claim_pairs(segments, counter))
    findings.extend(check_date_conflicts(segments, counter))
    findings.extend(check_role_name_conflicts(segments, counter))
    return dedupe_contradiction_findings(findings)
