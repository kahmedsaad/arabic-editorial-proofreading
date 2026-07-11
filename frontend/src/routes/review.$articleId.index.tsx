import { createFileRoute, useParams } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { findArticle } from "@/lib/articles";
import { ArticleView } from "@/components/ArticleView";
import { SuggestionCard } from "@/components/SuggestionCard";
import { useStore, resetArticle } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { usePipeline } from "@/lib/pipeline/orchestrator";

export const Route = createFileRoute("/review/$articleId/")({
  component: ReviewIndex,
});

function ReviewIndex() {
  const { articleId } = useParams({ from: "/review/$articleId/" });
  const article = findArticle(articleId)!;
  const suggestions = useStore((s) => s.suggestions[articleId] ?? []);
  const mode = useStore((s) => s.mode);
  const [activeId, setActiveId] = useState<string | undefined>();
  const [filter, setFilter] = useState<"all" | "open" | "decided" | "high">("open");
  const { status, phases, run, reset } = usePipeline(articleId);

  const filtered = useMemo(() => {
    return suggestions.filter((s) => {
      if (filter === "all") return true;
      if (filter === "decided") return s.status === "accepted" || s.status === "rejected" || s.status === "edited_by_human";
      if (filter === "open") return s.status === "pending_human_review" || s.status === "llm_judged";
      if (filter === "high") return s.severity === "hard_warning" || s.severity === "ban";
      return true;
    });
  }, [suggestions, filter]);

  return (
    <div className="grid lg:grid-cols-[1fr_420px] gap-4">
      <div className="space-y-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex gap-2 items-center">
            <Badge variant="outline">النص الأصلي مُقفل</Badge>
            <span className="text-xs text-muted-foreground">لا يُعدَّل أبداً.</span>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => resetArticle(articleId)}>إعادة تعيين</Button>
            <Button size="sm" onClick={run} disabled={status === "running"}>
              {status === "running"
                ? "جارٍ التشغيل…"
                : mode === "live"
                  ? "تشغيل المحرك (MVP Live)"
                  : "تشغيل المراحل (Demo)"}
            </Button>
            {status !== "idle" && <Button size="sm" variant="ghost" onClick={reset}>إيقاف</Button>}
          </div>
        </div>
        {status !== "idle" && (
          <div className="border rounded-md p-2 text-xs bg-muted/40">
            {phases.map((p) => (
              <div key={p.phase} className="flex items-center justify-between font-mono">
                <span>{p.name}</span>
                <span className={
                  p.status === "running" ? "text-amber-600" :
                  p.status === "complete" ? "text-emerald-700" :
                  p.status === "error" ? "text-red-600" : "text-muted-foreground"
                }>{p.status}{p.error ? ` — ${p.error}` : ""}</span>
              </div>
            ))}
          </div>
        )}
        <ArticleView article={article} suggestions={suggestions} activeId={activeId} onSelect={setActiveId} />
      </div>

      <aside className="space-y-3">
        <div className="flex gap-1 flex-wrap text-xs">
          {(["open", "high", "decided", "all"] as const).map((f) => (
            <Button key={f} size="sm" variant={filter === f ? "default" : "outline"} onClick={() => setFilter(f)}>
              {f === "open" ? "مفتوحة" : f === "high" ? "عالية الخطورة" : f === "decided" ? "تم البت" : "الكل"}
            </Button>
          ))}
          <span className="self-center text-muted-foreground">{filtered.length}/{suggestions.length}</span>
        </div>
        <div className="space-y-2 max-h-[80vh] overflow-y-auto pr-1">
          {filtered.map((s) => (
            <SuggestionCard
              key={s.suggestion_id}
              articleId={articleId}
              s={s}
              active={activeId === s.suggestion_id}
              onSelect={() => setActiveId(s.suggestion_id)}
            />
          ))}
          {filtered.length === 0 && (
            <p className="text-sm text-muted-foreground">لا توجد اقتراحات في هذه القائمة.</p>
          )}
        </div>
      </aside>
    </div>
  );
}