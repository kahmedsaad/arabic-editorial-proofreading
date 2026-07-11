"""Create multi-article fixtures and expand lexicons for batch scoring."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "evaluation" / "articles"
OUT.mkdir(parents=True, exist_ok=True)

ARTICLES: dict[str, dict] = {}

ARTICLES["econ-plains-v1"] = {
    "article_id": "econ-plains-v1",
    "title": "الحكومة تنقذ الاقتصاد من الإنهيار والمعارضة تواصل نشر الأكاذيب",
    "language": "ar",
    "content_type": "news",
    "sections": [
        {
            "section_id": "headline",
            "surface": "headline",
            "text": "الحكومة تنقذ الاقتصاد من الإنهيار والمعارضة تواصل نشر الأكاذيب",
        },
        {
            "section_id": "p1",
            "surface": "lead",
            "text": "أعلنت وزارة المالية في دولة السهول المتحدة أن الاقتصاد حقق نمواً تاريخياً خلال الربع الثاني من العام الجاري، رغم أن البيانات الرسمية المنشورة على موقع الوزارة أظهرت تراجع الناتج المحلي بنسبة 1.8%.",
        },
        {
            "section_id": "p2",
            "surface": "paragraph",
            "text": "وقال وزير المالية إن الإجراءات الأخيرة أثبتت نجاحها الكبير، وأن المواطنين بدأوا بالفعل يشعرون بتحسن واضح في مستويات المعيشة، رغم أن أسعار الوقود والخبز والمواصلات ارتفعت خلال الشهرين الماضيين.",
        },
        {
            "section_id": "p3",
            "surface": "paragraph",
            "text": "وأكد الوزير أن التضخم انخفض إلى 9%، بينما أشار تقرير البنك المركزي الصادر في اليوم نفسه إلى أن معدل التضخم بلغ 14.6%، وهو ما يعكس تحسناً كبيراً في الأوضاع المالية.",
        },
        {
            "section_id": "p4",
            "surface": "paragraph",
            "text": "وأضاف أن الحكومة لم تفرض أي ضرائب جديدة، لكنها أعلنت في البيان ذاته عن تطبيق رسم تنمية إضافي بنسبة 3% على عدد من الخدمات الأساسية.",
        },
        {
            "section_id": "p5",
            "surface": "paragraph",
            "text": "وقالت مصادر حكومية أن المعارضة تعمدت تضخيم الأزمة الإقتصادية بهدف إثارة المواطنين وتشوية صورة الحكومة في الخارج، كما أكدت أن بعض التقارير السلبية تم تمويلها من جهات أجنبية معادية.",
        },
        {
            "section_id": "p6",
            "surface": "paragraph",
            "text": "ولم توضح المصادر أسماء هذه الجهات، كما لم تقدم أدلة على وجود تمويلات خارجية، إلا أن المؤشرات كلها تؤكد أن هناك مؤامرة منظمة تستهدف استقرار البلاد.",
        },
        {
            "section_id": "p7",
            "surface": "paragraph",
            "text": "من جانبها، قالت جبهة التغيير الوطني إن سياسات الحكومة أدت إلى تراجع قيمة العملة وزيادة معدلات البطالة، وطالبت بإقالة وزير المالية فوراً.",
        },
        {
            "section_id": "p8",
            "surface": "paragraph",
            "text": "ويبدو أن المعارضة تحاول استغلال معاناة المواطنين لتحقيق مكاسب سياسية رخيصة، خاصة بعد فشلها في الفوز بثقة الشعب خلال الانتخابات الماضية.",
        },
        {
            "section_id": "p9",
            "surface": "paragraph",
            "text": "وقال أستاذ الاقتصاد الدكتور سامر نجيب إن الوضع الاقتصادي خطير، وأضاف أن الدين العام تجاوز الحدود الآمنة، لكنه لم يحدد المقصود بالحدود الآمنة أو البيانات التي استند إليها.",
        },
        {
            "section_id": "p10",
            "surface": "paragraph",
            "text": "وفي المقابل، أكد خبير اقتصادي مقرب من الحكومة أن الاقتصاد أصبح أقوى من أي وقت مضى، وأن المستثمرين يتسابقون لدخول السوق، دون ذكر أرقام أو أسماء مستثمرين.",
        },
        {
            "section_id": "p11",
            "surface": "paragraph",
            "text": "وتشير الإحصاءات إلى أن معدل البطالة بلغ 11%، بينما قالت الوزارة في فقرة أخرى إنه لم يتجاوز 8.5%، وأوضح البيان أن عدد العاطلين انخفض رغم زيادة عددهم من 720 ألفاً إلى 860 ألفاً.",
        },
        {
            "section_id": "p12",
            "surface": "paragraph",
            "text": "وفي نهاية البيان، شددت الحكومة على أن كل من يشكك في نجاح الخطة الاقتصادية يخدم أعداء الوطن، وأن المرحلة الحالية لا تحتمل النقد الهدام.",
        },
    ],
}

ARTICLES["north-border-v1"] = {
    "article_id": "north-border-v1",
    "title": "جيش الشمال يسحق المتمردين ويحسم المعركة الحدودية نهائياً",
    "language": "ar",
    "content_type": "breaking_news",
    "sections": [
        {
            "section_id": "headline",
            "surface": "headline",
            "text": "جيش الشمال يسحق المتمردين ويحسم المعركة الحدودية نهائياً",
        },
        {
            "section_id": "p1",
            "surface": "lead",
            "text": "أعلن جيش جمهورية الشمال صباح الأحد أنه تمكن من تحرير المنطقة الحدودية بالكامل بعد اشتباكات عنيفة مع قوات تابعة لإقليم الوادي.",
        },
        {
            "section_id": "p2",
            "surface": "paragraph",
            "text": "وقالت القيادة العسكرية إن العملية جاءت رداً على إعتداءات متكررة نفذتها مليشيات الوادي ضد نقاط المراقبة، مؤكدة أن الجيش لم يبدأ القتال وإنما دافع عن سيادة الدولة.",
        },
        {
            "section_id": "p3",
            "surface": "paragraph",
            "text": "لكن حكومة إقليم الوادي قالت إن قوات الشمال هي التي عبرت الحدود أولاً، وإن الاشتباكات بدأت بعد دخول آليات عسكرية إلى قرية السدر.",
        },
        {
            "section_id": "p4",
            "surface": "paragraph",
            "text": "ولم يتسن التأكد بشكل مستقل من رواية أي من الطرفين، إلا أن شهود عيان أكدوا بلا شك أن قوات الوادي هي التي بدأت الهجوم.",
        },
        {
            "section_id": "p5",
            "surface": "paragraph",
            "text": "وقال أحد السكان إن قذائف سقطت قرب منازل المدنيين، لكنه لم يتمكن من تحديد الجهة التي أطلقتها. ورغم ذلك، أثبتت الحادثة أن قوات الوادي تستخدم المدنيين كدروع بشرية.",
        },
        {
            "section_id": "p6",
            "surface": "paragraph",
            "text": "وأعلنت وزارة الدفاع مقتل 12 جندياً وإصابة 18 آخرين، بينما ذكر بيان لاحق أن إجمالي الخسائر العسكرية بلغ 21 فقط.",
        },
        {
            "section_id": "p7",
            "surface": "paragraph",
            "text": "كما أفادت السلطات بمقتل 7 مدنيين، من بينهم 4 أطفال و5 نساء، دون توضيح سبب تجاوز المجموع للعدد المعلن.",
        },
        {
            "section_id": "p8",
            "surface": "paragraph",
            "text": "وأكد قائد الجيش أن قواته لم تستهدف أي مناطق سكنية، لكنه أشار في المقابلة نفسها إلى أن الطيران قصف مواقع داخل ثلاث قرى حدودية.",
        },
        {
            "section_id": "p9",
            "surface": "paragraph",
            "text": "ووصف التلفزيون الرسمي قوات الوادي بالعصابات الإرهابية، رغم أن الحكومة لم تصدر تصنيفاً قانونياً بحقها.",
        },
        {
            "section_id": "p10",
            "surface": "paragraph",
            "text": "وقال محلل عسكري إن المعركة انتهت نهائياً لصالح جيش الشمال، وإن الطرف الآخر لن يستطيع شن أي هجوم جديد، لكنه حذر في الجملة التالية من احتمال تجدد القتال في أي لحظة.",
        },
        {
            "section_id": "p11",
            "surface": "paragraph",
            "text": "وفي العاصمة، خرج الآلاف للاحتفال بالنصر الساحق، بحسب وسائل إعلام حكومية، بينما أظهرت الصور المنشورة تجمعات محدودة في ميدان واحد.",
        },
        {
            "section_id": "p12",
            "surface": "paragraph",
            "text": "وأعلنت وزارة الخارجية أن الدولة ملتزمة بالحل السلمي، في الوقت الذي صرح فيه وزير الدفاع بأن القوة هي اللغة الوحيدة التي يفهمها الخصم.",
        },
        {
            "section_id": "p13",
            "surface": "paragraph",
            "text": "وتتهم منظمات حقوقية كلا الطرفين بارتكاب انتهاكات، إلا أن هذه المنظمات معروفة بعدائها الدائم للدولة ولا يمكن الوثوق بتقاريرها.",
        },
    ],
}

ARTICLES["elections-v1"] = {
    "article_id": "elections-v1",
    "title": "فوز كاسح للرئيس بعد إنتخابات نزيهة شهدت بعض المخالفات البسيطة",
    "language": "ar",
    "content_type": "news",
    "sections": [
        {
            "section_id": "headline",
            "surface": "headline",
            "text": "فوز كاسح للرئيس بعد إنتخابات نزيهة شهدت بعض المخالفات البسيطة",
        },
        {
            "section_id": "p1",
            "surface": "lead",
            "text": "أعلنت اللجنة العليا للانتخابات فوز الرئيس كمال الرفاعي بولاية جديدة بعد حصوله على 68% من الأصوات، في إنتخابات وصفتها الحكومة بأنها الأكثر نزاهة في تاريخ البلاد.",
        },
        {
            "section_id": "p2",
            "surface": "paragraph",
            "text": "وقالت اللجنة إن نسبة المشاركة بلغت 74%، بينما أظهر الجدول التفصيلي المنشور في التقرير أن عدد المصوتين بلغ 3.2 مليون من أصل 6 ملايين ناخب.",
        },
        {
            "section_id": "p3",
            "surface": "paragraph",
            "text": "وأكد رئيس اللجنة أن العملية مرت دون أي خروقات مؤثرة، لكنه أقر بتعطيل التصويت في 120 مركزاً، ومنع عدد من المراقبين من الدخول، وتأخر فتح بعض اللجان لأكثر من خمس ساعات.",
        },
        {
            "section_id": "p4",
            "surface": "paragraph",
            "text": "وقالت بعثة مراقبة محلية إن الانتخابات شهدت ضغوطاً على الموظفين للتصويت للرئيس، كما رصدت استخدام سيارات حكومية في نقل الناخبين إلى المؤتمرات الانتخابية.",
        },
        {
            "section_id": "p5",
            "surface": "paragraph",
            "text": "ورفضت الحكومة التقرير، معتبرة أن البعثة منحازة للمعارضة، ولم ترد بالتفصيل على الوقائع المذكورة فيه.",
        },
        {
            "section_id": "p6",
            "surface": "paragraph",
            "text": "وفي مؤتمر صحفي، قال المتحدث باسم الحزب الحاكم إن الشعب جدد ثقته الكاملة في الرئيس، وإن النتيجة تعكس إجماعاً وطنياً لا يقبل التشكيك.",
        },
        {
            "section_id": "p7",
            "surface": "paragraph",
            "text": "لكن مرشح المعارضة حصل على 29% من الأصوات، بينما ذهبت النسبة المتبقية إلى مرشحين آخرين، وهو ما لا ينسجم مع وصف النتيجة بأنها إجماع كامل.",
        },
        {
            "section_id": "p8",
            "surface": "paragraph",
            "text": "واتهم مرشح المعارضة اللجنة بتغيير النتائج في عدد من الدوائر، وقال إن لديه أدلة قاطعة، لكنه لم ينشرها حتى الآن.",
        },
        {
            "section_id": "p9",
            "surface": "paragraph",
            "text": "وذكرت وسائل إعلام موالية للحكومة أن المعارضة تحاول سرقة فرحة الشعب، وأن كل من يرفض النتيجة يرفض الإرادة الوطنية.",
        },
        {
            "section_id": "p10",
            "surface": "paragraph",
            "text": "وقال محلل سياسي إن فوز الرئيس كان متوقعاً لأن المواطنين يحبونه ويثقون بحكمته، دون الإشارة إلى أي استطلاع مستقل.",
        },
        {
            "section_id": "p11",
            "surface": "paragraph",
            "text": "كما أعلن التلفزيون الرسمي أن مراقبين دوليين أشادوا بنزاهة الانتخابات، بينما أوضحت البعثة الدولية في بيانها أنها سجلت مخالفات خطيرة تتطلب التحقيق.",
        },
        {
            "section_id": "p12",
            "surface": "paragraph",
            "text": "وفي إحدى الفقرات، ذكر التقرير أن الانتخابات جرت يوم السبت 15 سبتمبر، ثم أشار في فقرة لاحقة إلى أن التصويت بدأ صباح الأحد 15 سبتمبر.",
        },
    ],
}

ARTICLES["health-wave-v1"] = {
    "article_id": "health-wave-v1",
    "title": "الحكومة تقضي نهائياً على الوباء والمعارضة تنشر الذعر بين المواطنين",
    "language": "ar",
    "content_type": "news",
    "sections": [
        {
            "section_id": "headline",
            "surface": "headline",
            "text": "الحكومة تقضي نهائياً على الوباء والمعارضة تنشر الذعر بين المواطنين",
        },
        {
            "section_id": "p1",
            "surface": "lead",
            "text": "أعلنت وزارة الصحة انتهاء موجة وباء الحمى الموسمية بشكل كامل، مؤكدة أن المستشفيات لم تعد تستقبل أي حالات خطيرة.",
        },
        {
            "section_id": "p2",
            "surface": "paragraph",
            "text": "وفي البيان نفسه، طلبت الوزارة من المستشفيات رفع درجة الاستعداد القصوى بسبب الزيادة المفاجئة في أعداد المصابين.",
        },
        {
            "section_id": "p3",
            "surface": "paragraph",
            "text": "وقال الوزير إن عدد الإصابات انخفض إلى 500 حالة أسبوعياً، بينما أوضحت النشرة اليومية تسجيل 820 حالة خلال يوم واحد.",
        },
        {
            "section_id": "p4",
            "surface": "paragraph",
            "text": "وأضاف أن جميع اللقاحات المستخدمة آمنة بنسبة 100%، وأنه لم تسجل أي آثار جانبية، رغم أن هيئة الدواء أعلنت تلقي 43 بلاغاً عن أعراض جانبية محتملة.",
        },
        {
            "section_id": "p5",
            "surface": "paragraph",
            "text": "واتهم الوزير صفحات تابعة للمعارضة بنشر معلومات كاذبة عن نقص الأدوية، مؤكداً أن كل المستشفيات لديها مخزون كافي.",
        },
        {
            "section_id": "p6",
            "surface": "paragraph",
            "text": "لكن مراسل الصحيفة زار مستشفيين في العاصمة وقال أطباء فيهما إن بعض الأدوية الأساسية غير متوفرة منذ أسبوع.",
        },
        {
            "section_id": "p7",
            "surface": "paragraph",
            "text": "ولم يتسن الحصول على تعليق من الوزارة بشأن هذه الشهادات، إلا أن مسؤولاً حكومياً قال إن الأطباء الذين تحدثوا للإعلام قد يكونون جزءاً من حملة سياسية.",
        },
        {
            "section_id": "p8",
            "surface": "paragraph",
            "text": "وقالت المعارضة إن الحكومة تخفي الأرقام الحقيقية للوفيات، واستندت إلى صور متداولة على الإنترنت لم يتم التحقق من مكانها أو تاريخها.",
        },
        {
            "section_id": "p9",
            "surface": "paragraph",
            "text": "وذكرت الوزارة أن عدد الوفيات بلغ 18 حالة، بينما أشار تقرير المستشفيات إلى 27 حالة، ثم قال الوزير لاحقاً إن العدد لم يتجاوز 15.",
        },
        {
            "section_id": "p10",
            "surface": "paragraph",
            "text": "وأكدت الحكومة أن الوضع تحت السيطرة تماماً، لكنها فرضت حظر تجول جزئياً وأغلقت المدارس لمدة أسبوعين.",
        },
    ],
}


def main() -> None:
    for art in ARTICLES.values():
        path = OUT / f"{art['article_id']}.json"
        path.write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Also keep marfa if present
    marfa = ROOT / "data" / "evaluation" / "marfa_article.json"
    if marfa.exists():
        payload = json.loads(marfa.read_text(encoding="utf-8"))
        (OUT / "custom-marfa-chaos-v1.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    sp_path = ROOT / "data" / "spelling" / "replacements.json"
    sp = json.loads(sp_path.read_text(encoding="utf-8"))
    sp.update(
        {
            "الإنهيار": "الانهيار",
            "الإقتصادية": "الاقتصادية",
            "تشوية": "تشويه",
            "إعتداءات": "اعتداءات",
            "إنتخابات": "انتخابات",
            "مخزون كافي": "مخزون كافٍ",
            "مليشيات": "ميليشيات",
        }
    )
    sp_path.write_text(json.dumps(sp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lex_path = ROOT / "data" / "lexicons" / "editorial_phrases.json"
    lex = json.loads(lex_path.read_text(encoding="utf-8"))

    def add(bucket: str, entry: dict) -> None:
        items = lex.setdefault(bucket, [])
        spans = {x.get("span") for x in items}
        if entry["span"] not in spans:
            items.append(entry)

    phrases = [
        (
            "loaded_caption_phrases",
            "أكاذيب",
            ["R03"],
            "loaded_framing",
            "hard_warning",
            "high",
            "لغة قدحية/تحريضية.",
        ),
        (
            "loaded_caption_phrases",
            "أعداء الوطن",
            ["R03"],
            "loaded_framing",
            "hard_warning",
            "high",
            "لغة تحريضية ضد الخصوم.",
        ),
        (
            "loaded_caption_phrases",
            "مكاسب سياسية رخيصة",
            ["R03", "R_PUBLISHER_FACT"],
            "publisher_voice",
            "hard_warning",
            "high",
            "رأي/تحريض بصوت الناشر.",
        ),
        (
            "loaded_caption_phrases",
            "يسحق المتمردين",
            ["R03"],
            "loaded_framing",
            "hard_warning",
            "high",
            "لغة عسكرية منحازة في العنوان.",
        ),
        (
            "loaded_caption_phrases",
            "النصر الساحق",
            ["R03"],
            "loaded_framing",
            "hard_warning",
            "high",
            "تضخيم دعائي.",
        ),
        (
            "loaded_caption_phrases",
            "العصابات الإرهابية",
            ["R_TERROR_LABEL", "R03"],
            "loaded_framing",
            "hard_warning",
            "high",
            "وصف بالإرهاب دون تصنيف قانوني ظاهر.",
        ),
        (
            "evidence_gaps",
            "كدروع بشرية",
            ["R_EVIDENCE_WEAK"],
            "unsupported_certainty",
            "hard_warning",
            "high",
            "استنتاج غير مدعوم بما يكفي.",
        ),
        (
            "evidence_gaps",
            "أكدوا بلا شك",
            ["R_EVIDENCE_WEAK"],
            "unsupported_certainty",
            "hard_warning",
            "high",
            "قطع بعد تعذر التحقق المستقل.",
        ),
        (
            "evidence_gaps",
            "المؤشرات كلها تؤكد",
            ["R_PUBLISHER_FACT"],
            "publisher_voice",
            "hard_warning",
            "high",
            "تأكيد قطعي دون تحديد المؤشرات.",
        ),
        (
            "overgeneralizations",
            "المستثمرين يتسابقون",
            ["R_OVERGENERALIZE"],
            "unsupported_certainty",
            "soft_warning",
            "medium",
            "تعميم غير مثبت.",
        ),
        (
            "overgeneralizations",
            "إجماعاً وطنياً",
            ["R_OVERGENERALIZE"],
            "unsupported_certainty",
            "hard_warning",
            "high",
            "تعميم لا ينسجم مع نسب منافسة معتبرة.",
        ),
        (
            "overgeneralizations",
            "إجماع كامل",
            ["R_OVERGENERALIZE"],
            "unsupported_certainty",
            "hard_warning",
            "high",
            "تعميم لا ينسجم مع نسب منافسة معتبرة.",
        ),
        (
            "loaded_caption_phrases",
            "فرحة الشعب",
            ["R03", "R_OVERGENERALIZE"],
            "loaded_framing",
            "soft_warning",
            "medium",
            "عبارة دعائية.",
        ),
        (
            "loaded_caption_phrases",
            "الإرادة الوطنية",
            ["R03", "R_OVERGENERALIZE"],
            "loaded_framing",
            "soft_warning",
            "medium",
            "عبارة دعائية.",
        ),
        (
            "evidence_gaps",
            "آمنة بنسبة 100%",
            ["R_EVIDENCE_WEAK"],
            "unsupported_certainty",
            "hard_warning",
            "high",
            "ادعاء يقين مطلق.",
        ),
        (
            "loaded_caption_phrases",
            "تنشر الذعر",
            ["R03"],
            "loaded_framing",
            "hard_warning",
            "high",
            "لغة تحريضية ضد المعارضة.",
        ),
        (
            "evidence_gaps",
            "لا يمكن الوثوق بتقاريرها",
            ["R_EVIDENCE_WEAK"],
            "unsupported_certainty",
            "hard_warning",
            "high",
            "مهاجمة المصدر بدل مناقشة الأدلة.",
        ),
        (
            "evidence_gaps",
            "تمويلها من جهات أجنبية",
            ["R_EVIDENCE_WEAK"],
            "unsupported_certainty",
            "hard_warning",
            "high",
            "اتهام تمويل أجنبي دون أدلة ظاهرة.",
        ),
        (
            "evidence_gaps",
            "أدلة قاطعة",
            ["R_EVIDENCE_WEAK"],
            "unsupported_certainty",
            "soft_warning",
            "medium",
            "ادعاء امتلاك أدلة دون نشرها.",
        ),
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
            },
        )
    lex_path.write_text(json.dumps(lex, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    gr_path = ROOT / "data" / "lexicons" / "grammar_patterns.json"
    gr = json.loads(gr_path.read_text(encoding="utf-8"))
    existing = {e["span"] for e in gr["patterns"]}
    for entry in [
        {
            "span": "مخزون كافي",
            "suggested_text": "مخزون كافٍ",
            "rule_ids": ["MECH-GRAMMAR"],
            "category": "grammar",
            "decision": "replace",
            "severity": "medium",
            "explanation_ar": "خطأ نحوي شائع: كافٍ لا كافي.",
            "requires_editor_review": False,
        }
    ]:
        if entry["span"] not in existing:
            gr["patterns"].append(entry)
    gr_path.write_text(json.dumps(gr, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(list(OUT.glob('*.json')))} article fixtures")


if __name__ == "__main__":
    main()
