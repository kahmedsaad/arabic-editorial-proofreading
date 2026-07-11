import { createFileRoute, useParams } from "@tanstack/react-router";
import { GOLDEN } from "@/data/seed";
import { useStore } from "@/lib/store";

export const Route = createFileRoute("/review/$articleId/evaluation")({
  component: EvaluationPage,
});

function EvaluationPage() {
  const { articleId } = useParams({ from: "/review/$articleId/evaluation" });
  const suggestions = useStore((s) => s.suggestions[articleId] ?? []);
  const rows = GOLDEN.filter((g) => g.article_id === articleId).map((g) => {
    const matched = suggestions.find((s) =>
      s.anchor.section_id === g.section_id &&
      (s.anchor.original_text === g.span_text || g.span_text.includes(s.anchor.original_text)),
    );
    return {
      gold: g,
      machine_decision: matched?.severity ?? "—",
      machine_rules: matched?.rule_ids ?? [],
      agreement: matched ? matched.severity === g.expected_decision ? "agree" : "mismatch" : "miss",
    };
  });
  const counts = rows.reduce(
    (a, r) => ({ ...a, [r.agreement]: (a[r.agreement] ?? 0) + 1 }),
    {} as Record<string, number>,
  );

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">التقييم مقابل المرجعيات الذهبية</h2>
      <div className="flex gap-3 text-sm">
        <span>متطابق: <b>{counts.agree ?? 0}</b></span>
        <span>اختلاف: <b>{counts.mismatch ?? 0}</b></span>
        <span>مفقود: <b>{counts.miss ?? 0}</b></span>
      </div>
      <table className="w-full text-xs border">
        <thead className="bg-muted/50">
          <tr><th className="text-right p-2">المرجع</th><th className="text-right p-2">المتوقَّع</th><th className="text-right p-2">المُكتَشف</th><th className="text-right p-2">الاتفاق</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.gold.gold_id} className="border-t">
              <td className="p-2 font-mono">{r.gold.gold_id} <span className="text-muted-foreground">({r.gold.section_id})</span><div className="font-arabic" dir="rtl">«{r.gold.span_text}»</div></td>
              <td className="p-2">{r.gold.expected_decision}<div className="text-muted-foreground">{r.gold.expected_rules.join(", ")}</div></td>
              <td className="p-2">{r.machine_decision}<div className="text-muted-foreground">{r.machine_rules.join(", ")}</div></td>
              <td className="p-2 font-semibold" style={{ color: r.agreement === "agree" ? "rgb(16,150,80)" : r.agreement === "mismatch" ? "rgb(200,120,0)" : "rgb(200,40,40)" }}>{r.agreement}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}