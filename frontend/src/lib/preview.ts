import type { Article, Suggestion } from "./types";

export interface RevisedSection {
  section_id: string;
  label?: string;
  surface: string;
  original: string;
  revised: string;
  applied: Array<{ suggestion_id: string; from: string; to: string }>;
}

export function buildRevisedPreview(article: Article, suggestions: Suggestion[]): RevisedSection[] {
  const accepted = suggestions.filter(
    (s) => (s.status === "accepted" || s.status === "edited_by_human") && (s.edited_text ?? s.suggested_text),
  );
  return article.sections.map((sec) => {
    let revised = sec.text;
    const applied: RevisedSection["applied"] = [];
    const inSection = accepted
      .filter((s) => s.anchor.section_id === sec.section_id)
      // longest-first so overlapping shorter replacements don't break offsets
      .sort((a, b) => b.anchor.original_text.length - a.anchor.original_text.length);
    for (const s of inSection) {
      const replacement = s.edited_text ?? s.suggested_text ?? "";
      if (revised.includes(s.anchor.original_text)) {
        revised = revised.replace(s.anchor.original_text, replacement);
        applied.push({ suggestion_id: s.suggestion_id, from: s.anchor.original_text, to: replacement });
      }
    }
    return {
      section_id: sec.section_id,
      label: sec.label,
      surface: sec.surface,
      original: sec.text,
      revised,
      applied,
    };
  });
}