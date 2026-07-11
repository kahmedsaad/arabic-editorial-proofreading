// Domain types for the Al Jazeera editorial proofreading prototype.
// Mirrors fixture shapes in the spec (sections 6, 8, 10).

export type Severity =
  | "acceptable"
  | "acceptable_with_note"
  | "soft_warning"
  | "hard_warning"
  | "suggest"
  | "replace"
  | "ban";

export type SuggestionType =
  | "spelling"
  | "grammar"
  | "punctuation"
  | "mechanical_style"
  | "entity_name"
  | "temporal_descriptor"
  | "lexical"
  | "relational"
  | "headline_alternative"
  | "caption_alternative"
  | "wording_rewrite";

export type SuggestionStatus =
  | "detected"
  | "awaiting_llm_judgment"
  | "llm_judged"
  | "validation_failed"
  | "pending_human_review"
  | "accepted"
  | "rejected"
  | "edited_by_human"
  | "applied_to_preview"
  | "exported";

export interface Anchor {
  section_id: string;
  start_char: number;
  end_char: number;
  original_text: string;
  original_hash?: string;
}

export interface Suggestion {
  suggestion_id: string;
  candidate_id?: string;
  phase: string;
  type: SuggestionType;
  severity: Severity;
  anchor: Anchor;
  suggested_text: string | null;
  reason: string;
  rule_ids: string[];
  golden_ids?: string[];
  proof_steps: string[];
  validator_status: "passed" | "failed" | "pending";
  validator_notes?: string[];
  status: SuggestionStatus;
  requires_editor_approval: true;
  editor_note?: string;
  edited_text?: string;
}

export interface ArticleSection {
  section_id: string;
  surface: "headline" | "metadata" | "caption" | "lead" | "paragraph" | "section_heading";
  label?: string;
  text: string;
}

export interface Article {
  article_id: string;
  title: string;
  topic: string;
  language: "ar";
  content_type: string;
  main_entities: string[];
  sections: ArticleSection[];
  // Pre-computed phase outputs (Demo Mode). Live Mode regenerates these.
  mock_outputs?: Record<string, unknown>;
}

export interface EntityRecord {
  entity_id: string;
  approved_ar: string;
  type: "organization" | "public_figure" | "country" | "city" | "agency" | "club" | "university" | "event";
  aliases: string[];
  policy_profiles: string[];
  current_descriptors?: string[];
  current_title?: string;
  first_mention_form?: string;
  short_mention_form?: string;
  status: string;
  version: string;
  last_verified?: string;
}

export interface LexicalEntry {
  lex_id: string;
  canonical: string;
  field: string;
  forms: string[];
  semantic_neighbors: string[];
  effect: "elect_candidate_span";
  possible_rules: string[];
  example?: string;
}

export interface RelationalRule {
  rule_id: string;
  name: string;
  type: "relational" | "mechanical";
  natural_language: string;
  trigger_fields: string[];
  requires: string[];
  applies_when: { voice?: string[]; surfaces?: string[]; entities?: string[] };
  exceptions: string[];
  default_decision: Severity;
  requires_editor_approval: true;
  area?: string;
}

export interface GoldenExample {
  gold_id: string;
  article_id: string;
  span_text: string;
  section_id: string;
  expected_decision: Severity;
  expected_rules: string[];
  expected_reason: string;
  expected_minimum_safe_suggestion?: string;
}

export interface HistoricalEdit {
  edit_id: string;
  before: string;
  after: string;
  detected_pattern: string;
  candidate_rules: string[];
}

export interface AuditEvent {
  event_id: string;
  timestamp: string;
  actor: string;
  action: string;
  article_id: string;
  suggestion_id?: string;
  candidate_id?: string;
  original_text?: string;
  suggested_text?: string | null;
  rules?: string[];
  note?: string;
}

export type PhaseId =
  | "ingest"
  | "arabic_proofreading"
  | "mechanical_style"
  | "structure_source_quote"
  | "entity_extraction"
  | "temporal_descriptor"
  | "lexical_election"
  | "article_graph"
  | "persistent_graph_link"
  | "rule_retrieval"
  | "golden_retrieval"
  | "llm_packet"
  | "llm_response"
  | "validator"
  | "suggestion_review"
  | "human_approval";

export interface PhaseRecord {
  phase: PhaseId;
  name: string;
  purpose: string;
  approach: string;
  reference_source: string;
  input_summary: string;
  output: unknown;
  confidence?: number;
  next_phase?: PhaseId;
  source: "mock" | "llm-simulated" | "repository-driven";
}

export type AppMode = "demo" | "live";

export interface LiveSettings {
  /** MVP FastAPI base URL, e.g. http://127.0.0.1:8001 */
  baseUrl: string;
  /** Optional legacy OpenAI-compatible key (unused when useMvpEngine is true). */
  apiKey: string;
  model: string;
  /** Live Mode calls MVP /api/v1/reviews when true. */
  useMvpEngine: boolean;
}