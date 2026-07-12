import { createFileRoute, Link } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getState } from "@/lib/store";
import { authHeaders } from "@/lib/auth";
import { getMvpApiBase } from "@/lib/api/mvp";

export const Route = createFileRoute("/admin/logs")({
  component: AdminLogsPage,
  head: () => ({ meta: [{ title: "سجلات خط الأنابيب" }] }),
});

type LogSummary = {
  review_id: string;
  document_id: string;
  step_count: number;
  step_ids: string[];
  updated_at: string;
  created_at: string;
};

type LogStep = {
  step_id: string;
  label: string;
  kind: string;
  system_prompt?: string | null;
  user_payload?: string | null;
  raw_response?: string | null;
  context?: Record<string, unknown>;
  output_summary?: Record<string, unknown>;
  started_at?: string;
  finished_at?: string;
};

type FullLog = {
  review_id: string;
  document_id: string;
  steps: LogStep[];
  updated_at: string;
  created_at: string;
};

async function apiGet<T>(path: string): Promise<T> {
  const base = getMvpApiBase(getState().liveSettings.baseUrl);
  const res = await fetch(`${base}${path}`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

function AdminLogsPage() {
  const [list, setList] = useState<LogSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [detail, setDetail] = useState<FullLog | null>(null);
  const [openStep, setOpenStep] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const [live, setLive] = useState(true);

  const reloadList = useCallback(async () => {
    try {
      const rows = await apiGet<LogSummary[]>("/api/v1/admin/pipeline-logs");
      setList(rows);
      setErr("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }, []);

  const loadDetail = useCallback(async (reviewId: string) => {
    try {
      const log = await apiGet<FullLog>(`/api/v1/admin/pipeline-logs/${reviewId}`);
      setDetail(log);
      setActiveId(reviewId);
      setErr("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void reloadList();
  }, [reloadList]);

  useEffect(() => {
    if (!live) return;
    const t = setInterval(() => {
      void reloadList();
      if (activeId) void loadDetail(activeId);
    }, 2500);
    return () => clearInterval(t);
  }, [live, activeId, reloadList, loadDetail]);

  return (
    <>
      <div className="flex items-center justify-between flex-wrap gap-2 mb-4">
        <div>
          <h1 className="text-2xl font-bold">سجلات خط الأنابيب (Admin)</h1>
          <p className="text-sm text-muted-foreground">
            كل خطوة: السياق، برومت النظام، الحمولة، والاستجابة الخام — للتشخيص فقط.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant={live ? "default" : "outline"} size="sm" onClick={() => setLive((v) => !v)}>
            {live ? "بث مباشر: تشغيل" : "بث مباشر: إيقاف"}
          </Button>
          <Button variant="outline" size="sm" onClick={() => void reloadList()}>
            تحديث
          </Button>
          <Link to="/admin" className="text-sm underline self-center">
            ← الإعدادات
          </Link>
        </div>
      </div>

      {err && <p className="text-sm text-destructive mb-3">{err}</p>}

      <div className="grid lg:grid-cols-[320px_1fr] gap-4">
        <aside className="border rounded-md p-2 bg-card max-h-[80vh] overflow-y-auto space-y-1">
          {list.length === 0 && (
            <p className="text-xs text-muted-foreground p-2">لا سجلات بعد. شغّل مراجعة مقال أولاً.</p>
          )}
          {list.map((row) => (
            <button
              key={row.review_id}
              type="button"
              onClick={() => void loadDetail(row.review_id)}
              className={`w-full text-right p-2 rounded text-sm border ${
                activeId === row.review_id ? "border-primary bg-accent" : "border-transparent hover:bg-muted/50"
              }`}
            >
              <div className="font-mono text-xs">{row.review_id}</div>
              <div className="text-xs text-muted-foreground">{row.document_id}</div>
              <div className="flex gap-1 mt-1 flex-wrap">
                <Badge variant="secondary">{row.step_count} خطوات</Badge>
              </div>
            </button>
          ))}
        </aside>

        <section className="space-y-3 max-h-[80vh] overflow-y-auto">
          {!detail && (
            <p className="text-sm text-muted-foreground">اختر مراجعة من القائمة لعرض التفاصيل.</p>
          )}
          {detail && (
            <>
              <div className="border rounded-md p-3 bg-card">
                <div className="font-mono text-sm">{detail.review_id}</div>
                <div className="text-xs text-muted-foreground">
                  doc={detail.document_id} · updated={detail.updated_at || "—"}
                </div>
              </div>
              {detail.steps.map((step) => {
                const open = openStep === step.step_id + step.started_at;
                return (
                  <div key={`${step.step_id}-${step.started_at}`} className="border rounded-md bg-card">
                    <button
                      type="button"
                      className="w-full text-right p-3 flex items-center justify-between gap-2"
                      onClick={() =>
                        setOpenStep(open ? null : step.step_id + step.started_at)
                      }
                    >
                      <div>
                        <div className="font-semibold text-sm">{step.label}</div>
                        <div className="text-xs text-muted-foreground font-mono">
                          {step.step_id} · {step.kind}
                        </div>
                      </div>
                      <Badge variant="outline">{open ? "إخفاء" : "عرض"}</Badge>
                    </button>
                    {open && (
                      <div className="border-t p-3 space-y-3 text-xs" dir="ltr">
                        {step.system_prompt != null && step.system_prompt !== "" && (
                          <div>
                            <div className="font-semibold mb-1">System prompt</div>
                            <pre className="whitespace-pre-wrap bg-muted/50 p-2 rounded max-h-64 overflow-auto">
                              {step.system_prompt}
                            </pre>
                          </div>
                        )}
                        {step.user_payload != null && step.user_payload !== "" && (
                          <div>
                            <div className="font-semibold mb-1">User payload / context sent</div>
                            <pre className="whitespace-pre-wrap bg-muted/50 p-2 rounded max-h-80 overflow-auto">
                              {step.user_payload}
                            </pre>
                          </div>
                        )}
                        {step.raw_response != null && step.raw_response !== "" && (
                          <div>
                            <div className="font-semibold mb-1">Raw LLM / step response</div>
                            <pre className="whitespace-pre-wrap bg-muted/50 p-2 rounded max-h-80 overflow-auto">
                              {step.raw_response}
                            </pre>
                          </div>
                        )}
                        {step.context && Object.keys(step.context).length > 0 && (
                          <div>
                            <div className="font-semibold mb-1">Context metadata</div>
                            <pre className="whitespace-pre-wrap bg-muted/50 p-2 rounded max-h-64 overflow-auto">
                              {JSON.stringify(step.context, null, 2)}
                            </pre>
                          </div>
                        )}
                        {step.output_summary && Object.keys(step.output_summary).length > 0 && (
                          <div>
                            <div className="font-semibold mb-1">Output summary → next step input</div>
                            <pre className="whitespace-pre-wrap bg-muted/50 p-2 rounded max-h-80 overflow-auto">
                              {JSON.stringify(step.output_summary, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </>
          )}
        </section>
      </div>
    </>
  );
}
