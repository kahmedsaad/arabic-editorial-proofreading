/**
 * MVP FastAPI client + Finding → Suggestion adapter.
 * Live Mode should call this instead of OpenAI phase loops.
 */

import type { Article, Severity, Suggestion, SuggestionType } from "@/lib/types";

export type MvpFinding = {
  finding_id: string;
  document_id: string;
  segment_id: string;
  source: "mechanical" | "gemini" | "mock";
  category: string;
  decision: string;
  severity: string;
  original_text: string;
  suggested_text: string | null;
  start_offset: number;
  end_offset: number;
  rule_ids: string[];
  explanation_ar: string;
  confidence: number;
  requires_editor_review: boolean;
  validation_status: string;
};

export type MvpReviewResponse = {
  review_id: string;
  document: { document_id: string; headline: string; body: string };
  segments: Array<{ segment_id: string; zone: string; text: string; sequence: number }>;
  findings: MvpFinding[];
  rejected_findings: MvpFinding[];
  mechanical_finding_count: number;
  ai_finding_count: number;
};

const CATEGORY_TO_TYPE: Record<string, SuggestionType> = {
  spelling: "spelling",
  punctuation: "punctuation",
  terminology: "lexical",
  entity_name: "entity_name",
  attribution: "relational",
  attribution_strength: "relational",
  unsupported_certainty: "relational",
  loaded_framing: "relational",
  implicit_blame: "relational",
  quote_voice: "relational",
  publisher_voice: "relational",
  headline_framing: "headline_alternative",
  caption_framing: "caption_alternative",
  unsupported_causality: "relational",
  stance_drift: "relational",
  clarity: "wording_rewrite",
  repetition: "grammar",
};

const DECISION_TO_SEVERITY: Record<string, Severity> = {
  acceptable: "acceptable",
  suggest: "suggest",
  replace: "replace",
  soft_warning: "soft_warning",
  hard_warning: "hard_warning",
  ban: "ban",
  needs_editor_review: "soft_warning",
};

function defaultApiBase(): string {
  return (
    (typeof import.meta !== "undefined" &&
      (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_API_BASE_URL) ||
    "http://127.0.0.1:8001"
  );
}

export function getMvpApiBase(override?: string): string {
  return (override || defaultApiBase()).replace(/\/$/, "");
}

export function articleToReviewRequest(article: Article) {
  const headline =
    article.sections.find((s) => s.surface === "headline")?.text ?? article.title;
  const bodyParts = article.sections
    .filter((s) => s.surface === "lead" || s.surface === "paragraph" || s.surface === "caption")
    .map((s) => s.text);
  const metadata = article.sections.find((s) => s.surface === "metadata")?.text;
  if (metadata) {
    bodyParts.push(metadata);
  }
  return {
    document_id: article.article_id,
    language: "ar" as const,
    source: "editorial_compass_ui",
    headline,
    body: bodyParts.join("\n"),
    metadata: {
      content_type: article.content_type,
      topic: article.topic,
      ui: "editorial-compass",
    },
  };
}

function locateAnchor(article: Article, finding: MvpFinding) {
  for (const section of article.sections) {
    const idx = section.text.indexOf(finding.original_text);
    if (idx >= 0) {
      return {
        section_id: section.section_id,
        start_char: idx,
        end_char: idx + finding.original_text.length,
        original_text: finding.original_text,
      };
    }
  }
  // Fallback: first section + reported offsets (may not highlight correctly)
  const fallback = article.sections[0];
  return {
    section_id: fallback?.section_id ?? finding.segment_id,
    start_char: finding.start_offset,
    end_char: finding.end_offset,
    original_text: finding.original_text,
  };
}

export function findingsToSuggestions(
  article: Article,
  findings: MvpFinding[],
  reviewId: string,
): Suggestion[] {
  return findings.map((f, i) => {
    const severity = DECISION_TO_SEVERITY[f.decision] ?? "soft_warning";
    const type = CATEGORY_TO_TYPE[f.category] ?? "relational";
    const phase =
      f.source === "mechanical"
        ? "mechanical_style"
        : f.source === "gemini"
          ? "llm_response"
          : "llm_response";
    return {
      suggestion_id: f.finding_id || `MVP-${i + 1}`,
      candidate_id: `${reviewId}:${f.finding_id}`,
      phase,
      type,
      severity,
      anchor: locateAnchor(article, f),
      suggested_text: f.suggested_text,
      reason: f.explanation_ar || f.category,
      rule_ids: f.rule_ids ?? [],
      proof_steps: [
        `source=${f.source}`,
        `decision=${f.decision}`,
        `validation=${f.validation_status}`,
        `confidence=${f.confidence}`,
        `review_id=${reviewId}`,
      ],
      validator_status: f.validation_status === "valid" ? "passed" : "failed",
      validator_notes:
        f.validation_status === "valid" ? undefined : [`status=${f.validation_status}`],
      status: "pending_human_review",
      requires_editor_approval: true as const,
      editor_note:
        f.decision === "needs_editor_review" ? "يحتاج مراجعة المحرر (من المحرك)." : undefined,
    };
  });
}

export async function createMvpReview(
  article: Article,
  apiBase?: string,
): Promise<MvpReviewResponse> {
  const base = getMvpApiBase(apiBase);
  const res = await fetch(`${base}/api/v1/reviews`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(articleToReviewRequest(article)),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`MVP review failed (${res.status}): ${text.slice(0, 300)}`);
  }
  return (await res.json()) as MvpReviewResponse;
}

export async function checkMvpHealth(apiBase?: string): Promise<{ ok: boolean; body?: unknown; error?: string }> {
  try {
    const base = getMvpApiBase(apiBase);
    const res = await fetch(`${base}/api/v1/health`);
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
    return { ok: true, body: await res.json() };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
