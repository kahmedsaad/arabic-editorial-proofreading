# Arabic editorial calibration packet

> AI labels are calibration evidence, not editorial truth. Reviewer fields are intentionally blank.

## Deterministic selection method

- Input: `C:/Users/khhab/Downloads/ai-proofreading/data/evaluation/analysis/editorial_labels_run3/expert_labels.jsonl` (163 rows, source order by `source_index`).
- Fixed decision quotas: 10 `keep`, 15 `drop`, 5 `uncertain`.
- Within each fixed category stratum below, select the lowest available `source_index`; no random seed or manual substitution.
- Keep strata: headline 4, numeric 3, spelling 1, repetition 1, grammar/consistency 1.
- Drop strata: attribution 3, clarity 3, loaded framing 2, entity 2, headline 2, spelling 2, repetition 1.
- Uncertain strata: numeric 3, entity confusion 1, headline 1.
- Duplicate markers use exact article + category + original span + explanation groups across all 163 rows.

## Reviewer instructions

For each item, choose exactly one: `agree | change_to_keep | change_to_drop | change_to_uncertain`.
Do not edit the current AI decision in this packet; record a proposed change and evidence in reviewer notes.

## 1. `gemini_run3:ANAD-015348:FND-AI-0001`

- **Source index / category:** `40` / `headline_body_mismatch`
- **Headline:** مايكروسوفت تفتح برنامج Windows Live Messenger
- **Necessary source context:** نشرت بعض المواقع المتخصصة في العالم التقني على شبكة الإنترنت، بما في ذلك موقع liveside.net، خبراً مفاده أن شركة مايكروسوفت أتاحت برنامج التراسل الفوري (Windows Live Messenger) بصورة غير معلنة لكافة المستخدمين الذين يتمتعون بعضوية في خدمة Microsoft Passport. وقد كان الدخول إلى هذا البرنامج محصور بهؤلاء الذين تلقوا دعوة لذلك، الأمر الذي أحبط المستخدمين الآخرين…
- **Model finding:** يتناقض العنوان الذي يفيد بأن مايكروسوفت 'تفتح' البرنامج بشكل قاطع مع نص المقال الذي يذكر أن البرنامج 'لا يزال يتطلب دعوة للدخول' وأن الخبر مستند إلى 'بعض المواقع المتخصصة' وليس إعلاناً رسمياً من مايكروسوفت بفتحه للجميع.
- **Original span → proposed edit:** `مايكروسوفت تفتح برنامج Windows Live Messenger` → `—`
- **Current AI decision:** `keep`
- **AI rationale / confidence:** Material contradiction claimed between headline/body (or internal spans). / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 2. `gemini_run3:ANAD-049216:FND-AI-0001`

- **Source index / category:** `41` / `headline_body_mismatch`
- **Headline:** تعرف على أبرز سيارات السيدان الجديدة كليا المتاحة في 2019
- **Necessary source context:** …صدارات في عالم السيارات وسط منافسة كبيرة بين المركبات السيدان والكروس أوفر التي تسجل نموا كبيرا. تعرض القائمة التالية أبرز السيارات السيدان الجديدة كليا أو التي شهدت تغييرات ملحوظة في التصميم فضلا عن أسعارها التقريبية بالدولار.
- **Model finding:** يصف العنوان السيارات بأنها 'جديدة كليا'، بينما يوضح متن المقال (SEG-002) أن القائمة ستشمل 'السيارات السيدان الجديدة كليا أو التي شهدت تغييرات ملحوظة في التصميم'. هذا التناقض قد يضلل القارئ حول محتوى المقال.
- **Original span → proposed edit:** `الجديدة كليا` → `الجديدة أو المحدثة`
- **Current AI decision:** `keep`
- **AI rationale / confidence:** Material contradiction claimed between headline/body (or internal spans). / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 3. `gemini_run3:ANAD-136139:FND-AI-1`

- **Source index / category:** `42` / `headline_body_mismatch`
- **Headline:** الشباب يتعادل مع فيلنو في معسكر هولندا
- **Necessary source context:** حسم التعادل السلبي نتيجة لقاء الشباب الودي مع نظيره الهولندي فيلنو والتي أقيمت في إطار معسكر الفريق بالنمسا. وبدأ فريق الشباب اللقاء بتشكيل مكون من: وليد والأسطا والفهد وسند وحسن وعبدالمجيد الصليهم والسليطين والخيبري وجعفر وهيبرتي وبن يطو. وسيلتقي الشباب يوم الخميس مع هيلينورد الهولندي في رابع وأخر ودياته بمسكره في هولندا استعداداً للموسم الجديد. وينتهي معسك…
- **Model finding:** تتناقض معلومات الموقع الجغرافي للمباراة المذكورة في العنوان مع ما ورد في الفقرة الأولى من النص. العنوان يذكر أن المباراة كانت في 'معسكر هولندا'، بينما النص يوضح أنها أقيمت في 'معسكر الفريق بالنمسا'.
- **Original span → proposed edit:** `الشباب يتعادل مع فيلنو في معسكر هولندا` → `—`
- **Current AI decision:** `keep`
- **AI rationale / confidence:** Material contradiction claimed between headline/body (or internal spans). / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 4. `gemini_run3:ANAD-211552:FND-AI-0001`

- **Source index / category:** `43` / `headline_body_mismatch`
- **Headline:** الخارجية تعلن إطلاق سراح 6 مصريين كانوا مختطفين بليبيا
- **Necessary source context:** وزارة الخارجية المصرية إطلاق سراح 6 #مصريين كانوا مختطفين في ليبيا., وصرح المستشار أحمد أبو زيد، المتحدث الرسمي باسم #وزارة_الخارجية بأن السفارة المصرية في طرابلس، التي تمارس مهامها من القاهرة بسبب الأوضاع في الأراضي الليبية، علمت أن المواطنين المصريين الستة الذين تم استيقافهم في طريق عودتهم من طرابلس محتجزون حاليا لدى السلطات المحلية بمدينة بني وليد، وجارٍ …
- **Model finding:** العنوان يشير إلى 'إطلاق سراح' المواطنين المصريين، بينما يوضح متن الخبر لاحقًا (في SEG-002) أنهم 'محتجزون حاليًا لدى السلطات المحلية' وأن العمل جارٍ على اتخاذ الترتيبات لعودتهم. هذا التناقض بين العنوان ومحتوى الخبر قد يضلل القارئ حول الوضع الفعلي للمواطنين.
- **Original span → proposed edit:** `الخارجية تعلن إطلاق سراح 6 مصريين كانوا مختطفين بليبيا` → `—`
- **Current AI decision:** `keep`
- **AI rationale / confidence:** Material contradiction claimed between headline/body (or internal spans). / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 5. `gemini_run3:ANAD-392361:FND-AI-1`

- **Source index / category:** `128` / `numeric_contradiction`
- **Headline:** أمام الأخضر 3 انتصارات لسكر الرقم الأفضل
- **Necessary source context:** ون أمام المنتخب السعودي لكرة القدم تحقيق ثلاث انتصارات متتالية لكسر رقمه السابق عام 2001 بتحقيق عدد أكبر بالفوز المتتالي، حيث نجح في عام 2001 في تحقيق عشرة انتصارات متتالية. وسجل الأخضر بفوزه على اليابان 1/0 الخميس الماضي لحساب الجولة الثالثة من التصفيات الآسيوية الحاسمة والمؤهلة لنهائيات كأس العالم 2022 في قطر، ثماني انتصارات متتالية، وتبقى له تحقيق انتصاري…
- **Model finding:** العدد المذكور للانتصارات في العنوان (3) يتعارض مع العدد المذكور في متن المقال (ثماني انتصارات متتالية).
- **Original span → proposed edit:** `3 انتصارات` → `8 انتصارات`
- **Current AI decision:** `keep`
- **AI rationale / confidence:** Internal numeric contradiction claimed between spans. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 6. `gemini_run3:ANAD-392361:FND-AI-4`

- **Source index / category:** `129` / `numeric_contradiction`
- **Headline:** أمام الأخضر 3 انتصارات لسكر الرقم الأفضل
- **Necessary source context:** ون أمام المنتخب السعودي لكرة القدم تحقيق ثلاث انتصارات متتالية لكسر رقمه السابق عام 2001 بتحقيق عدد أكبر بالفوز المتتالي، حيث نجح في عام 2001 في تحقيق عشرة انتصارات متتالية. وسجل الأخضر بفوزه على اليابان 1/0 الخميس الماضي لحساب الجولة الثالثة…
- **Model finding:** العدد المذكور للانتصارات في بداية المقال (ثلاث انتصارات) يتعارض مع العدد المذكور لاحقًا في نفس المقال (ثماني انتصارات متتالية).
- **Original span → proposed edit:** `ثلاث انتصارات متتالية` → `ثماني انتصارات متتالية`
- **Current AI decision:** `keep`
- **AI rationale / confidence:** Internal numeric contradiction claimed between spans. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 7. `gemini_run3:SANAD-039318:FND-AI-1`

- **Source index / category:** `132` / `numeric_contradiction`
- **Headline:** سجل مؤشر الرقم القياسي العام لتكلفة المعيشة في السعودية لشهر أغسطس الماضي مقارنة بنظيره من العام السابق، ارتفاعاً بنسبة 2
- **Necessary source context:** سجل مؤشر الرقم القياسي العام لتكلفة المعيشة في السعودية لشهر أغسطس الماضي مقارنة بنظيره من العام السابق، ارتفاعاً بنسبة 2.8%، وذلك نتيجة الارتفاع الذي شهدته الأقسام الرئيسية المكونة للرقم القياسي لتكلفة المعيشة في مؤشراتها القياسية. وأوضحت مصلحة الإحصاءات العامة والمعلومات في تقريرها الشهري أن قسم ال…
- **Model finding:** توجد نسبة ارتفاع غير مكتملة في العنوان (2) بينما يذكر نص المقال النسبة الصحيحة (2.8%). يجب أن تتطابق النسبة في العنوان مع النص لتجنب التناقض.
- **Original span → proposed edit:** `2` → `2.8%`
- **Current AI decision:** `keep`
- **AI rationale / confidence:** Internal numeric contradiction claimed between spans. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 8. `gemini_run3:ANAD-096823:FND-AI-1`

- **Source index / category:** `144` / `spelling`
- **Headline:** "الدويش": أخطاء التحكيم جزء من اللعبة عبارة هلالية
- **Necessary source context:** علق الإعلامي الرياضي محمد الدويش على عبارة "أخطاء التحكيم جزء من اللعبة"، مشيرًا إلى أن الهلال هو من يستخدم تلك العبارة. وكتب الدويش عبر تويتر: "أخطاء التحكيم جزءٌ من اللعبة عبارة هلالية، تعني أنّ أخطاء التحكيم في كل بطولة". وأض…
- **Model finding:** خطأ إملائي في كلمة "أخطا" داخل اقتباس مباشر. يجب أن تكون "أخطاء". نظرًا للتعليمات بعدم إعادة صياغة الاقتباسات المنسوبة، يتم وضع علامة على هذا الأمر لمراجعة المحرر.
- **Original span → proposed edit:** `أخطا` → `—`
- **Current AI decision:** `keep`
- **AI rationale / confidence:** Flags possible typo inside quote without rewriting quote — useful editor note. / `medium`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 9. `gemini_run3:SANAD-068864:FND-M-0003`

- **Source index / category:** `147` / `repetition`
- **Headline:** أخبارنا المغربية : المهدي الوافي علمت أخبارنا من مصادر رسمية أن رئيس الحكومة دعا زعماء الأحزاب المتحالفة معه إلى اجتماع عاجل سيحتضنه بيته بحي الليمون هذا المساء
- **Necessary source context:** …كيران يهدف من خلال اجتماعه هذا إلى ترميم الصفوف خاصة بعد التناقض الكبير في المواقف داخل مكونات الحكومة بشأن ملف الأساتذة المتدربين وما تلاه من من حرب للمراسلات الوزارية.
- **Model finding:** تكرار كلمة متجاورة.
- **Original span → proposed edit:** `من من` → `من`
- **Current AI decision:** `keep`
- **AI rationale / confidence:** Objective adjacent duplicate word. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 10. `gemini_run3:ANAD-207095:FND-AI-0004`

- **Source index / category:** `142` / `consistency`
- **Headline:** تظاهرات تطالب قطر بمنع ترحيل مسلم من الإيغور إلى الصين
- **Necessary source context:** ناشطون من الإيغور في الصين أمس السبت، أمام سفارة قطر في واشنطن لمطالبة الدوحة بعدم إبعاد الناشط ابليكيم يوسف إلى الصين خوفاً على حياته لأنه مهدد بالموت والاعتقال هناك., وانتشر هاشتاغ #لا_لترحيل_ابليكيم_يوسف لدعم الناشط البالغ من العمر 53 عاماً والعالق في مطار الدوحة., ولفت يوسف الانتباه بعد أن نشر فيديو عبر الهاتف الجوال يطلب المساعدة خوفا من الترحيل إلى الص…
- **Model finding:** يوجد تضارب في اسم الناشط المعني، حيث يُشار إليه باسم "ابليكيم يوسف" في بداية المقال وفي الهاشتاغ، ثم يُشار إليه باسم "عبدالحكيم يوسف" لاحقًا. يجب توحيد الاسم المستخدم لتجنب الالتباس.
- **Original span → proposed edit:** `عبدالحكيم يوسف` → `—`
- **Current AI decision:** `keep`
- **AI rationale / confidence:** Name inconsistency across article is editorially actionable. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 11. `gemini_run3:SANAD-036358:FND-E-0004`

- **Source index / category:** `10` / `attribution`
- **Headline:** أخبارنا المغربية : حنان سلامة كشفت وسائل إعلام فرنسية أن البرلمان الأوروبي سيتدارس مشروع قانون جديد يقضي بوقف استيراد الفوسفاط من المغرب بعد ظهور تقارير تفيد بك…
- **Necessary source context:** أخبارنا المغربية : حنان سلامة كشفت وسائل إعلام فرنسية أن البرلمان الأوروبي سيتدارس مشروع قانون جديد يقضي بوقف استيراد الفوسفاط من المغرب بعد ظهور تقارير تفيد بكون مكوناته غير مطابقة للمعايير المعمول به أوروبيا. وأضافت ذات المص…
- **Model finding:** إسناد إعلامي مبهم.
- **Original span → proposed edit:** `وسائل إعلام` → `—`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** Attribution nag without a demonstrated unsupported factual leap. / `medium`
- **Duplicate-pattern source indices:** `10, 11`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 12. `gemini_run3:SANAD-036358:FND-E-0005`

- **Source index / category:** `11` / `attribution`
- **Headline:** أخبارنا المغربية : حنان سلامة كشفت وسائل إعلام فرنسية أن البرلمان الأوروبي سيتدارس مشروع قانون جديد يقضي بوقف استيراد الفوسفاط من المغرب بعد ظهور تقارير تفيد بك…
- **Necessary source context:** أخبارنا المغربية : حنان سلامة كشفت وسائل إعلام فرنسية أن البرلمان الأوروبي سيتدارس مشروع قانون جديد يقضي بوقف استيراد الفوسفاط من المغرب بعد ظهور تقارير تفيد بكون مكوناته غير مطابقة للمعايير المعمول به أوروبيا. وأضافت ذات المص…
- **Model finding:** إسناد إعلامي مبهم.
- **Original span → proposed edit:** `وسائل إعلام` → `—`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** Attribution nag without a demonstrated unsupported factual leap. / `medium`
- **Duplicate-pattern source indices:** `10, 11`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 13. `gemini_run3:ANAD-213771:FND-AI-0002`

- **Source index / category:** `0` / `attribution`
- **Headline:** مصر.. 3 قتلى في تفجير بالشيخ زويد بسيناء
- **Necessary source context:** 3 مصرعهم وأصيب آخرون بتفجير مدرعة بالشيخ زويد بشمال سيناء., وذكرت مصادر قبلية أن إرهابيين فجروا عن بعد عبوة ناسفة في مدرعة بمنطقة جرادة غرب مدينة الشيخ زويد، ما أسفر عن تدمير المدرعة ومقتل 3 بداخلها وإصابة آخرين., وأضافوا أنه تم فرض طوق أمني حول موقع الحادث…
- **Model finding:** استخدام مصدر مبهم 'مصادر قبلية' لخبر حساس يتضمن وفيات وعمل إرهابي، مما يقلل من موثوقية الخبر ويجعل التحقق صعباً. القاعدة R_SOURCE_VAGUE توصي بتسمية المصدر أو تخفيف قوة الإسناد.
- **Original span → proposed edit:** `مصادر قبلية` → `—`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** Vague-source phrasing is common published journalism; not a clear defect on silence-set external corpora (not AJ house style). / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 14. `gemini_run3:SANAD-057777:FND-AI-0001`

- **Source index / category:** `63` / `clarity`
- **Headline:** بالفيديو
- **Necessary source context:** بالفيديو.. الشروط الواجب توفرها في أضحية العيد السليمة إن كنت تستعدين لشراء أضحية العيد، فعليك اكتشاف الشروط الواجب توفرها ليكون الخروف سليما معافيا، خاليا من أي أمراض. وهذا الفيديو يكشف ل…
- **Model finding:** العنوان الرئيسي غير وصفي ويفتقر إلى المعلومات الأساسية حول محتوى المقال، مما قد يؤثر على وضوح المحتوى وقابليته للاكتشاف. العنوان الفعلي للمحتوى يبدو أنه موجود في الفقرة الأولى من النص.
- **Original span → proposed edit:** `بالفيديو` → `الشروط الواجب توفرها في أضحية العيد السليمة`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** Headline rewrite preference without a concrete comprehension failure. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 15. `gemini_run3:ANAD-000848:FND-M-0010`

- **Source index / category:** `64` / `clarity`
- **Headline:** شعراء كأنهم مديرو علاقات عامة وآخرون زاهدون حتى الغياب
- **Necessary source context:** للشعراء طرقٌ كثيرةٌ للتعبير عن ذواتهم، والإعلان عن وجودهم، بصفتهم تجارب شعرية ثابتة على الأرض، ولكن على ما يبدو أن هناك اتجاهين أو خطين واضحين لمثل هذا الإعلان؛ هذان الخطان مختلفان تمام الاختلاف: الأ…
- **Model finding:** مقطع طويل جداً قد يحتاج إعادة تقسيم.
- **Original span → proposed edit:** `للشعراء طرقٌ كثيرةٌ` → `—`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** Long-paragraph split preference; no concrete ambiguity. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 16. `gemini_run3:ANAD-029457:FND-M-0005`

- **Source index / category:** `65` / `clarity`
- **Headline:** نسخة سكايب لويندوز 8 قادمة قريباً
- **Necessary source context:** ترددت مؤخراً بعض الأخبار حول نية شركة سكايب توفير نسخة جديدة من برنامجها الشهير خاصة بأجهزة سيرفس التي تعمل بنظام ويندوز 8 الجديد مع اقتراب موعد إطلاقه رسمياً، بإصداريه ويندوز 8 وويندوز آر تي، في السا…
- **Model finding:** مقطع طويل جداً قد يحتاج إعادة تقسيم.
- **Original span → proposed edit:** `ترددت مؤخراً بعض الأ` → `—`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** Long-paragraph split preference; no concrete ambiguity. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 17. `gemini_run3:ANAD-213202:FND-AI-1`

- **Source index / category:** `97` / `loaded_framing`
- **Headline:** ما هما القاعدتان العسكريتان اللتان استهدفتهما إيران؟
- **Necessary source context:** ميليشيا الحرس الثوري الإيرانية، الثلاثاء، أنها نفذت هجوما صاروخيا على قاعدة عين الأسد في محافظة الأنبار غرب العراق، وقاعدة حرير في أربيل، والاثنتين تضمان قوات أميركية، فما هما هاتين القاعدتين اللتين ضربتهما إير…
- **Model finding:** وصف "الحرس الثوري الإيراني" بـ "ميليشيا" قد يعتبر تحيزًا أو تسييسًا، حيث أنه جزء من القوات المسلحة الرسمية لدولة ذات سيادة. يجب استخدام وصف محايد مثل "الحرس الثوري الإيراني" أو "القوات الإيرانية".
- **Original span → proposed edit:** `ميليشيا الحرس الثوري الإيرانية` → `الحرس الثوري الإيراني`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** Militia/loaded label rule is AJ house-style policy; external published copy on silence set should not be treated as FP-worthy by default. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 18. `gemini_run3:ANAD-247893:FND-AI-0001`

- **Source index / category:** `98` / `loaded_framing`
- **Headline:** مقتل العشرات من الحوثيين في معسكر تدريبي في صنعاء
- **Necessary source context:** العشرات من عناصر ميليشيات الحوثي مصرعهم وجرح آخرون بغارات جوية لمقاتلات تحالف دعم الشرعية في اليمن استهدفت معسكراً تدريبياً للميليشيات في الضاحية الشمالية الغربية للعاصمة #صنعاء., وأكدت مصادر محلية أن مقاتلات الت…
- **Model finding:** يستخدم النص مصطلح "ميليشيات الحوثي" بصوت الناشر، وهو ما يتعارض مع القاعدة R03 التي تمنع إطلاق أوصاف الميليشيا بشكل آلي على كيانات الصراع الحساسة. هذا الاستخدام قد يُعتبر تأطيراً متحيزاً.
- **Original span → proposed edit:** `ميليشيات الحوثي` → `جماعة الحوثي`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** Militia/loaded label rule is AJ house-style policy; external published copy on silence set should not be treated as FP-worthy by default. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 19. `gemini_run3:ANAD-216325:FND-E-0002`

- **Source index / category:** `111` / `entity_name`
- **Headline:** اليمن.. هادي يوجه بإرسال تعزيزات عسكرية إلى تعز
- **Necessary source context:** مصادر مقربة من الرئاسة اليمنية بأن الرئيس، عبد ربه منصور هادي، وجّه بإرسال تعزيزات عسكرية إلى محافظة تعز، لدعم الجيش الوطني والمقاومة، اللذين يخوضان مواجهات عنيفة ضد ميليشيات الحوثي والمخلوع صالح., وأوضحت المصادر أن هادي أصدر توجيهات لقيادة الجيش بتعزيز الوحدات المقاتلة في تعز، وذلك بإرسال إمدادات وعتاد عسكري ثقيل ودعم الجبهات بالمدرعات والجنود، لحسم المعركة…
- **Model finding:** وصف مقاتل بصوت الناشر يحتاج مراجعة.
- **Original span → proposed edit:** `مقاتليها` → `عناصرها`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** مقاتل→عناصر is AJ house-style; not applicable as hard FP on SANAD/ANAD silence set. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 20. `gemini_run3:ANAD-225223:FND-E-0009`

- **Source index / category:** `112` / `entity_name`
- **Headline:** واشنطن بوست: مقتل 70 سجينا بمخيم الهول على أيدي متطرفين
- **Necessary source context:** …ولون عن مخيم الهول بأن أكثر من 70 شخصًا قتلوا داخل المخيم في شمال شرقي سوريا منذ كانون الثاني يناير، حيث يضم المخيم 62 ألفًا من أفراد عائلة مقاتلي تنظيم داعش وآخرين اعتُقلوا خلال انهيار دولة الخلافة المزعومة قبل أكثر من عامين.وأصبح الهول مكانًا أكثر خطورة ويأسًا من أي وقت مضى. وبحسب صحيفة واشنطن بوست فإن التشدد الديني آخذ في…
- **Model finding:** وصف مقاتل بصوت الناشر يحتاج مراجعة.
- **Original span → proposed edit:** `مقاتلي` → `عناصر`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** مقاتل→عناصر is AJ house-style; not applicable as hard FP on SANAD/ANAD silence set. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 21. `gemini_run3:ANAD-213771:FND-AI-0001`

- **Source index / category:** `44` / `publisher_voice`
- **Headline:** مصر.. 3 قتلى في تفجير بالشيخ زويد بسيناء
- **Necessary source context:** 3 مصرعهم وأصيب آخرون بتفجير مدرعة بالشيخ زويد بشمال سيناء., وذكرت مصادر قبلية أن إرهابيين فجروا عن بعد عبوة ناسفة في مدرعة بمنطقة جرادة غرب مدينة الشيخ زويد، ما أسفر عن تدمير المدرعة ومقتل 3 بداخلها وإصابة آخرين., وأضافوا أنه تم فرض طوق أمني حول موقع الحادث، وتمشيط المنطقة بحثا عن الإرهابيين، فيما تم نقل الضحايا والمصابين إلى المستشفى بالعريش.
- **Model finding:** العنوان يقدم عدد القتلى كحقيقة مؤكدة بصوت الناشر، بينما يعزو النص في المتن هذا العدد إلى 'مصادر قبلية'، مما قد يخل بمبدأ الحفاظ على نسبة القول إلى المصدر ويضفي على المعلومة طابعاً قطعياً غير موجود في المتن.
- **Original span → proposed edit:** `3 قتلى` → `—`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** Headline states figure that body attributes; normal news compression. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 22. `gemini_run3:ANAD-334801:FND-AI-0001`

- **Source index / category:** `45` / `headline_body_mismatch`
- **Headline:** الاسترليني يهبط وسط توقعات بعدم فوز المحافظين بأغلبية في برلمان بريطانيا
- **Necessary source context:** هبط الجنيه الاسترليني اليوم الأربعاء بعد توقعات لمؤسسة يوجوف لاستطلاعات الرأي تظهر أن حزب المحافظين الحاكم في بريطانيا بعيد عن الحصول على أغلبية في الانتخابات العامة التي ستجرى في الثامن من يونيو حزيران. وانخفض اليورو قليلا في الوقت الذي ينتظر فيه المتعاملون بيانات التضخم لاستقراء المزيد من الأدلة بشأن التعافي الاقتصادي في أوروبا بينما عوض الدولار بعض خسائره…
- **Model finding:** يتناول العنوان هبوط الجنيه الإسترليني وتوقعات الانتخابات البريطانية، بينما تتحدث الفقرات المتوفرة من المقال (SEG-003 و SEG-007) عن اليورو والدولار والين والتضخم في أوروبا، مما يشير إلى عدم تطابق بين العنوان ومحتوى المقال المقدم.
- **Original span → proposed edit:** `الاسترليني يهبط وسط توقعات بعدم فوز المحافظين بأغلبية في برلمان بريطانيا` → `—`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** Ordinary headline compression/angle without material contradiction. / `medium`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 23. `gemini_run3:ANAD-247893:FND-M-0001`

- **Source index / category:** `145` / `spelling`
- **Headline:** مقتل العشرات من الحوثيين في معسكر تدريبي في صنعاء
- **Necessary source context:** …غارات معسكراً تدريبياً في منطقة "الشعاب" بمديرية ضلاع همدان، شمال غربي العاصمة., وأشارت المصادر إلى أن الغارات أسفرت عن مصرع عدد من عناصر المليشيات الحوثية وإصابة آخرين.
- **Model finding:** استبدال إملائي معروف.
- **Original span → proposed edit:** `مليشيات` → `ميليشيات`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** مليشيات/ميليشيات both attested; optional orthography. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 24. `gemini_run3:SANAD-074502:FND-M-0003`

- **Source index / category:** `149` / `spelling`
- **Headline:** وضع ليبي حدا لحياته منتحرا بمدينة الجديدة احتجاجا على ما يقع ببلاده على يد معمر القذافي ومليشياته المسلحة، والتي أدت إلى مقتل بعض أفراد عائلته
- **Necessary source context:** وضع ليبي حدا لحياته منتحرا بمدينة الجديدة احتجاجا على ما يقع ببلاده على يد معمر القذافي ومليشياته المسلحة، والتي أدت إلى مقتل بعض أفراد عائلته. وقد رمى نفسه من الطابق الرابع لعمارة حيث سقط على سيارة أجرة كانت متوقفة أمام العمارة المذكورة . يشتغل الليبي المنتحر كمسؤول في أحد ا…
- **Model finding:** استبدال إملائي معروف.
- **Original span → proposed edit:** `مليشيات` → `ميليشيات`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** مليشيات/ميليشيات both attested; optional orthography. / `high`
- **Duplicate-pattern source indices:** `149, 150`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 25. `gemini_run3:SANAD-036358:FND-AI-0002`

- **Source index / category:** `162` / `repetition`
- **Headline:** أخبارنا المغربية : حنان سلامة كشفت وسائل إعلام فرنسية أن البرلمان الأوروبي سيتدارس مشروع قانون جديد يقضي بوقف استيراد الفوسفاط من المغرب بعد ظهور تقارير تفيد بك…
- **Necessary source context:** أخبارنا المغربية : حنان سلامة كشفت وسائل إعلام فرنسية أن البرلمان الأوروبي سيتدارس مشروع قانون جديد يقضي بوقف استيراد الفوسفاط من المغرب بعد ظهور تقارير تفيد بكون مكوناته غير مطابقة للمعايير المعمول به أوروبيا. وأضافت ذات المصادر أن التحليلات المنجزة على بعض العينات أظهرت تواجد مادة حديدية بصادرات الفوسفاط الشيء الذي يضعف جودته ويجعله غير مطابق للمعايير. هذا وقد يشكل التصويت على تطبيق ال…
- **Model finding:** تكرار غير ضروري للجملة الافتتاحية للمقال، والتي تظهر بشكل مختصر في عنوان المقال (SEG-001). هذا يشير إلى مشكلة في هيكلة المقال تتطلب مراجعة.
- **Original span → proposed edit:** `كشفت وسائل إعلام فرنسية أن البرلمان الأوروبي سيتدارس مشروع قانون جديد يقضي بوقف استيراد الفوسفاط من المغرب بعد ظهور تقارير تفيد بكون مكوناته غير مطابقة للمعايير المعمول به أوروبيا.` → `—`
- **Current AI decision:** `drop`
- **AI rationale / confidence:** Lead/headline echo is common news structure, not a hard error. / `high`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 26. `gemini_run3:ANAD-425200:FND-AI-1`

- **Source index / category:** `130` / `numeric_contradiction`
- **Headline:** السياحة تطلق جولات افتراضية داخل المتحف المصرى مدعومة بشرح المرشدين السياحيين
- **Necessary source context:** …ى أطلقتها الوزارة الأسبوع الماضي لإتاحة زيارات افتراضية وجولات إرشادية لبعض المتاحف والمواقع الأثرية المصرية يوميا. وتتضمن هذه الجولات شرح لعشرين قطعة اثرية مميزة داخل المتحف المصري بالتحرير من خلال المرشدين السياحيين الم
- **Model finding:** يذكر النص "عشرين قطعة أثرية"، بينما تشير البيانات المستخلصة (article_context.numbers) إلى الرقم "19". يجب التحقق من العدد الصحيح للقطع الأثرية.
- **Original span → proposed edit:** `عشرين قطعة اثرية مميزة` → `—`
- **Current AI decision:** `uncertain`
- **AI rationale / confidence:** Model cites context numbers needing verification; not proven from excerpt. / `low`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 27. `gemini_run3:ANAD-443219:FND-AI-0001`

- **Source index / category:** `131` / `numeric_contradiction`
- **Headline:** 3.5 ملايين كجم أغذية مصادرة العام الماضي
- **Necessary source context:** صادرت وزارة الشؤون البلدية والقروية أكثر من 3 ملايين و525 ألفا و904 كيلو جرامات و178255 علبة منتجات غذائية غير صالحة خلال العام الماضي 1440 في جميع مناطق المملكة، إضافة إلى 627206 لترات مشروبات وعصائر وألبان.وأظهرت إحصائية الوزارة، أن الزيوت والدهون حصلت على النسبة الأعلى من المصادرات بـ 1441266 كجم بنسبة 40.8%، ثم الخضروات والفواكه بـ 925287 كجم بنسبة 26.2%…
- **Model finding:** تُقدم هذه النسب المئوية متتالية بطريقة توحي بأنها جزء من إحصائية واحدة أو مجموع كلي واحد، لكن مجموعها يتجاوز 100% بكثير (حوالي 167.2%). يبدو أن النسب الأولى تتعلق بالمصادرات بالكيلو جرام، بينما النسب الأخيرة تتعلق بالمعلبات، مما يسبب التباسًا ويجعل البيانات غير واضحة أو مضللة للقارئ.
- **Original span → proposed edit:** `الزيوت والدهون حصلت على النسبة الأعلى من المصادرات بـ 1441266 كجم بنسبة 40.8%، ثم الخضروات والفواكه بـ 925287 كجم بنسبة 26.2%، ثم الدقيق ومشتقاتة بـ 361520 كجم بنسبة 10.2%، فيما ج…` → `—`
- **Current AI decision:** `uncertain`
- **AI rationale / confidence:** Numeric issue not fully verifiable from supplied excerpt. / `low`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 28. `gemini_run3:SANAD-121407:FND-AI-0001`

- **Source index / category:** `134` / `numeric_contradiction`
- **Headline:** عندما يشارك المنتخب الكاميروني لكرة القدم في نهائيات كأس العالم 2010 بجنوب إفريقيا سيكون هو الفريق الذي يحمل على عاتقه أكبر عبء من بين جميع المنتخبات الإفريقية …
- **Necessary source context:** عندما يشارك المنتخب الكاميروني لكرة القدم في نهائيات كأس العالم 2010 بجنوب إفريقيا سيكون هو الفريق الذي يحمل على عاتقه أكبر عبء من بين جميع المنتخبات الإفريقية المشاركة في النهائيات وذلك لتاريخه الطويل في بطولات كأس العالم والذي يفوق جميع المشاركين الآخرين من القارة السمراء .يشارك المنتخب الكاميروني في النهائيات للمرة السادسة منذ عام 1982 ليكون أكثر الفرق ال…
- **Model finding:** القائمة المذكورة لسنوات مشاركة المنتخب الكاميروني السابقة في كأس العالم تتضمن عام 1988، وهو ليس عامًا أقيمت فيه بطولة كأس العالم. يجب أن يكون العام 1998 بدلاً من 1988 لتتوافق مع مشاركات الفريق الفعلية.
- **Original span → proposed edit:** `مشاركاته السابقة في كؤوس العالم: خمس مرات أعوام 1982 و1990 و1994 و1988 و2002 .` → `مشاركاته السابقة في كؤوس العالم: خمس مرات أعوام 1982 و1990 و1994 و1998 و2002 .`
- **Current AI decision:** `uncertain`
- **AI rationale / confidence:** Numeric issue not fully verifiable from supplied excerpt. / `low`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 29. `gemini_run3:SANAD-081131:FND-E-0008`

- **Source index / category:** `113` / `entity_confusion`
- **Headline:** أعلن مدير عمليات وكالة غوث وتشغيل اللاجئين الفلسطينيين أونروا في قطاع غزة جون جينج عن تقديم 6 ملايين دولار لطلبة مدارس أونروا في القطاع لمساعدتهم في تلبية احتيا…
- **Necessary source context:** أعلن مدير عمليات وكالة غوث وتشغيل اللاجئين الفلسطينيين أونروا في قطاع غزة جون جينج عن تقديم 6 ملايين دولار لطلبة مدارس أونروا في القطاع لمساعدتهم في تلبية احتياجاتهم الدراسية في بداية العام الدراسي الحالي. وفي تصريحات صحافية، أمس، طالب جينج مصر وإسرائيل بفتح معبري رفح وبيت حانون (إيرز) أمام الفلسطينيين العاديين، موضحا أن تلك المعابر مفتوحة لفئات معينة وليس ل…
- **Model finding:** أسماء متشابهة قد تكون خلطًا إحاليًا: «المصري تطالب» و«المصري على».
- **Original span → proposed edit:** `المصري على` → `—`
- **Current AI decision:** `uncertain`
- **AI rationale / confidence:** Possible referent confusion; excerpt insufficient to confirm mix-up. / `low`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**

## 30. `gemini_run3:ANAD-336524:FND-AI-ANAD-336524-001`

- **Source index / category:** `46` / `headline_body_mismatch`
- **Headline:** حاكم دبي: إعمار والدار ستدشنان مشروعات بقيمة 8.2 مليار دولار
- **Necessary source context:** وقال الشيخ محمد الذي يشغل أيضا منصب رئيس الوزراء ونائب رئيس دولة الإمارات إنه والشيخ محمد بن زايد ولي عهد أبوظبي شهدا توقيع الاتفاقية.
- **Model finding:** العنوان ينسب تصريحًا محددًا (بشأن إعمار والدار وقيمة المشروعات) إلى حاكم دبي، لكن نص المقال المتاح (SEG-002) لا يحتوي على هذا التصريح أو تفاصيله، بل يذكر فقط أن الشيخ محمد شهد توقيع اتفاقية. هذا يشكل تضاربًا بين العنوان ومحتوى النص المتاح، حيث أن الادعاء الرئيسي في العنوان غير مدعوم بالتفاصيل في النص.
- **Original span → proposed edit:** `حاكم دبي: إعمار والدار ستدشنان مشروعات بقيمة 8.2 مليار دولار` → `—`
- **Current AI decision:** `uncertain`
- **AI rationale / confidence:** Headline claim may be unsupported, but excerpt is too short to adjudicate. / `low`
- **Duplicate-pattern source indices:** `none detected`
- **Reviewer decision:** `[ ] agree  [ ] change_to_keep  [ ] change_to_drop  [ ] change_to_uncertain`
- **Reviewer notes:**
