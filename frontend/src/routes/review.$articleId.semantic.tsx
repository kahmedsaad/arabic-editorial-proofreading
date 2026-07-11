import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { SEED_SEMANTIC, LEXICAL } from "@/data/seed";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useStore, getApiKey, getState } from "@/lib/store";
import { callLlmPhase } from "@/lib/llm.functions";
import { SYSTEM_PROMPTS, buildUserPrompt } from "@/lib/pipeline/prompts";

export const Route = createFileRoute("/review/$articleId/semantic")({
  component: SemanticPage,
});

interface SemanticResult {
  query_span: string;
  nearest_fields: Array<{ field: string; score: number }>;
  decision: string;
  note?: string;
}

function SemanticPage() {
  const mode = useStore((s) => s.mode);
  const [span, setSpan] = useState(SEED_SEMANTIC.query_span);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [llm, setLlm] = useState<SemanticResult | null>(null);

  async function runLlm() {
    setBusy(true); setErr(null);
    try {
      const apiKey = getApiKey();
      if (!apiKey) throw new Error("لا يوجد مفتاح API. افتح الإعدادات.");
      const { liveSettings } = getState();
      const system = SYSTEM_PROMPTS.semantic_search;
      const user = buildUserPrompt("semantic_search", {
        query_span: span,
        lexical_fields: LEXICAL.map((l) => ({ field: l.field, canonical: l.canonical, neighbors: l.semantic_neighbors, example: l.example })),
      });
      const res = await callLlmPhase({ data: { baseUrl: liveSettings.baseUrl, apiKey, model: liveSettings.model, system, user } });
      if (!res.ok) throw new Error(`LLM ${res.status}: ${res.error}`);
      setLlm(JSON.parse(res.json));
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const display = llm ?? SEED_SEMANTIC;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">مفتش البحث الدلالي</h2>
        <p className="text-xs text-muted-foreground">
          الانتخاب ≠ مخالفة. هذه طبقة تُرشِّح فقط المرشحين الذين يستحقون الحكم العلائقي.
        </p>
      </div>

      <div className="border rounded-md p-3 bg-card flex flex-wrap gap-2 items-end">
        <div className="flex-1 min-w-[240px]">
          <label className="text-xs text-muted-foreground">عبارة مرشَّحة (Arabic)</label>
          <Input value={span} onChange={(e) => setSpan(e.target.value)} dir="rtl" />
        </div>
        <Badge variant={mode === "live" ? "destructive" : "secondary"}>{mode}</Badge>
        <Button size="sm" onClick={runLlm} disabled={busy || mode !== "live" || !span.trim()}>
          {busy ? "جارٍ…" : "محاكاة embedding عبر LLM"}
        </Button>
      </div>
      {err && <p className="text-xs text-red-600">{err}</p>}

      <div className="border rounded-md p-4 bg-card">
        <div className="text-sm font-arabic" dir="rtl">
          العبارة المرشَّحة: <span className="font-semibold">{display.query_span}</span>
          {llm ? <Badge className="mr-2" variant="outline">LLM</Badge> : <Badge className="mr-2" variant="secondary">fixture</Badge>}
        </div>
        <table className="text-xs mt-2 w-full">
          <thead><tr className="text-muted-foreground"><th className="text-right">الحقل</th><th className="text-right">درجة التشابه</th></tr></thead>
          <tbody>
            {display.nearest_fields.map((f) => (
              <tr key={f.field}><td className="font-mono">{f.field}</td><td>{Number(f.score).toFixed(2)}</td></tr>
            ))}
          </tbody>
        </table>
        <p className="text-xs mt-2"><span className="font-semibold">القرار:</span> {display.decision}</p>
        {display.note && <p className="text-xs text-muted-foreground mt-1">{display.note}</p>}
      </div>

      <details className="border rounded-md p-3 bg-card">
        <summary className="text-sm font-semibold cursor-pointer">برومت النظام — semantic_search</summary>
        <pre className="text-[11px] bg-muted/50 p-3 rounded overflow-x-auto mt-2" dir="ltr">{SYSTEM_PROMPTS.semantic_search}</pre>
      </details>

      <div>
        <h3 className="text-sm font-semibold mb-2">حقول المعجم المتاحة</h3>
        <ul className="text-xs grid sm:grid-cols-2 gap-2">
          {LEXICAL.map((l) => (
            <li key={l.lex_id} className="border rounded p-2">
              <div className="font-mono">{l.lex_id} — <span className="font-arabic">{l.canonical}</span></div>
              <div className="text-muted-foreground">field: {l.field}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}