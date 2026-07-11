import type {
  Article,
  AuditEvent,
  EntityRecord,
  GoldenExample,
  HistoricalEdit,
  LexicalEntry,
  PhaseRecord,
  RelationalRule,
  Suggestion,
} from "@/lib/types";

// ============================================================
// ENTITY REPOSITORY
// ============================================================
export const ENTITIES: EntityRecord[] = [
  { entity_id: "E_HEZBOLLAH", approved_ar: "حزب الله", type: "organization", aliases: ["الحزب", "الجماعة"], policy_profiles: ["sensitive_conflict_party", "non_state_armed_political_actor"], current_descriptors: [], status: "active", version: "demo-1" },
  { entity_id: "E_ISRAELI_MILITARY", approved_ar: "الجيش الإسرائيلي", type: "organization", aliases: ["جيش الاحتلال", "الجيش"], policy_profiles: ["state_military_actor", "sensitive_conflict_party"], status: "active", version: "demo-1" },
  { entity_id: "E_ISRAEL", approved_ar: "إسرائيل", type: "country", aliases: ["تل أبيب"], policy_profiles: ["sensitive_conflict_party"], status: "active", version: "demo-1" },
  { entity_id: "E_NYT", approved_ar: "نيويورك تايمز", type: "agency", aliases: ["NYT"], policy_profiles: ["named_named_western_outlet"], status: "active", version: "demo-1" },
  { entity_id: "E_AJ", approved_ar: "الجزيرة", type: "agency", aliases: ["الجزيرة نت", "قناة الجزيرة"], policy_profiles: ["aj_voice"], status: "active", version: "demo-1" },
  { entity_id: "E_REUTERS", approved_ar: "رويترز", type: "agency", aliases: ["وكالة رويترز"], policy_profiles: ["international_wire"], status: "active", version: "demo-1" },
  { entity_id: "E_NETANYAHU", approved_ar: "بنيامين نتنياهو", type: "public_figure", aliases: ["نتنياهو"], policy_profiles: ["public_figure_temporal_descriptor"], current_title: "رئيس الوزراء الإسرائيلي", first_mention_form: "رئيس الوزراء الإسرائيلي بنيامين نتنياهو", short_mention_form: "نتنياهو", status: "in_office", version: "demo-1", last_verified: "2026-06-05" },
  { entity_id: "E_TRUMP", approved_ar: "دونالد ترامب", type: "public_figure", aliases: ["ترامب"], policy_profiles: ["public_figure_temporal_descriptor"], current_title: "الرئيس الأميركي", first_mention_form: "الرئيس الأميركي دونالد ترامب", short_mention_form: "ترامب", status: "in_office", version: "demo-1", last_verified: "2026-06-05" },
  { entity_id: "E_VENEZUELA", approved_ar: "فنزويلا", type: "country", aliases: [], policy_profiles: [], status: "active", version: "demo-1" },
  { entity_id: "E_USA", approved_ar: "الولايات المتحدة", type: "country", aliases: ["أميركا"], policy_profiles: [], status: "active", version: "demo-1" },
  { entity_id: "E_IRAN", approved_ar: "إيران", type: "country", aliases: ["السلطات الإيرانية"], policy_profiles: [], status: "active", version: "demo-1" },
  { entity_id: "E_RUSSIA", approved_ar: "روسيا", type: "country", aliases: [], policy_profiles: [], status: "active", version: "demo-1" },
  { entity_id: "E_UKRAINE", approved_ar: "أوكرانيا", type: "country", aliases: [], policy_profiles: [], status: "active", version: "demo-1" },
  { entity_id: "E_ICC", approved_ar: "المحكمة الجنائية الدولية", type: "organization", aliases: [], policy_profiles: ["international_legal_body"], status: "active", version: "demo-1" },
  { entity_id: "E_UN", approved_ar: "الأمم المتحدة", type: "organization", aliases: [], policy_profiles: [], status: "active", version: "demo-1" },
  { entity_id: "E_WHO", approved_ar: "منظمة الصحة العالمية", type: "organization", aliases: [], policy_profiles: ["health_authority"], status: "active", version: "demo-1" },
  { entity_id: "E_NASA", approved_ar: "ناسا", type: "agency", aliases: [], policy_profiles: ["science_authority"], status: "active", version: "demo-1" },
  { entity_id: "E_HARVARD", approved_ar: "جامعة هارفارد", type: "university", aliases: [], policy_profiles: [], status: "active", version: "demo-1" },
  { entity_id: "E_CAIRO_UNI", approved_ar: "جامعة القاهرة", type: "university", aliases: [], policy_profiles: [], status: "active", version: "demo-1" },
  { entity_id: "E_REAL_MADRID", approved_ar: "ريال مدريد", type: "club", aliases: [], policy_profiles: ["sports_club"], status: "active", version: "demo-1" },
  { entity_id: "E_BARCELONA", approved_ar: "برشلونة", type: "club", aliases: [], policy_profiles: ["sports_club"], status: "active", version: "demo-1" },
  { entity_id: "E_MAN_CITY", approved_ar: "مانشستر سيتي", type: "club", aliases: [], policy_profiles: ["sports_club"], status: "active", version: "demo-1" },
  { entity_id: "E_FIFA", approved_ar: "الاتحاد الدولي لكرة القدم", type: "organization", aliases: ["فيفا"], policy_profiles: ["sports_governing_body"], status: "active", version: "demo-1" },
  { entity_id: "E_CANNES", approved_ar: "مهرجان كان السينمائي", type: "event", aliases: [], policy_profiles: [], status: "active", version: "demo-1" },
  { entity_id: "E_NETFLIX", approved_ar: "نتفليكس", type: "organization", aliases: [], policy_profiles: [], status: "active", version: "demo-1" },
  { entity_id: "E_OPENAI", approved_ar: "أوبن إيه آي", type: "organization", aliases: ["OpenAI"], policy_profiles: ["tech_company"], status: "active", version: "demo-1" },
  { entity_id: "E_APPLE", approved_ar: "آبل", type: "organization", aliases: [], policy_profiles: ["tech_company"], status: "active", version: "demo-1" },
  { entity_id: "E_GAZA", approved_ar: "غزة", type: "city", aliases: [], policy_profiles: ["sensitive_conflict_zone"], status: "active", version: "demo-1" },
  { entity_id: "E_TEL_AVIV", approved_ar: "تل أبيب", type: "city", aliases: [], policy_profiles: ["metonym_caution"], status: "active", version: "demo-1" },
  { entity_id: "E_LEBANON", approved_ar: "لبنان", type: "country", aliases: [], policy_profiles: [], status: "active", version: "demo-1" },
];

// ============================================================
// LEXICAL REPOSITORY
// ============================================================
export const LEXICAL: LexicalEntry[] = [
  { lex_id: "LEX_MILITIA", canonical: "ميليشيا", field: "contested_label", forms: ["ميليشيا", "الميليشيا", "ميليشيات", "الميليشيات"], semantic_neighbors: ["مسلحون", "جماعة مسلحة", "فصيل مسلح"], effect: "elect_candidate_span", possible_rules: ["R03", "R08"], example: "وصفت التقارير الجماعة بأنها ميليشيا مسلحة." },
  { lex_id: "LEX_FIGHTER", canonical: "مقاتل", field: "armed_combatant_descriptor", forms: ["مقاتل", "مقاتلون", "مقاتلين", "مقاتليه", "مقاتليها", "مقاتلي"], semantic_neighbors: ["محارب", "مسلح", "عنصر مسلح"], effect: "elect_candidate_span", possible_rules: ["R_DESC_NONSTATE"], example: "مقتل أحد مقاتلي الجماعة." },
  { lex_id: "LEX_TERROR", canonical: "إرهابية", field: "terrorism_label", forms: ["إرهابية", "إرهابي", "إرهاب", "منظمة إرهابية"], semantic_neighbors: ["متطرفة", "متشددة"], effect: "elect_candidate_span", possible_rules: ["R_TERROR_LABEL"], example: "وصفها بأنها منظمة إرهابية." },
  { lex_id: "LEX_RESISTANCE", canonical: "المقاومة", field: "resistance_frame", forms: ["المقاومة", "مقاومة"], semantic_neighbors: ["الجهاد", "النضال المسلح"], effect: "elect_candidate_span", possible_rules: ["R_LOADED_FRAME"], example: "أعلنت المقاومة عن عملية جديدة." },
  { lex_id: "LEX_CONFIRM", canonical: "تأكيد", field: "confirmation_strength", forms: ["تأكيد", "تأكيده", "أكد", "أكدت", "مؤكد"], semantic_neighbors: ["إثبات", "جزم"], effect: "elect_candidate_span", possible_rules: ["R_ATTR_CONFIRMATION"], example: "نقلت الوكالة تأكيده للخبر." },
  { lex_id: "LEX_VAGUE_SOURCE", canonical: "وسائل إعلام", field: "vague_source", forms: ["وسائل إعلام", "مصادر إعلامية", "تقارير", "مصادر مطلعة"], semantic_neighbors: ["جهات لم تسمَّ", "مصدر غير محدد"], effect: "elect_candidate_span", possible_rules: ["R_SOURCE_VAGUE"], example: "قالت وسائل إعلام لبنانية إن الحادثة وقعت." },
  { lex_id: "LEX_UNCERTAIN_HL", canonical: "ربما", field: "headline_uncertainty_marker", forms: ["ربما", "قد", "محتمل", "يحتمل"], semantic_neighbors: ["لربما", "من المرجح"], effect: "elect_candidate_span", possible_rules: ["R_HEADLINE_UNCERTAINTY"], example: "الجيش ربما يرد على الهجوم." },
  { lex_id: "LEX_ELEMENTS", canonical: "عناصر", field: "member_descriptor", forms: ["عناصر", "عنصر", "عناصره", "عناصرها"], semantic_neighbors: ["أفراد", "أعضاء"], effect: "elect_candidate_span", possible_rules: [], example: "عناصر تابعة للجماعة." },
  { lex_id: "LEX_FOREIGN_BACKED", canonical: "مدعومة من الخارج", field: "foreign_backed_claim", forms: ["مدعومة من الخارج", "بدعم خارجي", "تدعمها أطراف خارجية"], semantic_neighbors: ["بأجندات أجنبية", "بتمويل خارجي"], effect: "elect_candidate_span", possible_rules: ["R04"], example: "وصفت بأنها مدعومة من الخارج." },
  { lex_id: "LEX_INTIMIDATION", canonical: "ترهيب", field: "intimidation_framing", forms: ["ترهيب", "لترهيب", "إرهاب", "تخويف"], semantic_neighbors: ["تهديد", "ضغط"], effect: "elect_candidate_span", possible_rules: ["R07"], example: "اتُّهمت بترهيب السكان." },
];

// ============================================================
// RELATIONAL RULES + MECHANICAL RULES
// ============================================================
export const RULES: RelationalRule[] = [
  { rule_id: "R03", name: "Militia label for sensitive entities", type: "relational", natural_language: "Do not apply militia-style labels blindly to sensitive conflict-party entities in Al Jazeera voice.", trigger_fields: ["contested_label"], requires: ["entity", "voice", "surface"], applies_when: { voice: ["al_jazeera_voice"], surfaces: ["headline", "caption", "body"] }, exceptions: ["direct_attributed_quote"], default_decision: "hard_warning", requires_editor_approval: true, area: "conflict" },
  { rule_id: "R04", name: "Attribution required for foreign-backed claim", type: "relational", natural_language: "Foreign-backed framing must carry a clear, named attribution.", trigger_fields: ["foreign_backed_claim"], requires: ["voice", "source"], applies_when: { voice: ["al_jazeera_voice"], surfaces: ["headline", "caption", "body"] }, exceptions: ["direct_attributed_quote"], default_decision: "hard_warning", requires_editor_approval: true, area: "source" },
  { rule_id: "R07", name: "Caption-level framing claims", type: "relational", natural_language: "Captions must not add unattributed framing beyond what the image shows.", trigger_fields: ["intimidation_framing", "foreign_backed_claim", "contested_label"], requires: ["surface"], applies_when: { surfaces: ["caption"] }, exceptions: [], default_decision: "hard_warning", requires_editor_approval: true, area: "caption" },
  { rule_id: "R08", name: "Loaded conflict framing softening", type: "relational", natural_language: "Loaded conflict adjectives should be softened to neutral descriptions where possible.", trigger_fields: ["loaded_conflict_framing", "resistance_frame"], requires: ["voice"], applies_when: { voice: ["al_jazeera_voice"] }, exceptions: ["direct_attributed_quote"], default_decision: "soft_warning", requires_editor_approval: true, area: "conflict" },
  { rule_id: "R_DESC_NONSTATE", name: "Armed-combatant descriptor for non-state actor", type: "relational", natural_language: "Use neutral member descriptors (عناصر) instead of armed-combatant labels for Hezbollah in Al Jazeera voice.", trigger_fields: ["armed_combatant_descriptor"], requires: ["entity", "voice"], applies_when: { voice: ["al_jazeera_voice"], entities: ["E_HEZBOLLAH"] }, exceptions: ["direct_attributed_quote"], default_decision: "hard_warning", requires_editor_approval: true, area: "entity" },
  { rule_id: "R_TERROR_LABEL", name: "Terrorism label", type: "relational", natural_language: "Never apply terrorism labels to a sensitive conflict party in Al Jazeera voice. Inside attributed quotes, preserve wording.", trigger_fields: ["terrorism_label"], requires: ["voice"], applies_when: { voice: ["al_jazeera_voice"] }, exceptions: ["direct_attributed_quote"], default_decision: "ban", requires_editor_approval: true, area: "conflict" },
  { rule_id: "R_LOADED_FRAME", name: "Resistance frame in editorial voice", type: "relational", natural_language: "Resistance framing is acceptable inside attributed quotes; flag if used in editorial narration.", trigger_fields: ["resistance_frame"], requires: ["voice"], applies_when: { voice: ["al_jazeera_voice"] }, exceptions: ["direct_attributed_quote"], default_decision: "soft_warning", requires_editor_approval: true, area: "conflict" },
  { rule_id: "R_ATTR_CONFIRMATION", name: "Confirmation-strength verb with single source", type: "relational", natural_language: "Do not use confirmation-strength verbs when a claim is supported by only one source.", trigger_fields: ["confirmation_strength"], requires: ["source"], applies_when: { surfaces: ["body", "lead"] }, exceptions: [], default_decision: "soft_warning", requires_editor_approval: true, area: "source" },
  { rule_id: "R_SOURCE_VAGUE", name: "Vague media source", type: "relational", natural_language: "Replace vague media-group attributions with named direct sources, or soften the claim.", trigger_fields: ["vague_source"], requires: ["source"], applies_when: { surfaces: ["lead", "body"] }, exceptions: [], default_decision: "hard_warning", requires_editor_approval: true, area: "source" },
  { rule_id: "R_HEADLINE_UNCERTAINTY", name: "Headline uncertainty marker", type: "relational", natural_language: "Headlines should avoid uncertainty markers (ربما، قد) unless absolutely necessary.", trigger_fields: ["headline_uncertainty_marker"], requires: ["surface"], applies_when: { surfaces: ["headline"] }, exceptions: [], default_decision: "soft_warning", requires_editor_approval: true, area: "headline" },
  { rule_id: "M_SOURCE_FORMAT", name: "Caption source format", type: "mechanical", natural_language: "Sources in metadata/captions must use the approved format: NAME1 / NAME2", trigger_fields: [], requires: [], applies_when: { surfaces: ["caption", "metadata"] }, exceptions: [], default_decision: "replace", requires_editor_approval: true, area: "mechanical" },
  { rule_id: "M_ENTITY_APPROVED", name: "Approved entity name form", type: "mechanical", natural_language: "Use the approved Arabic form for known entities (e.g. نيويورك تايمز not نيورك تايمز).", trigger_fields: [], requires: [], applies_when: { surfaces: ["headline", "lead", "body", "caption"] }, exceptions: [], default_decision: "replace", requires_editor_approval: true, area: "mechanical" },
  { rule_id: "M_FIRST_MENTION_TITLE", name: "Public figure first mention with title", type: "mechanical", natural_language: "First mention of a public figure must include the approved current title.", trigger_fields: [], requires: ["entity"], applies_when: { surfaces: ["headline", "lead", "body"] }, exceptions: [], default_decision: "suggest", requires_editor_approval: true, area: "mechanical" },
  { rule_id: "R31", name: "Sports club casual naming", type: "relational", natural_language: "Use full approved club name on first mention in sports articles.", trigger_fields: [], requires: ["entity"], applies_when: { entities: ["E_REAL_MADRID", "E_BARCELONA", "E_MAN_CITY"] }, exceptions: [], default_decision: "suggest", requires_editor_approval: true, area: "sports" },
  { rule_id: "R39", name: "Scientific certainty claim", type: "relational", natural_language: "Avoid presenting preliminary scientific findings as confirmed.", trigger_fields: ["science_certainty"], requires: [], applies_when: { surfaces: ["headline", "lead", "body"] }, exceptions: ["direct_attributed_quote"], default_decision: "hard_warning", requires_editor_approval: true, area: "science" },
];

// ============================================================
// GOLDEN DATASET
// ============================================================
export const GOLDEN: GoldenExample[] = [
  { gold_id: "G_HEADLINE_001", article_id: "aj-hezbollah-drones-v3", span_text: "مقاتليه", section_id: "headline", expected_decision: "hard_warning", expected_rules: ["R_DESC_NONSTATE"], expected_reason: "Armed-combatant descriptor for Hezbollah in headline (Al Jazeera voice).", expected_minimum_safe_suggestion: "عناصره" },
  { gold_id: "G_LEAD_001", article_id: "aj-hezbollah-drones-v3", span_text: "وسائل إعلام لبنانية", section_id: "lead", expected_decision: "hard_warning", expected_rules: ["R_SOURCE_VAGUE"], expected_reason: "Vague source for a factual news claim.", expected_minimum_safe_suggestion: "مصدر مسمى أو تليين الإسناد" },
  { gold_id: "G_BODY_001", article_id: "aj-hezbollah-drones-v3", span_text: "تأكيده", section_id: "p3", expected_decision: "soft_warning", expected_rules: ["R_ATTR_CONFIRMATION"], expected_reason: "Confirmation-strength verb with single source.", expected_minimum_safe_suggestion: "قوله" },
  { gold_id: "G_QUOTE_001", article_id: "aj-hezbollah-drones-v3", span_text: "المقاومة لن تسكت على هذا العدوان", section_id: "p2", expected_decision: "acceptable_with_note", expected_rules: ["R_LOADED_FRAME"], expected_reason: "Inside attributed direct quote — preserve wording." },
  { gold_id: "G_QUOTE_002", article_id: "aj-hezbollah-drones-v3", span_text: "منظمة إرهابية", section_id: "p5", expected_decision: "acceptable_with_note", expected_rules: ["R_TERROR_LABEL"], expected_reason: "Loaded label inside attributed quote — preserve, do not auto-replace." },
  { gold_id: "G_CAPTION_001", article_id: "aj-hezbollah-drones-v3", span_text: "الميليشيا المدعومة من الخارج لترهيب الحدود", section_id: "caption_1", expected_decision: "hard_warning", expected_rules: ["R03", "R04", "R07"], expected_reason: "Caption uses contested label + unattributed foreign-backed claim + intimidation framing.", expected_minimum_safe_suggestion: "صور لمسيّرات حزب الله من تقرير بثته الجزيرة" },
];

// ============================================================
// HISTORICAL EDITS
// ============================================================
export const HISTORICAL_EDITS: HistoricalEdit[] = [
  { edit_id: "HIST_017", before: "استمر الحزب في اعتداءاته", after: "واصل الحزب استهداف القوات", detected_pattern: "loaded conflict framing softened to neutral description", candidate_rules: ["R08"] },
  { edit_id: "HIST_018", before: "ميليشيات مدعومة من إيران", after: "فصائل مسلحة موالية لإيران", detected_pattern: "contested label replaced with neutral compound", candidate_rules: ["R03"] },
  { edit_id: "HIST_019", before: "أكد المصدر", after: "قال المصدر", detected_pattern: "confirmation strength softened with single-source claim", candidate_rules: ["R_ATTR_CONFIRMATION"] },
];

// ============================================================
// ARTICLE FIXTURE (Hezbollah drones v3 from the spec simulation)
// ============================================================
const HEZBOLLAH_ARTICLE: Article = {
  article_id: "aj-hezbollah-drones-v3",
  title: "حزب الله ربما يرد بعد مقتل أحد مقاتليه في غارة إسرائيلية",
  topic: "Hezbollah drones and Israeli military vulnerabilities",
  language: "ar",
  content_type: "breaking_news",
  main_entities: ["E_HEZBOLLAH", "E_ISRAELI_MILITARY", "E_ISRAEL", "E_REUTERS"],
  sections: [
    { section_id: "headline", surface: "headline", label: "العنوان", text: "حزب الله ربما يرد بعد مقتل أحد مقاتليه في غارة إسرائيلية" },
    { section_id: "metadata", surface: "metadata", label: "بيانات النشر", text: "المصدر: نيورك تايمز والجزيره نت" },
    { section_id: "caption_1", surface: "caption", label: "تعليق صورة", text: "صورة للميليشيا المدعومة من الخارج لترهيب الحدود الإسرائيلية." },
    { section_id: "lead", surface: "lead", label: "المقدمة", text: "قالت وسائل إعلام لبنانية إن الجيش الإسرائيلي شن غارة على بلدة حدودية جنوبي لبنان، ما أدى إلى مقتل أحد مقاتلي حزب الله." },
    { section_id: "p2", surface: "paragraph", label: "فقرة 2", text: "وقالت الجماعة في بيانها إن \"المقاومة لن تسكت على هذا العدوان\"، مضيفة أن مقاتليها استهدفوا موقعا عسكريا إسرائيليا." },
    { section_id: "p3", surface: "paragraph", label: "فقرة 3", text: "ونقلت وكالة رويترز عن مصدر أمني لبناني تأكيده أن الغارة أسفرت عن مقتل شخصين وإصابة آخرين." },
    { section_id: "p4", surface: "paragraph", label: "فقرة 4", text: "وقال الجيش الإسرائيلي إنه استهدف عناصر تابعة لحزب الله كانت تستعد لإطلاق صواريخ." },
    { section_id: "p5", surface: "paragraph", label: "فقرة 5", text: "وفي سياق متصل، وصف وزير إسرائيلي حزب الله بأنه \"منظمة إرهابية\"، وقال إن تل أبيب ستواصل عملياتها." },
  ],
};

const CLEAN_ARTICLE: Article = {
  article_id: "aj-hezbollah-drones-v1",
  title: "حزب الله يتحدث عن رد بعد مقتل أحد عناصره في غارة إسرائيلية",
  topic: "Hezbollah and Israeli military activity",
  language: "ar",
  content_type: "breaking_news",
  main_entities: ["E_HEZBOLLAH", "E_ISRAELI_MILITARY"],
  sections: [
    { section_id: "headline", surface: "headline", label: "العنوان", text: "حزب الله يتحدث عن رد بعد مقتل أحد عناصره في غارة إسرائيلية" },
    { section_id: "lead", surface: "lead", label: "المقدمة", text: "أفادت قناة المنار اللبنانية بأن الجيش الإسرائيلي شن غارة على بلدة حدودية جنوبي لبنان، ما أدى إلى مقتل أحد عناصر حزب الله." },
    { section_id: "p2", surface: "paragraph", label: "فقرة 2", text: "وقالت الجماعة في بيانها إن \"المقاومة لن تسكت على هذا العدوان\"، مضيفة أن عناصرها استهدفوا موقعا عسكريا إسرائيليا." },
    { section_id: "p3", surface: "paragraph", label: "فقرة 3", text: "ونقلت وكالة رويترز عن مصدر أمني لبناني قوله إن الغارة أسفرت عن مقتل شخصين وإصابة آخرين." },
  ],
};

export const ARTICLES: Article[] = [HEZBOLLAH_ARTICLE, CLEAN_ARTICLE];

// ============================================================
// MOCK PHASE OUTPUTS for the v3 article (Demo Mode)
// ============================================================

function hashOf(text: string): string {
  // tiny deterministic non-crypto hash for prototype span integrity
  let h = 0;
  for (let i = 0; i < text.length; i++) h = (h * 31 + text.charCodeAt(i)) | 0;
  return "h" + (h >>> 0).toString(16);
}

function anchor(article: Article, section_id: string, fragment: string) {
  const sec = article.sections.find((s) => s.section_id === section_id);
  if (!sec) throw new Error(`unknown section ${section_id}`);
  const start = sec.text.indexOf(fragment);
  return {
    section_id,
    start_char: start,
    end_char: start + fragment.length,
    original_text: fragment,
    original_hash: hashOf(fragment),
  };
}

const A = HEZBOLLAH_ARTICLE;

export const SEED_SUGGESTIONS: Suggestion[] = [
  // ---- Phase: arabic_proofreading
  {
    suggestion_id: "P001",
    phase: "arabic_proofreading",
    type: "spelling",
    severity: "suggest",
    anchor: anchor(A, "metadata", "نيورك"),
    suggested_text: "نيويورك",
    reason: "Spelling: missing letter — approved form is نيويورك.",
    rule_ids: [],
    proof_steps: ["lexicon: نيورك → نيويورك (typo)"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
  {
    suggestion_id: "P002",
    phase: "arabic_proofreading",
    type: "spelling",
    severity: "suggest",
    anchor: anchor(A, "metadata", "الجزيره"),
    suggested_text: "الجزيرة",
    reason: "Spelling: ta marbuta. Approved form is الجزيرة.",
    rule_ids: [],
    proof_steps: ["lexicon: الجزيره → الجزيرة"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
  // ---- Phase: mechanical_style
  {
    suggestion_id: "M001",
    phase: "mechanical_style",
    type: "mechanical_style",
    severity: "replace",
    anchor: anchor(A, "metadata", "نيورك تايمز والجزيره نت"),
    suggested_text: "نيويورك تايمز / الجزيرة نت",
    reason: "Caption/metadata source format must use ' / ' separator with approved entity forms.",
    rule_ids: ["M_SOURCE_FORMAT", "M_ENTITY_APPROVED"],
    proof_steps: ["rule M_SOURCE_FORMAT", "rule M_ENTITY_APPROVED for نيويورك تايمز and الجزيرة"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
  // ---- Phase: temporal_descriptor (none triggered here, but placeholder for sample)
  // ---- Phase: relational (headline + lexical-driven)
  {
    suggestion_id: "SUG-001",
    candidate_id: "C001",
    phase: "llm_response",
    type: "relational",
    severity: "hard_warning",
    anchor: anchor(A, "headline", "مقاتليه"),
    suggested_text: "عناصره",
    reason: "Armed-combatant descriptor applied to Hezbollah in headline (Al Jazeera voice, not a quote).",
    rule_ids: ["R_DESC_NONSTATE"],
    golden_ids: ["G_HEADLINE_001"],
    proof_steps: [
      "surface=headline",
      "voice=al_jazeera_voice",
      "entity=E_HEZBOLLAH",
      "lemma=مقاتل (armed_combatant_descriptor)",
      "rule=R_DESC_NONSTATE",
    ],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
  {
    suggestion_id: "SUG-002",
    candidate_id: "C002",
    phase: "llm_response",
    type: "relational",
    severity: "soft_warning",
    anchor: anchor(A, "headline", "ربما"),
    suggested_text: "يتحدث عن رد",
    reason: "Uncertainty marker in headline — prefer concrete framing supported by body.",
    rule_ids: ["R_HEADLINE_UNCERTAINTY"],
    proof_steps: ["surface=headline", "field=headline_uncertainty_marker", "rule=R_HEADLINE_UNCERTAINTY"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
    editor_note: "Suggestion replaces 'ربما يرد' with 'يتحدث عن رد' — assumes body supports it.",
  },
  {
    suggestion_id: "SUG-003",
    candidate_id: "C003",
    phase: "llm_response",
    type: "relational",
    severity: "hard_warning",
    anchor: anchor(A, "lead", "وسائل إعلام لبنانية"),
    suggested_text: "قناة لبنانية مسماة",
    reason: "Vague media-group attribution; style requires a named direct source or softer attribution.",
    rule_ids: ["R_SOURCE_VAGUE"],
    golden_ids: ["G_LEAD_001"],
    proof_steps: ["surface=lead", "field=vague_source", "rule=R_SOURCE_VAGUE"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
  {
    suggestion_id: "SUG-004",
    candidate_id: "C004",
    phase: "llm_response",
    type: "relational",
    severity: "hard_warning",
    anchor: anchor(A, "lead", "مقاتلي حزب الله"),
    suggested_text: "عناصر حزب الله",
    reason: "Armed-combatant descriptor in editorial narration about Hezbollah.",
    rule_ids: ["R_DESC_NONSTATE"],
    proof_steps: ["surface=lead", "voice=al_jazeera_voice", "entity=E_HEZBOLLAH", "rule=R_DESC_NONSTATE"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
  {
    suggestion_id: "SUG-005",
    candidate_id: "C005",
    phase: "llm_response",
    type: "relational",
    severity: "hard_warning",
    anchor: anchor(A, "p2", "مقاتليها"),
    suggested_text: "عناصرها",
    reason: "Descriptor in indirect reported speech (مضيفة أن…) — not protected as a direct quote.",
    rule_ids: ["R_DESC_NONSTATE"],
    proof_steps: ["surface=paragraph", "voice=reported_speech (مضيفة أن)", "entity=E_HEZBOLLAH", "rule=R_DESC_NONSTATE"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
  {
    suggestion_id: "SUG-006",
    candidate_id: "C006",
    phase: "llm_response",
    type: "relational",
    severity: "soft_warning",
    anchor: anchor(A, "p3", "تأكيده"),
    suggested_text: "قوله",
    reason: "Confirmation-strength verb may overstate certainty with a single source.",
    rule_ids: ["R_ATTR_CONFIRMATION"],
    golden_ids: ["G_BODY_001"],
    proof_steps: ["field=confirmation_strength", "source=single (مصدر أمني لبناني)", "rule=R_ATTR_CONFIRMATION"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
  {
    suggestion_id: "SUG-007",
    candidate_id: "C007",
    phase: "llm_response",
    type: "relational",
    severity: "acceptable_with_note",
    anchor: anchor(A, "p2", "المقاومة لن تسكت على هذا العدوان"),
    suggested_text: null,
    reason: "Inside attributed direct quote — preserve wording. No replacement.",
    rule_ids: ["R_LOADED_FRAME"],
    golden_ids: ["G_QUOTE_001"],
    proof_steps: ["voice=direct_attributed_quote", "exception fires for R_LOADED_FRAME"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
  {
    suggestion_id: "SUG-008",
    candidate_id: "C008",
    phase: "llm_response",
    type: "relational",
    severity: "acceptable_with_note",
    anchor: anchor(A, "p5", "منظمة إرهابية"),
    suggested_text: null,
    reason: "Loaded label inside attributed Israeli-minister quote. Preserve wording; do not auto-replace.",
    rule_ids: ["R_TERROR_LABEL"],
    golden_ids: ["G_QUOTE_002"],
    proof_steps: ["voice=direct_attributed_quote", "exception fires for R_TERROR_LABEL"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
  {
    suggestion_id: "SUG-009",
    candidate_id: "C009",
    phase: "llm_response",
    type: "relational",
    severity: "hard_warning",
    anchor: anchor(A, "caption_1", "للميليشيا المدعومة من الخارج لترهيب الحدود الإسرائيلية"),
    suggested_text: "لمسيّرات حزب الله — من تقرير بثته الجزيرة",
    reason: "Caption stacks a contested label + unattributed foreign-backed claim + intimidation framing.",
    rule_ids: ["R03", "R04", "R07"],
    golden_ids: ["G_CAPTION_001"],
    proof_steps: ["surface=caption", "fields=contested_label, foreign_backed_claim, intimidation_framing", "rules=R03, R04, R07"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
  {
    suggestion_id: "SUG-010",
    candidate_id: "C010",
    phase: "llm_response",
    type: "entity_name",
    severity: "suggest",
    anchor: anchor(A, "p5", "تل أبيب"),
    suggested_text: "الحكومة الإسرائيلية",
    reason: "Metonym caution: 'تل أبيب' is sometimes used as a metonym for the Israeli government. Prefer the explicit institution.",
    rule_ids: ["M_ENTITY_APPROVED"],
    proof_steps: ["entity=E_TEL_AVIV", "policy_profile=metonym_caution"],
    validator_status: "passed",
    status: "pending_human_review",
    requires_editor_approval: true,
  },
];

// ============================================================
// PHASE RECORDS (Demo Mode)
// ============================================================
export const SEED_PHASES: PhaseRecord[] = [
  { phase: "ingest", name: "0. Ingest article", purpose: "Receive the article and create an immutable original.", approach: "Parse JSON, assign IDs, character offsets, lock original.", reference_source: "Spec §8 Step 0", input_summary: "Article JSON from CMS", output: { article_id: A.article_id, sections: A.sections.length, original_locked: true }, source: "mock", next_phase: "arabic_proofreading" },
  { phase: "arabic_proofreading", name: "1. Arabic proofreading", purpose: "Detect spelling, hamza, ta marbuta, grammar, punctuation, dialectal leakage.", approach: "Arabic proofreading engine (deterministic in Demo Mode; LLM in Live Mode).", reference_source: "Spec §8 Step 1", input_summary: "Original article text", output: { suggestions: ["P001", "P002"] }, confidence: 0.96, source: "mock", next_phase: "mechanical_style" },
  { phase: "mechanical_style", name: "2. Mechanical style", purpose: "Check house-style conventions (source format, approved entity forms, dates).", approach: "Mechanical style register lookup.", reference_source: "Spec §8 Step 2", input_summary: "Article surfaces", output: { suggestions: ["M001"] }, confidence: 0.99, source: "mock", next_phase: "structure_source_quote" },
  { phase: "structure_source_quote", name: "3. Structure / source / quote map", purpose: "Identify surfaces, voice zones, sources, attributions, direct and indirect quotes.", approach: "Discourse parser.", reference_source: "Spec §8 Step 3", input_summary: "Article sections", output: { source_map: [{ section_id: "lead", span: "وسائل إعلام لبنانية", confidence: 0.92 }, { section_id: "p3", span: "رويترز / مصدر أمني لبناني", confidence: 0.98 }, { section_id: "p4", span: "الجيش الإسرائيلي", confidence: 0.99 }, { section_id: "p5", span: "وزير إسرائيلي", confidence: 0.93 }], quote_map: [{ section_id: "p2", span: "المقاومة لن تسكت على هذا العدوان", type: "direct_quote" }, { section_id: "p5", span: "منظمة إرهابية", type: "direct_quote" }, { section_id: "p2", span: "مقاتليها استهدفوا موقعا عسكريا إسرائيليا", type: "indirect_quote" }], voice_map: [{ section_id: "headline", voice: "al_jazeera_voice" }, { section_id: "caption_1", voice: "al_jazeera_voice" }, { section_id: "lead", voice: "attributed_to_source" }, { section_id: "p2", voice: "attributed_to_hezbollah_statement" }, { section_id: "p3", voice: "agency_attribution" }, { section_id: "p4", voice: "attributed_to_israeli_military" }, { section_id: "p5", voice: "attributed_to_israeli_minister" }] }, confidence: 0.91, source: "mock", next_phase: "entity_extraction" },
  { phase: "entity_extraction", name: "4. Entity extraction", purpose: "Detect named and implied entities, resolve to repository.", approach: "Exact + alias + fuzzy match against entity repo.", reference_source: "Spec §8 Step 4", input_summary: "Article text + entity repo", output: { entities: [{ entity_id: "E_HEZBOLLAH", mentions: 5, confidence: 0.99 }, { entity_id: "E_ISRAELI_MILITARY", mentions: 3, confidence: 0.99 }, { entity_id: "E_REUTERS", mentions: 1, confidence: 0.99 }, { entity_id: "E_NYT", mentions: 1, confidence: 0.97 }, { entity_id: "E_AJ", mentions: 1, confidence: 0.97 }, { entity_id: "E_TEL_AVIV", mentions: 1, confidence: 0.95 }] }, confidence: 0.97, source: "mock", next_phase: "temporal_descriptor" },
  { phase: "temporal_descriptor", name: "5. Public figure temporal descriptor", purpose: "Verify first-mention titles and current descriptors for public figures.", approach: "Match mentions against public-figure repo.", reference_source: "Spec §8 Step 5", input_summary: "Entity mentions", output: { suggestions: [], note: "No public-figure mentions in this article." }, confidence: 1, source: "mock", next_phase: "lexical_election" },
  { phase: "lexical_election", name: "6. Lexical candidate election", purpose: "Elect spans for deeper review via lexical match + morphology + semantic search.", approach: "Lexical repo lookup + morphological expansion + semantic neighbor scoring.", reference_source: "Spec §8 Step 6", input_summary: "Article text + lexical repo", output: { candidates: ["C001", "C002", "C003", "C004", "C005", "C006", "C007", "C008", "C009", "C010"] }, confidence: 0.9, source: "mock", next_phase: "article_graph" },
  { phase: "article_graph", name: "7. Article episode graph", purpose: "Build a temporary graph of sections, entities, candidate spans, and semantic fields.", approach: "In-memory graph construction.", reference_source: "Spec §8 Step 7", input_summary: "Phase 3-6 outputs", output: { nodes: 22, edges: 31 }, confidence: 1, source: "mock", next_phase: "persistent_graph_link" },
  { phase: "persistent_graph_link", name: "8. Persistent graph linking", purpose: "Link article nodes to permanent entity / lexical / rule nodes.", approach: "Exact + semantic linking with confidence scoring.", reference_source: "Spec §8 Step 8", input_summary: "Article graph + repos", output: { links: 18 }, confidence: 0.94, source: "mock", next_phase: "rule_retrieval" },
  { phase: "rule_retrieval", name: "9. Rule retrieval", purpose: "Pull only rules relevant to this article from the full repository.", approach: "Entity / field / surface filtering + specificity reranking.", reference_source: "Spec §8 Step 9", input_summary: "Persistent graph links", output: { active_rules: ["R03", "R04", "R07", "R08", "R_DESC_NONSTATE", "R_TERROR_LABEL", "R_LOADED_FRAME", "R_ATTR_CONFIRMATION", "R_SOURCE_VAGUE", "R_HEADLINE_UNCERTAINTY", "M_SOURCE_FORMAT", "M_ENTITY_APPROVED"], ignored_rules: ["R31", "R39", "M_FIRST_MENTION_TITLE"] }, confidence: 0.93, source: "mock", next_phase: "golden_retrieval" },
  { phase: "golden_retrieval", name: "10. Golden example retrieval", purpose: "Retrieve similar editor-approved precedents.", approach: "Similarity scoring on span text + rule overlap.", reference_source: "Spec §8 Step 10", input_summary: "Candidate spans + active rules", output: { examples: ["G_HEADLINE_001", "G_LEAD_001", "G_BODY_001", "G_QUOTE_001", "G_QUOTE_002", "G_CAPTION_001"] }, confidence: 0.9, source: "mock", next_phase: "llm_packet" },
  { phase: "llm_packet", name: "11. LLM packet creation", purpose: "Assemble a curated context packet for the LLM.", approach: "Combine article + candidates + active rules + golden examples + strict schema.", reference_source: "Spec §8 Step 11", input_summary: "All upstream outputs", output: { packet_size_kb: 7, candidates: 10, active_rules: 12, golden_examples: 6 }, confidence: 1, source: "mock", next_phase: "llm_response" },
  { phase: "llm_response", name: "12. LLM structured response", purpose: "Receive structured judgments per candidate.", approach: "OpenAI-compatible JSON response, schema-validated.", reference_source: "Spec §8 Step 12", input_summary: "LLM packet", output: { judgments: 10 }, confidence: 0.88, source: "mock", next_phase: "validator" },
  { phase: "validator", name: "13. Validator", purpose: "Schema, ID, decision-enum, anchor, and no-auto-apply checks.", approach: "Zod validation + invariant checks.", reference_source: "Spec §8 Step 13", input_summary: "LLM JSON", output: { status: "passed", checks: [{ name: "schema_valid", status: "passed" }, { name: "candidate_ids_valid", status: "passed" }, { name: "requires_editor_approval_true", status: "passed" }, { name: "no_auto_apply", status: "passed" }, { name: "quote_text_unchanged", status: "passed" }] }, confidence: 1, source: "mock", next_phase: "suggestion_review" },
  { phase: "suggestion_review", name: "14. Suggestion review", purpose: "Present each suggestion as an editor action card.", approach: "UI card per validated judgment.", reference_source: "Spec §8 Step 14", input_summary: "Validated suggestions", output: { suggestions: 10 }, confidence: 1, source: "mock", next_phase: "human_approval" },
  { phase: "human_approval", name: "15. Human approval", purpose: "Editor accepts / rejects / edits / comments.", approach: "Manual review; every status change recorded in the audit log.", reference_source: "Spec §8 Step 15", input_summary: "Editor decisions", output: { invariant: "Original article never mutated. Accepted suggestions only mutate the revised preview." }, confidence: 1, source: "mock" },
];

export const SEED_AUDIT: AuditEvent[] = [];

// ============================================================
// REGISTRY HELPERS
// ============================================================
export function getArticle(id: string): Article | undefined {
  return ARTICLES.find((a) => a.article_id === id);
}
export function getEntity(id: string): EntityRecord | undefined {
  return ENTITIES.find((e) => e.entity_id === id);
}
export function getRule(id: string): RelationalRule | undefined {
  return RULES.find((r) => r.rule_id === id);
}
export function getLexical(id: string): LexicalEntry | undefined {
  return LEXICAL.find((l) => l.lex_id === id);
}
export function getGolden(id: string): GoldenExample | undefined {
  return GOLDEN.find((g) => g.gold_id === id);
}

// Mermaid graph for the v3 article (used by Graph Explorer)
export const SEED_MERMAID = `graph TD
  D["Article: Hezbollah drones v3"]
  H["Headline"]
  L["Lead"]
  C1["Caption 1"]
  P2["Paragraph 2 (quote)"]
  P3["Paragraph 3 (Reuters)"]
  P5["Paragraph 5 (Israeli minister)"]
  E1["Entity: حزب الله"]
  E2["Entity: الجيش الإسرائيلي"]
  E3["Entity: رويترز"]
  S_H["Span: مقاتليه"]
  S_L1["Span: وسائل إعلام لبنانية"]
  S_L2["Span: مقاتلي حزب الله"]
  S_C1["Span: الميليشيا المدعومة..."]
  S_P5["Span: منظمة إرهابية (quote)"]
  F1["Field: armed_combatant_descriptor"]
  F2["Field: vague_source"]
  F3["Field: contested_label"]
  F4["Field: terrorism_label"]
  R1["Rule R_DESC_NONSTATE"]
  R2["Rule R_SOURCE_VAGUE"]
  R3["Rule R03 + R04 + R07"]
  R4["Rule R_TERROR_LABEL"]
  G1["Golden G_HEADLINE_001"]
  G2["Golden G_CAPTION_001"]
  G3["Golden G_QUOTE_002"]

  D --> H
  D --> L
  D --> C1
  D --> P2
  D --> P3
  D --> P5
  H --> S_H
  L --> S_L1
  L --> S_L2
  C1 --> S_C1
  P5 --> S_P5
  S_H --> F1
  S_L1 --> F2
  S_L2 --> F1
  S_C1 --> F3
  S_P5 --> F4
  S_H --> E1
  S_L2 --> E1
  S_C1 --> E1
  S_P5 --> E1
  P4 --> E2
  P3 --> E3
  F1 --> R1
  F2 --> R2
  F3 --> R3
  F4 --> R4
  R1 --> G1
  R3 --> G2
  R4 --> G3
`;

// Semantic-search inspector mock (matches spec example)
export const SEED_SEMANTIC = {
  query_span: "لافتعال الأزمات العسكرية",
  nearest_fields: [
    { field: "motive_attribution", score: 0.87 },
    { field: "loaded_conflict_framing", score: 0.82 },
    { field: "neutral_military_activity", score: 0.41 },
  ],
  decision: "elect_as_candidate",
  note: "This is not a violation yet. It is sent for relational judgment.",
};

// LLM packet (mocked)
export const SEED_LLM_PACKET = {
  task: "Judge only listed candidate spans. Do not rewrite the full article. Return structured JSON. Every suggestion requires human approval.",
  article_context: {
    content_type: "breaking_news",
    topic: A.topic,
    main_entities: ["حزب الله", "الجيش الإسرائيلي", "إسرائيل", "رويترز"],
  },
  candidate_spans: SEED_SUGGESTIONS.filter((s) => s.candidate_id).map((s) => ({
    candidate_id: s.candidate_id,
    section_id: s.anchor.section_id,
    start_char: s.anchor.start_char,
    end_char: s.anchor.end_char,
    original_text: s.anchor.original_text,
    active_rules: s.rule_ids,
  })),
  output_schema: {
    judgments: [
      {
        candidate_id: "string",
        decision: "acceptable|acceptable_with_note|suggest|replace|soft_warning|hard_warning|ban",
        reason: "string",
        minimum_safe_suggestion: "string|null",
        requires_editor_approval: true,
        proof_steps: ["string"],
      },
    ],
  },
};

export const SEED_LLM_RESPONSE = {
  judgments: SEED_SUGGESTIONS.filter((s) => s.candidate_id).map((s) => ({
    candidate_id: s.candidate_id,
    decision: s.severity,
    reason: s.reason,
    minimum_safe_suggestion: s.suggested_text,
    requires_editor_approval: true,
    proof_steps: s.proof_steps,
  })),
};

export const SEED_VALIDATOR = {
  status: "passed",
  checks: [
    { name: "schema_valid", status: "passed" },
    { name: "candidate_ids_valid", status: "passed" },
    { name: "requires_editor_approval_true", status: "passed" },
    { name: "no_auto_apply", status: "passed" },
    { name: "quote_text_unchanged", status: "passed" },
    { name: "no_new_facts_introduced", status: "passed" },
  ],
};