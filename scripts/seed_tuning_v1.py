"""Seed a separate tuning set (NOT the hidden benchmark)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmark_tuning_v1" / "cases"
OUT.mkdir(parents=True, exist_ok=True)

CASES = [
    {
        "case_id": "tune-0001",
        "headline": "وزارة الصحة تعلن انخفاض الإصابات بعد أسبوع من الإغلاق",
        "body": "قالت الوزارة إن الإصابات انخفضت إلى 400 أسبوعياً، بينما سجلت النشرة اليومية 900 حالة في يوم واحد. وأكدت أن الوضع تحت السيطرة رغم إعادة فرض حظر جزئي.",
        "expect_needles": ["خلال يوم", "تحت السيطرة", "حظر"],
    },
    {
        "case_id": "tune-0002",
        "headline": "زعيم الحزب: المعارضة «خانت الوطن»",
        "body": "قال زعيم الحزب إن المعارضة «خانت الوطن»، دون تقديم أدلة. ويبدو أن تصريحه يعكس إجماعاً شعبياً واسعاً ضد المعارضة.",
        "expect_needles": ["إجماعاً شعبياً", "خانت الوطن"],
    },
    {
        "case_id": "tune-0003",
        "headline": "الحكومة تلغي الرسوم الجديدة على الخدمات",
        "body": "أعلنت الحكومة تأجيل تطبيق الرسوم الجديدة لمدة شهرين فقط، مشيرة إلى مراجعة لاحقة.",
        "expect_needles": ["تلغي", "تأجيل"],
    },
    {
        "case_id": "tune-0004",
        "headline": "نتائج التصويت تؤكد أغلبية المجلس",
        "body": "صوّت 95 نائباً من أصل 210 لصالح المشروع، وقال المتحدث إن الشعب أقر القانون عبر ممثليه.",
        "expect_needles": ["أغلبية", "الشعب أقر"],
    },
    {
        "case_id": "tune-0005",
        "headline": "مصادر: الاتفاق أصبح نهائياً",
        "body": "قال دبلوماسي إن هناك «إشارات إيجابية». وأكد أنه وافق بالفعل على الانسحاب. وقالت الخارجية إن أي حديث عن اتفاق نهائي سابق لأوانه.",
        "expect_needles": ["أكد أنه وافق", "سابق لأوانه"],
    },
    {
        "case_id": "tune-0006",
        "headline": "بدء محادثات بين الحكومة والمعارضة",
        "body": "بدأت محادثات في العاصمة لمناقشة قانون الانتخابات. وقال ممثل المعارضة إن اللقاء كان «جدياً»، دون إعلان اتفاق.",
        "expect_needles": [],
        "clean": True,
    },
    {
        "case_id": "tune-0007",
        "headline": "المحكمة تدين المتهم نهائياً",
        "body": "أُدين المتهم نهائيًا، ولا يزال الحكم قابلًا للاستئناف أمام محكمة أعلى.",
        "expect_needles": ["نهائي", "استئناف"],
    },
    {
        "case_id": "tune-0008",
        "headline": "ارتفاع عدد المشتغلين يعكس التعافي",
        "body": "قالت الوزارة إن عدد المشتغلين ارتفع من 3.2 ملايين إلى 3.1 ملايين، بينما انخفضت البطالة من 11% إلى 10%.",
        "expect_needles": ["الارتفاع من 3.2"],
    },
    {
        "case_id": "tune-0009",
        "headline": "قال المتحدث: «هذه الإدارة فاسدة بالكامل»",
        "body": "قال المتحدث: «هذه الإدارة فاسدة بالكامل». ونقلت الوكالة التصريح منسوبًا إليه دون تعليق إضافي.",
        "expect_needles": ["فاسدة"],
        "quote_preserve": True,
    },
    {
        "case_id": "tune-0010",
        "headline": "بحسب مصادر سيستقيل الوزير غداً",
        "body": "بحسب مصادر، فإن الوزير سيستقيل غدًا دون الإشارة إلى هوية المصدر أو درجة التأكيد.",
        "expect_needles": ["بحسب مصادر", "سيستقيل"],
    },
]

for case in CASES:
    path = OUT / f"{case['case_id']}.json"
    public = {
        "case_id": case["case_id"],
        "headline": case["headline"],
        "body": case["body"],
    }
    path.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

meta = {
    "name": "benchmark_tuning_v1",
    "note": "Separate from hidden benchmark_v2. Do not copy hidden gold here.",
    "cases": [
        {
            "case_id": c["case_id"],
            "clean": c.get("clean", False),
            "quote_preserve": c.get("quote_preserve", False),
            "expect_needles": c.get("expect_needles", []),
        }
        for c in CASES
    ],
}
(ROOT / "benchmark_tuning_v1" / "expectations.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
(ROOT / "benchmark_tuning_v1" / "README.md").write_text(
    "# benchmark_tuning_v1\n\n"
    "Public tuning cases only. Iterate prompts/gates here.\n"
    "Keep `benchmark_v2` frozen for final blind evaluation.\n",
    encoding="utf-8",
)
print(f"wrote {len(CASES)} tuning cases")
