import { createFileRoute, useParams } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { SEED_MERMAID } from "@/data/seed";
import { findArticle } from "@/lib/articles";
import { MermaidView } from "@/components/MermaidView";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useStore, getApiKey, getState, log } from "@/lib/store";
import { callLlmPhase } from "@/lib/llm.functions";
import { SYSTEM_PROMPTS, buildUserPrompt } from "@/lib/pipeline/prompts";
import { ENTITIES, RULES, GOLDEN } from "@/data/seed";

export const Route = createFileRoute("/review/$articleId/graph")({
  component: GraphPage,
});

function buildArticleMermaid(articleId: string): string {
  const a = findArticle(articleId);
  if (!a) return SEED_MERMAID;
  const lines: string[] = ["graph TD"];
  lines.push(`  D["مقال: ${a.title.slice(0, 28)}…"]`);
  a.sections.forEach((s, i) => {
    const id = `S${i}`;
    const label = `${s.label ?? s.section_id}`.replace(/"/g, "'");
    lines.push(`  ${id}["${label} (${s.surface})"]`);
    lines.push(`  D --> ${id}`);
  });
  a.main_entities.forEach((eid, i) => {
    const e = ENTITIES.find((x) => x.entity_id === eid);
    if (!e) return;
    const id = `E${i}`;
    lines.push(`  ${id}["كيان: ${e.approved_ar}"]`);
    lines.push(`  D --> ${id}`);
  });
  return lines.join("\n");
}

function GraphPage() {
  const { articleId } = useParams({ from: "/review/$articleId/graph" });
  const mode = useStore((s) => s.mode);
  const auto = useMemo(() => buildArticleMermaid(articleId), [articleId]);
  const [llmMermaid, setLlmMermaid] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function runLlmGraph() {
    setBusy(true); setErr(null);
    try {
      const article = findArticle(articleId);
      if (!article) throw new Error("Article not found");
      const apiKey = getApiKey();
      if (!apiKey) throw new Error("لا يوجد مفتاح API. افتح الإعدادات أولاً.");
      const { liveSettings } = getState();
      const system = SYSTEM_PROMPTS.article_graph;
      const user = buildUserPrompt("article_graph", {
        article: { sections: article.sections, main_entities: article.main_entities, title: article.title },
        entities: ENTITIES.slice(0, 20).map((e) => ({ entity_id: e.entity_id, approved_ar: e.approved_ar })),
        active_rules: RULES.slice(0, 12).map((r) => ({ rule_id: r.rule_id, area: r.area })),
        golden: GOLDEN.slice(0, 6).map((g) => ({ gold_id: g.gold_id, span_text: g.span_text })),
      });
      const res = await callLlmPhase({ data: { baseUrl: liveSettings.baseUrl, apiKey, model: liveSettings.model, system, user } });
      if (!res.ok) throw new Error(`LLM ${res.status}: ${res.error}`);
      const parsed = JSON.parse(res.json) as { mermaid?: string };
      if (!parsed.mermaid) throw new Error("النموذج لم يُعِد حقل mermaid.");
      setLlmMermaid(parsed.mermaid);
      log("system", "graph_llm_generated", { article_id: articleId });
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-lg font-semibold">رسم بياني للمقال (Article + Persistent links)</h2>
          <p className="text-xs text-muted-foreground max-w-xl">
            عُقد المقال (أقسام، كيانات، عبارات مرشحة) مرتبطة بحقول المعجم والقواعد والمراجعات الذهبية.
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <Badge variant={mode === "live" ? "destructive" : "secondary"}>{mode}</Badge>
          <Button size="sm" onClick={runLlmGraph} disabled={busy || mode !== "live"}>
            {busy ? "جارٍ التوليد…" : "ولّد الرسم عبر LLM"}
          </Button>
        </div>
      </div>

      {err && <p className="text-xs text-red-600">{err}</p>}

      <section className="border rounded-md p-3 bg-card">
        <h3 className="text-sm font-semibold mb-2">رسم بياني مُولَّد محلياً من بنية المقال</h3>
        <MermaidView source={auto} id={`auto-${articleId}`} />
        <details className="mt-2">
          <summary className="text-xs cursor-pointer text-muted-foreground">عرض مصدر Mermaid</summary>
          <pre className="text-[11px] bg-muted/50 p-2 rounded overflow-x-auto mt-1" dir="ltr">{auto}</pre>
        </details>
      </section>

      {llmMermaid && (
        <section className="border rounded-md p-3 bg-card">
          <h3 className="text-sm font-semibold mb-2">رسم بياني مُولَّد عبر النموذج اللغوي (Live)</h3>
          <MermaidView source={llmMermaid} id={`llm-${articleId}`} />
          <details className="mt-2">
            <summary className="text-xs cursor-pointer text-muted-foreground">عرض مصدر Mermaid</summary>
            <pre className="text-[11px] bg-muted/50 p-2 rounded overflow-x-auto mt-1" dir="ltr">{llmMermaid}</pre>
          </details>
        </section>
      )}

      <section className="border rounded-md p-3 bg-card">
        <h3 className="text-sm font-semibold mb-2">رسم مرجعي ثابت (الفيكسر)</h3>
        <MermaidView source={SEED_MERMAID} id="seed" />
      </section>

      <details className="border rounded-md p-3 bg-card">
        <summary className="text-sm font-semibold cursor-pointer">برومت النظام — article_graph</summary>
        <pre className="text-[11px] bg-muted/50 p-3 rounded overflow-x-auto mt-2" dir="ltr">{SYSTEM_PROMPTS.article_graph}</pre>
      </details>
    </div>
  );
}