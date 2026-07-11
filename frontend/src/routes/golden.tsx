import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { GOLDEN } from "@/data/seed";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/golden")({
  component: GoldenPage,
  head: () => ({ meta: [{ title: "المرجعيات الذهبية" }] }),
});

function GoldenPage() {
  return (
    <AppShell>
      <h1 className="text-2xl font-bold mb-4">المرجعيات الذهبية ({GOLDEN.length})</h1>
      <p className="text-xs text-muted-foreground mb-3">
        قرارات محرّرين معتمدة سابقاً، تُستخدم كأمثلة للنموذج اللغوي وكمعيار تقييم.
      </p>
      <div className="space-y-3">
        {GOLDEN.map((g) => (
          <div key={g.gold_id} className="border rounded-md p-3 bg-card">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <h3 className="font-mono text-sm">{g.gold_id} <span className="text-muted-foreground">· {g.article_id} · {g.section_id}</span></h3>
              <Badge variant="secondary">{g.expected_decision}</Badge>
            </div>
            <p className="font-arabic mt-2" dir="rtl">«{g.span_text}»</p>
            <p className="text-xs text-muted-foreground mt-1">{g.expected_reason}</p>
            <div className="text-xs mt-1">
              <b>rules:</b> <span className="font-mono">{g.expected_rules.join(", ")}</span>
              {g.expected_minimum_safe_suggestion && (
                <span className="mr-3"><b>safe:</b> <span className="font-arabic" dir="rtl">{g.expected_minimum_safe_suggestion}</span></span>
              )}
            </div>
          </div>
        ))}
      </div>
    </AppShell>
  );
}