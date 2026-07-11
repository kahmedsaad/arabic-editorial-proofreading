import type { Article, Suggestion } from "@/lib/types";

const TYPE_TO_CLASS: Record<string, string> = {
  spelling: "hl hl-proofreading",
  grammar: "hl hl-proofreading",
  punctuation: "hl hl-proofreading",
  mechanical_style: "hl hl-mechanical",
  entity_name: "hl hl-entity",
  temporal_descriptor: "hl hl-entity",
  lexical: "hl hl-lexical",
  relational: "hl hl-relational",
  headline_alternative: "hl hl-relational",
  caption_alternative: "hl hl-relational",
  wording_rewrite: "hl hl-relational",
};

function classFor(s: Suggestion): string {
  const base = TYPE_TO_CLASS[s.type] ?? "hl hl-relational";
  if (s.severity === "ban" || s.severity === "hard_warning") return base + " hl-high-risk";
  return base;
}

interface Props {
  article: Article;
  suggestions: Suggestion[];
  activeId?: string;
  onSelect: (id: string) => void;
}

export function ArticleView({ article, suggestions, activeId, onSelect }: Props) {
  return (
    <article className="space-y-4 arabic-body" dir="rtl">
      {article.sections.map((sec) => {
        const inSection = suggestions
          .filter((s) => s.anchor.section_id === sec.section_id && s.anchor.start_char >= 0)
          .sort((a, b) => a.anchor.start_char - b.anchor.start_char);
        return (
          <SectionBlock
            key={sec.section_id}
            label={sec.label ?? sec.section_id}
            surface={sec.surface}
            text={sec.text}
            spans={inSection}
            activeId={activeId}
            onSelect={onSelect}
          />
        );
      })}
    </article>
  );
}

function SectionBlock({
  label, surface, text, spans, activeId, onSelect,
}: {
  label: string; surface: string; text: string; spans: Suggestion[]; activeId?: string;
  onSelect: (id: string) => void;
}) {
  // Build non-overlapping render segments by walking spans in order.
  type Seg = { text: string; s?: Suggestion };
  const segs: Seg[] = [];
  let cursor = 0;
  for (const sp of spans) {
    const { start_char, end_char } = sp.anchor;
    if (start_char < cursor) continue; // skip overlap
    if (start_char > cursor) segs.push({ text: text.slice(cursor, start_char) });
    segs.push({ text: text.slice(start_char, end_char), s: sp });
    cursor = end_char;
  }
  if (cursor < text.length) segs.push({ text: text.slice(cursor) });

  const isHeadline = surface === "headline";
  const isCaption = surface === "caption";

  return (
    <section className="border rounded-md p-4 bg-card">
      <div className="text-xs text-muted-foreground mb-2 flex justify-between">
        <span>{label}</span>
        <span className="font-mono">{surface}</span>
      </div>
      <div className={isHeadline ? "text-xl font-bold leading-9" : isCaption ? "italic text-sm" : ""}>
        {segs.map((seg, i) =>
          seg.s ? (
            <span
              key={i}
              className={`${classFor(seg.s)}${activeId === seg.s.suggestion_id ? " hl-active" : ""}`}
              onClick={() => onSelect(seg.s!.suggestion_id)}
              title={seg.s.reason}
            >
              {seg.text}
            </span>
          ) : (
            <span key={i}>{seg.text}</span>
          ),
        )}
      </div>
    </section>
  );
}