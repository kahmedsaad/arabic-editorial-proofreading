"""Seed advanced cases 6-12, short adversarial sentences, and split datasets."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data" / "evaluation" / "articles"
ART.mkdir(parents=True, exist_ok=True)
EVAL = ROOT / "data" / "evaluation"


def _art(article_id: str, title: str, paragraphs: list[str], content_type: str = "news") -> dict:
    sections = [
        {"section_id": "headline", "surface": "headline", "text": title},
    ]
    for i, text in enumerate(paragraphs, start=1):
        sections.append(
            {
                "section_id": f"p{i}",
                "surface": "lead" if i == 1 else "paragraph",
                "text": text,
            }
        )
    return {
        "article_id": article_id,
        "title": title,
        "language": "ar",
        "content_type": content_type,
        "sections": sections,
    }


ARTICLES: dict[str, dict] = {}

ARTICLES["indirect-accusation-v1"] = _art(
    "indirect-accusation-v1",
    "تحقيقات تكشف تورط مسؤولين سابقين في تحويل أموال الإعمار إلى الخارج",
    [
        "قالت هيئة النزاهة في جمهورية النهر إن تحقيقاتها الأولية رصدت تحويلات مالية مرتبطة بعقود إعادة الإعمار، مشيرة إلى أن بعض المستفيدين كانوا يشغلون مناصب حكومية خلال الفترة الماضية.",
        "ولم تسمّ الهيئة أي مسؤول بصورة مباشرة، كما أوضحت أن التحقيق لم يصل بعد إلى مرحلة توجيه اتهامات رسمية.",
        "لكن مسؤولًا مطلعًا على الملف قال إن «الأدلة أصبحت شبه مكتملة»، وإن الإعلان عن أسماء المتورطين قد يتم خلال أسابيع.",
        "وكان الوزير السابق سامح الديب قد أشرف على لجنة إعادة الإعمار بين عامي 2021 و2023، وهي الفترة نفسها التي تقول الهيئة إن أغلب التحويلات المشبوهة جرت خلالها.",
        "ويؤكد ذلك أن الوزير السابق كان أحد المستفيدين من عمليات التحويل، رغم أنه نفى سابقًا امتلاك أي حسابات خارجية.",
        "وقال محامي الديب إن موكله لم يُستدعَ للتحقيق، وإن ربط اسمه بالقضية اعتمادًا على فترة توليه المنصب «محاولة لإدانته إعلاميًا قبل ظهور الأدلة».",
        "وفي بيان لاحق، قالت الهيئة إن التحقيق يشمل «كل من كانت له صلة مباشرة أو غير مباشرة بالعقود»، دون تحديد ما إذا كانت الصلة الإدارية وحدها كافية لإدراج الشخص في التحقيق.",
    ],
)

ARTICLES["quoted-incitement-v1"] = _art(
    "quoted-incitement-v1",
    "زعيم الحزب الوطني: خصومنا أدوات للخارج ولا يستحقون المشاركة في الحكم",
    [
        "قال رئيس الحزب الوطني، حاتم رزق، خلال تجمع جماهيري إن المعارضة «مجموعة من العملاء الذين يبيعون البلاد مقابل دعم أجنبي»، مضيفًا أن السماح لهم بالمشاركة في الانتخابات «تهديد مباشر لأمن الدولة».",
        "وأوضح رزق أن حزبه سيطالب البرلمان بتعديل قانون الأحزاب لمنع الكيانات التي تتلقى تمويلًا خارجيًا من خوض الانتخابات.",
        "ولم يقدم رئيس الحزب أدلة على تلقي أحزاب المعارضة تمويلًا غير قانوني، لكنه قال إن «كل المواطنين يعرفون الحقيقة».",
        "من جانبها، رفضت جبهة المستقبل الاتهامات، وقالت إن الحزب الحاكم يستخدم خطاب التخوين لتبرير التضييق السياسي.",
        "وأكدت الجبهة أنها تنشر حساباتها المالية سنويًا، وأن آخر مراجعة رسمية لم تسجل مخالفات ضدها.",
        "ويبدو أن تصريحات رزق تعكس غضبًا شعبيًا واسعًا من المعارضة، التي فقدت بالفعل شرعيتها السياسية بسبب ارتباطاتها المشبوهة.",
    ],
)

ARTICLES["name-date-chaos-v1"] = _art(
    "name-date-chaos-v1",
    "رئيس الحكومة يعلن استقالته بعد يومين من تشكيل الوزارة الجديدة",
    [
        "أعلن رئيس الحكومة كمال منصور مساء الاثنين استقالته من منصبه، موضحًا أن القرار جاء لأسباب صحية.",
        "وكان الرئيس نادر منصور قد كلّف كمال منصور بتشكيل الحكومة يوم الأحد الماضي، بعد قبول استقالة رئيس الوزراء السابق نادر الكيلاني.",
        "وفي بيان صادر صباح الثلاثاء، قال مكتب رئيس الوزراء إن الحكومة ستواصل عملها حتى تعيين بديل، وإن كمال الكيلاني سيترأس جلسة مجلس الوزراء المقبلة.",
        "وذكرت وكالة الأنباء الرسمية أن الرئيس قبل استقالة منصور يوم الاثنين 18 أكتوبر، بينما أشارت وثيقة الرئاسة إلى أن قرار القبول صدر يوم الأحد 18 أكتوبر.",
        "كما قالت الوثيقة إن الحكومة الحالية تشكلت قبل ثلاثة أسابيع، رغم أن البيان السابق ذكر أنها شُكلت قبل يومين فقط.",
        "وفي فقرة لاحقة، أشار التقرير إلى أن نادر منصور يشغل منصب رئيس الحكومة منذ عامين، مع أنه ذُكر في بداية التقرير بصفته رئيس الدولة.",
    ],
)

ARTICLES["labor-context-math-v1"] = _art(
    "labor-context-math-v1",
    "تراجع البطالة للمرة الأولى منذ خمس سنوات رغم فقدان 80 ألف وظيفة",
    [
        "أعلنت وزارة العمل انخفاض معدل البطالة من 12.4% إلى 10.9% خلال الربع الثالث، وقالت إن ذلك يعكس تعافي سوق العمل.",
        "وأوضحت الوزارة أن عدد المشتغلين ارتفع من 4.1 ملايين إلى 4.05 ملايين شخص، بينما انخفض عدد العاطلين من 620 ألفًا إلى 670 ألفًا.",
        "وأضافت أن الاقتصاد وفر 120 ألف فرصة عمل جديدة، رغم أن التقرير نفسه أشار إلى إغلاق مصانع أدّى إلى فقدان 80 ألف وظيفة، وخروج 55 ألف شخص من سوق العمل.",
        "وقالت الوزارة إن نسبة المشاركة الاقتصادية ارتفعت إلى 63% بعد أن كانت 65% في الربع السابق.",
        "من جانبه، قال وزير العمل إن انخفاض البطالة يثبت نجاح خطة الحكومة، لكن اقتصاديين أشاروا إلى أن خروج عدد كبير من الأشخاص من قوة العمل قد يؤدي حسابيًا إلى انخفاض معدل البطالة دون تحسن حقيقي في التوظيف.",
        "ويعني ذلك أن الحكومة خفضت البطالة فعلًا من خلال خلق فرص عمل جديدة.",
    ],
)

ARTICLES["pronoun-source-v1"] = _art(
    "pronoun-source-v1",
    "مصادر: الدولة المجاورة وافقت على سحب قواتها من المنطقة المتنازع عليها",
    [
        "قال مسؤول دبلوماسي إن بلاده تلقت «إشارات إيجابية» من الدولة المجاورة بشأن خفض التصعيد في المنطقة الحدودية.",
        "وأضاف أن المباحثات تناولت إنشاء آلية مشتركة للمراقبة، لكنه شدد على أن التفاصيل لم تُحسم بعد.",
        "ونقلت صحيفة محلية عن مصدر قريب من المحادثات قوله إن الطرف الآخر أبدى استعدادًا لمناقشة إعادة الانتشار.",
        "وأكد أنه وافق بالفعل على سحب القوات خلال أسبوعين.",
        "ولم يتضح ما إذا كان الضمير في عبارة «أكد أنه وافق» يعود إلى المصدر، أم المسؤول الدبلوماسي، أم ممثل الدولة المجاورة.",
        "وفي بيان رسمي، قالت وزارة الخارجية إن المفاوضات مستمرة، وإن أي حديث عن اتفاق نهائي «سابق لأوانه».",
        "ورغم ذلك، أصبح من المؤكد أن الانسحاب سيبدأ قبل نهاية الشهر.",
    ],
)

ARTICLES["majority-precision-v1"] = _art(
    "majority-precision-v1",
    "البرلمان يعتمد مشروع القانون المثير للجدل بعد موافقة الأغلبية",
    [
        "صوّت البرلمان لصالح مشروع قانون تنظيم الإعلام بأغلبية 101 نائب من أصل 220.",
        "وقال رئيس البرلمان إن المشروع حظي بتأييد غالبية الأعضاء الحاضرين، موضحًا أن عدد الحاضرين في الجلسة بلغ 150 نائبًا.",
        "واعترضت المعارضة على وصف النتيجة بأنها موافقة أغلبية البرلمان، قائلة إن المؤيدين لم يشكلوا أغلبية إجمالي أعضاء المجلس.",
        "وفي النسخة الأولى من الخبر وردت العبارة التالية: وافق البرلمان بأغلبية أعضائه على مشروع القانون.",
        "وقال المتحدث باسم الحكومة إن «الشعب أقر القانون عبر ممثليه»، رغم عدم إجراء استفتاء شعبي.",
    ],
)

ARTICLES["clean-talks-v1"] = _art(
    "clean-talks-v1",
    "بدء جولة جديدة من المحادثات بين الحكومة والمعارضة",
    [
        "بدأت في العاصمة، صباح الأربعاء، جولة جديدة من المحادثات بين ممثلين عن الحكومة وتحالف المعارضة، بهدف مناقشة التعديلات المقترحة على قانون الانتخابات.",
        "وقال المتحدث باسم الحكومة إن اللقاء ركز على آليات تشكيل لجنة مستقلة للإشراف على الانتخابات المقبلة.",
        "من جانبه، قال ممثل المعارضة إن المحادثات كانت «جدية»، لكنه أوضح أن الخلافات لا تزال قائمة بشأن طريقة اختيار أعضاء اللجنة وصلاحياتها.",
        "ولم يعلن الطرفان التوصل إلى اتفاق نهائي، واتفقا على استئناف الاجتماعات الأسبوع المقبل.",
        "وقالت بعثة الوساطة في بيان إن الطرفين أبديا استعدادًا لمواصلة الحوار، دون أن تشير إلى حدوث تقدم ملموس.",
    ],
)

# Short adversarial / sentence-level cases
SHORT: dict[str, dict] = {}
SHORT["adv-protests-prove-fraud"] = _art(
    "adv-protests-prove-fraud",
    "احتجاجات بعد الانتخابات",
    ["وقالت المعارضة إن الحكومة زورت النتائج، وهو ما أثبتته الاحتجاجات الواسعة لاحقًا."],
)
SHORT["adv-quote-preserve-corrupt"] = _art(
    "adv-quote-preserve-corrupt",
    "تصريح المتحدث",
    ["قال المتحدث: «هذه الحكومة فاسدة بالكامل»."],
)
SHORT["adv-synonym-trap"] = _art(
    "adv-synonym-trap",
    "بيان الأضرار",
    ["قالت الوزارة إن الأضرار «محدودة»."],
)
SHORT["adv-vague-future"] = _art(
    "adv-vague-future",
    "مصدر عن الاستقالة",
    ["بحسب مصادر، فإن الوزير سيستقيل غدًا."],
)
SHORT["adv-plural-singular"] = _art(
    "adv-plural-singular",
    "مصدر مجهول",
    ["قالت مصادر مطلعة، طلبت عدم الكشف عن هويته، إن القرار صدر أمس."],
)
SHORT["adv-final-vs-appeal"] = _art(
    "adv-final-vs-appeal",
    "حكم قضائي",
    ["أُدين المتهم نهائيًا، ولا يزال الحكم قابلًا للاستئناف."],
)
SHORT["adv-pct-sum-103"] = _art(
    "adv-pct-sum-103",
    "نتائج أولية",
    ["حصل المرشح الأول على 48% والثاني على 47%، بينما توزعت النسبة المتبقية البالغة 8% على بقية المرشحين."],
)
SHORT["adv-title-cancel-defer"] = _art(
    "adv-title-cancel-defer",
    "الحكومة تلغي الضريبة الجديدة",
    ["أعلنت الحكومة تأجيل تطبيق الضريبة لمدة ثلاثة أشهر."],
)
SHORT["adv-publisher-after-quote"] = _art(
    "adv-publisher-after-quote",
    "تصريح وزير",
    ["قال الوزير إن المعارضة «تعمل ضد الوطن». وهذا بالفعل ما تثبته مواقفها الأخيرة."],
)
SHORT["adv-similar-names"] = _art(
    "adv-similar-names",
    "لقاء وزاري",
    [
        "اجتمع وزير الخارجية سامر خليل مع رئيس الوزراء سامر جليل، وقال خليل إنه سيزور العاصمة الأسبوع المقبل. وأضاف جليل أن زيارته ستستمر يومين."
    ],
)


def _merge_phrases() -> None:
    path = ROOT / "data" / "lexicons" / "editorial_phrases.json"
    lex = json.loads(path.read_text(encoding="utf-8"))

    def add(bucket: str, entry: dict) -> None:
        items = lex.setdefault(bucket, [])
        if not any(x.get("span") == entry["span"] for x in items):
            items.append(entry)

    phrases = [
        ("evidence_gaps", "ويؤكد ذلك", ["R_PUBLISHER_FACT", "R_EVIDENCE_WEAK"], "publisher_voice", "hard_warning", "high", "تحويل قرائن إلى حقيقة بصوت الناشر."),
        ("evidence_gaps", "تكشف تورط", ["R_EVIDENCE_WEAK"], "unsupported_certainty", "hard_warning", "high", "العنوان يجزم بتورط بينما التحقيق أولي."),
        ("overgeneralizations", "غضبًا شعبيًا واسعًا", ["R_OVERGENERALIZE"], "unsupported_certainty", "hard_warning", "high", "تعميم بلا بيانات."),
        ("overgeneralizations", "فقدت بالفعل شرعيتها", ["R_OVERGENERALIZE", "R_PUBLISHER_FACT"], "publisher_voice", "hard_warning", "high", "حكم تحريري بصوت الناشر."),
        ("evidence_gaps", "ارتباطاتها المشبوهة", ["R_EVIDENCE_WEAK", "R_PUBLISHER_FACT"], "publisher_voice", "hard_warning", "high", "اتهام غير مثبت بصوت الناشر."),
        ("loaded_caption_phrases", "وهذا بالفعل ما تثبته", ["R_PUBLISHER_FACT"], "publisher_voice", "hard_warning", "high", "تبنّي اتهام بعد الاقتباس بصوت الكاتب."),
        ("evidence_gaps", "أثبتته الاحتجاجات", ["R_EVIDENCE_WEAK"], "unsupported_certainty", "hard_warning", "high", "الاحتجاجات لا تثبت الادعاء."),
        ("evidence_gaps", "أصبح من المؤكد", ["R_PUBLISHER_FACT", "R_EVIDENCE_WEAK"], "unsupported_certainty", "hard_warning", "high", "جزم بعد نفي الاتفاق النهائي."),
        ("evidence_gaps", "أكد أنه وافق", ["R_SOURCE_VAGUE"], "attribution", "hard_warning", "high", "مرجع الضمير غامض؛ يحتاج إعادة صياغة."),
        ("vague_sources", "بحسب مصادر", ["R_SOURCE_VAGUE"], "attribution", "hard_warning", "high", "مصدر مجهّل مع تأكيد مستقبلي."),
        ("evidence_gaps", "سيستقيل غدًا", ["R_EVIDENCE_WEAK"], "unsupported_certainty", "soft_warning", "medium", "معلومة مستقبلية بصيغة مؤكدة أكثر من اللازم."),
        ("overgeneralizations", "الشعب أقر القانون", ["R_OVERGENERALIZE", "R_PUBLISHER_FACT"], "publisher_voice", "hard_warning", "high", "مجاز سياسي يُقدَّم كحقيقة مباشرة."),
        ("evidence_gaps", "الوزير السابق كان أحد المستفيدين", ["R_EVIDENCE_WEAK", "R_PUBLISHER_FACT"], "unsupported_certainty", "hard_warning", "high", "اتهام غير مباشر لشخص مسمّى عبر التزامن الزمني."),
        ("evidence_gaps", "زيارته ستستمر", ["R_SOURCE_VAGUE"], "attribution", "soft_warning", "medium", "مرجع الضمير قد يلتبس بين شخصين متشابهين."),
        ("evidence_gaps", "ويعني ذلك أن الحكومة خفضت البطالة فعلًا", ["R_PUBLISHER_FACT"], "publisher_voice", "hard_warning", "high", "تجاهل التفسير البديل وتحويله إلى حقيقة."),
        ("evidence_gaps", "ويؤكد ذلك", ["R_PUBLISHER_FACT", "R_EVIDENCE_WEAK"], "publisher_voice", "hard_warning", "high", "تحويل قرائن إلى حقيقة بصوت الناشر."),
        ("quote_preserve", "مجموعة من العملاء", ["R03"], "quote_voice", "needs_editor_review", "medium", "لغة حادة داخل اقتباس منسوب — لا تُستبدل تلقائيًا."),
        ("quote_preserve", "فاسدة بالكامل", ["R03"], "quote_voice", "needs_editor_review", "medium", "اقتباس منسوب — يُحفظ مع تحذير حساسية فقط."),
        ("quote_preserve", "محدودة", ["R04"], "quote_voice", "needs_editor_review", "low", "لا تستبدل بمرادف قد يغيّر القوة الدلالية."),
        ("quote_preserve", "تعمل ضد الوطن", ["R03"], "quote_voice", "needs_editor_review", "medium", "اقتباس منسوب — لا يُعادت صياغته."),
    ]
    for bucket, span, rules, cat, dec, sev, expl in phrases:
        add(
            bucket,
            {
                "span": span,
                "suggested_text": None,
                "rule_ids": rules,
                "category": cat,
                "decision": dec,
                "severity": sev,
                "explanation_ar": expl,
                "requires_editor_review": True,
                "must_be_quoted": bucket == "quote_preserve",
            },
        )

    path.write_text(json.dumps(lex, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _merge_grammar() -> None:
    path = ROOT / "data" / "lexicons" / "grammar_patterns.json"
    gr = json.loads(path.read_text(encoding="utf-8"))
    existing = {e["span"] for e in gr["patterns"]}
    for entry in [
        {
            "span": "مصادر مطلعة، طلبت عدم الكشف عن هويته",
            "suggested_text": "مصادر مطلعة، طلبت عدم الكشف عن هويتها",
            "rule_ids": ["MECH-GRAMMAR"],
            "category": "grammar",
            "decision": "replace",
            "severity": "medium",
            "explanation_ar": "عدم تطابق الجمع/المفرد: مصادر مقابل هويته.",
            "requires_editor_review": False,
        }
    ]:
        if entry["span"] not in existing:
            gr["patterns"].append(entry)
    path.write_text(json.dumps(gr, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    all_articles = {**ARTICLES, **SHORT}
    for art in all_articles.values():
        (ART / f"{art['article_id']}.json").write_text(
            json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    _merge_phrases()
    _merge_grammar()

    # Dataset splits (no near-duplicates of lexicon spans in hidden set ideally;
    # here we separate by purpose).
    def dump_jsonl(name: str, ids: list[str]) -> None:
        rows = []
        for aid in ids:
            art = all_articles[aid]
            rows.append(
                {
                    "record_id": aid,
                    "article_id": aid,
                    "headline": art["title"],
                    "body": "\n\n".join(
                        s["text"] for s in art["sections"] if s["surface"] != "headline"
                    ),
                    "split": name.replace(".jsonl", ""),
                }
            )
        path = EVAL / name
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
            encoding="utf-8",
        )

    dump_jsonl(
        "validation_set.jsonl",
        [
            "indirect-accusation-v1",
            "quoted-incitement-v1",
            "name-date-chaos-v1",
            "labor-context-math-v1",
            "pronoun-source-v1",
            "majority-precision-v1",
        ],
    )
    dump_jsonl("negative_cases.jsonl", ["clean-talks-v1"])
    dump_jsonl(
        "adversarial_cases.jsonl",
        list(SHORT.keys()),
    )
    dump_jsonl(
        "hidden_test_set.jsonl",
        [
            "adv-title-cancel-defer",
            "adv-final-vs-appeal",
            "adv-pct-sum-103",
            "adv-similar-names",
            "clean-talks-v1",
        ],
    )
    # training_set placeholder: earlier articles if present
    train_ids = [
        p.stem
        for p in ART.glob("*.json")
        if p.stem
        not in set(ARTICLES)
        | set(SHORT)
        | {"clean-talks-v1"}
    ]
    if train_ids:
        rows = []
        for stem in train_ids:
            art = json.loads((ART / f"{stem}.json").read_text(encoding="utf-8"))
            rows.append(
                {
                    "record_id": stem,
                    "article_id": stem,
                    "headline": art.get("title", ""),
                    "body": "\n\n".join(
                        s["text"]
                        for s in art.get("sections", [])
                        if s.get("surface") != "headline"
                    ),
                    "split": "training_set",
                }
            )
        (EVAL / "training_set.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
            encoding="utf-8",
        )

    print(f"wrote {len(all_articles)} fixtures + dataset splits")


if __name__ == "__main__":
    main()
