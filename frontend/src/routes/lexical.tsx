import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { LEXICAL } from "@/data/seed";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/lexical")({
  component: LexicalPage,
  head: () => ({ meta: [{ title: "المعجم المنظَّم" }] }),
});

function LexicalPage() {
  return (
    <AppShell>
      <h1 className="text-2xl font-bold mb-4">المعجم المنظَّم ({LEXICAL.length})</h1>
      <p className="text-xs text-muted-foreground mb-3">
        الانتخاب المعجمي يختار المرشحين فقط — ليس مخالفات. يقرر الحكم العلائقي لاحقاً.
      </p>
      <div className="grid md:grid-cols-2 gap-3">
        {LEXICAL.map((l) => (
          <div key={l.lex_id} className="border rounded-md p-3 bg-card">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-mono text-sm font-semibold">{l.lex_id} — <span className="font-arabic">{l.canonical}</span></h3>
              <Badge variant="outline">{l.field}</Badge>
            </div>
            <div className="text-xs mt-2 space-y-1">
              <div><b>forms:</b> <span className="font-arabic" dir="rtl">{l.forms.join("، ")}</span></div>
              <div><b>neighbors:</b> <span className="font-arabic" dir="rtl">{l.semantic_neighbors.join("، ")}</span></div>
              <div><b>possible rules:</b> <span className="font-mono">{l.possible_rules.join(", ") || "—"}</span></div>
              {l.example && <div className="text-muted-foreground font-arabic" dir="rtl">مثال: {l.example}</div>}
            </div>
          </div>
        ))}
      </div>
    </AppShell>
  );
}