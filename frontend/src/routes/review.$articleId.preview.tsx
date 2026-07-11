import { createFileRoute, useParams } from "@tanstack/react-router";
import { findArticle } from "@/lib/articles";
import { useStore, log } from "@/lib/store";
import { buildRevisedPreview } from "@/lib/preview";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/review/$articleId/preview")({
  component: PreviewPage,
});

function PreviewPage() {
  const { articleId } = useParams({ from: "/review/$articleId/preview" });
  const article = findArticle(articleId)!;
  const suggestions = useStore((s) => s.suggestions[articleId] ?? []);
  const revised = buildRevisedPreview(article, suggestions);

  function exportJson() {
    const blob = new Blob([JSON.stringify({ article, revised, suggestions }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${article.article_id}-revised.json`;
    a.click();
    URL.revokeObjectURL(url);
    log("editor_demo", "exported_revised_preview", { article_id: articleId });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">المعاينة المنقَّحة</h2>
          <p className="text-xs text-muted-foreground">إسقاط للاقتراحات المقبولة فقط. النص الأصلي لم يتغيّر.</p>
        </div>
        <Button size="sm" onClick={exportJson}>تصدير JSON</Button>
      </div>
      <div className="space-y-3">
        {revised.map((sec) => (
          <div key={sec.section_id} className="grid md:grid-cols-2 gap-3">
            <div className="border rounded-md p-3 bg-muted/30">
              <div className="text-xs text-muted-foreground mb-1">الأصل · {sec.label}</div>
              <p className="arabic-body" dir="rtl">{sec.original}</p>
            </div>
            <div className="border rounded-md p-3 bg-emerald-50 dark:bg-emerald-950/20">
              <div className="text-xs text-muted-foreground mb-1">المعاينة المنقَّحة</div>
              <p className="arabic-body" dir="rtl">{sec.revised}</p>
              {sec.applied.length > 0 && (
                <ul className="text-[11px] mt-2 text-muted-foreground font-mono space-y-0.5">
                  {sec.applied.map((a) => (
                    <li key={a.suggestion_id}>{a.suggestion_id}: «{a.from}» → «{a.to}»</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}