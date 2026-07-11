import { createFileRoute, useParams, useSearch } from "@tanstack/react-router";
import { useEffect, useRef } from "react";
import { SEED_PHASES } from "@/data/seed";
import { usePipeline } from "@/lib/pipeline/orchestrator";
import { SYSTEM_PROMPTS } from "@/lib/pipeline/prompts";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useStore } from "@/lib/store";
import { z } from "zod";

const search = z.object({ autorun: z.coerce.number().optional() }).parse;

export const Route = createFileRoute("/review/$articleId/phases")({
  validateSearch: (input: Record<string, unknown>) => search(input),
  component: PhasesPage,
});

function PhasesPage() {
  const { articleId } = useParams({ from: "/review/$articleId/phases" });
  const { autorun } = useSearch({ from: "/review/$articleId/phases" });
  const mode = useStore((s) => s.mode);
  const { status, phases, run, runPhase, reset } = usePipeline(articleId);
  const started = useRef(false);
  useEffect(() => {
    if (autorun && !started.current && status === "idle") {
      started.current = true;
      run();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autorun, status]);
  const data: Array<typeof phases[number]> =
    status === "idle"
      ? SEED_PHASES.map((p) => ({ ...p, status: "complete" as const }))
      : phases;
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">المراحل الـ16 — عرض تفصيلي</h2>
        <div className="flex gap-2">
          <Badge variant={mode === "demo" ? "secondary" : "destructive"}>{mode}</Badge>
          <Button size="sm" onClick={run} disabled={status === "running"}>تشغيل</Button>
          <Button size="sm" variant="ghost" onClick={reset}>إعادة</Button>
        </div>
      </div>
      <ol className="space-y-2">
        {data.map((p, idx) => (
          <li key={p.phase} className="border rounded-md p-3 bg-card">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="font-semibold text-sm">{p.name}</h3>
              <div className="flex gap-2 text-xs">
                <Badge variant="outline">{p.source ?? "mock"}</Badge>
                <Badge variant={
                  p.status === "complete" ? "default" :
                  p.status === "running" ? "secondary" :
                  p.status === "error" ? "destructive" : "outline"
                }>{p.status}</Badge>
                {typeof p.confidence === "number" && <span className="text-muted-foreground">conf {Math.round(p.confidence * 100)}%</span>}
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 px-2 text-[11px]"
                  disabled={p.status === "running"}
                  onClick={() => runPhase(idx)}
                >
                  {p.status === "error" ? "إعادة المحاولة" : "تشغيل هذه المرحلة"}
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">{p.purpose}</p>
            <div className="grid sm:grid-cols-2 gap-2 mt-2 text-xs">
              <div><span className="font-semibold">approach:</span> {p.approach}</div>
              <div><span className="font-semibold">ref:</span> {p.reference_source}</div>
              <div><span className="font-semibold">input:</span> {p.input_summary}</div>
              <div><span className="font-semibold">next:</span> {p.next_phase ?? "—"}</div>
            </div>
            <details className="mt-2">
              <summary className="text-xs cursor-pointer text-muted-foreground">output JSON</summary>
              <pre className="text-[11px] bg-muted/50 p-2 rounded overflow-x-auto mt-1" dir="ltr">{JSON.stringify(p.output, null, 2)}</pre>
            </details>
            {"raw" in p && p.raw && (
              <details className="mt-2" open={"error" in p && !!p.error}>
                <summary className="text-xs cursor-pointer text-muted-foreground">الرد الخام من النموذج (raw)</summary>
                <pre className="text-[11px] bg-muted/50 p-2 rounded overflow-x-auto mt-1 whitespace-pre-wrap" dir="ltr">{p.raw}</pre>
              </details>
            )}
            {SYSTEM_PROMPTS[p.phase] && (
              <details className="mt-2">
                <summary className="text-xs cursor-pointer text-muted-foreground">برومت النظام (System prompt)</summary>
                <pre className="text-[11px] bg-muted/50 p-2 rounded overflow-x-auto mt-1" dir="ltr">{SYSTEM_PROMPTS[p.phase]}</pre>
              </details>
            )}
            {"error" in p && p.error && <p className="text-xs text-red-600 mt-2">{p.error}</p>}
          </li>
        ))}
      </ol>
    </div>
  );
}