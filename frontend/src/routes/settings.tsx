import { createFileRoute, useSearch } from "@tanstack/react-router";
import { z } from "zod";
import { AppShell } from "@/components/AppShell";
import { useStore, setLiveSettings, setMode, setRole, resetAll, getApiKey } from "@/lib/store";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useEffect, useRef, useState } from "react";
import { checkMvpHealth } from "@/lib/api/mvp";

const search = z.object({ focus: z.string().optional() }).parse;

export const Route = createFileRoute("/settings")({
  validateSearch: (input: Record<string, unknown>) => search(input),
  component: SettingsPage,
  head: () => ({ meta: [{ title: "الإعدادات" }] }),
});

function SettingsPage() {
  const mode = useStore((s) => s.mode);
  const role = useStore((s) => s.role);
  const live = useStore((s) => s.liveSettings);
  const { focus } = useSearch({ from: "/settings" });
  const [apiKey, setApiKey] = useState("");
  const [health, setHealth] = useState<string>("");
  const apiRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    setApiKey(getApiKey());
  }, []);
  useEffect(() => {
    if (focus === "apiKey" && apiRef.current) {
      apiRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
      apiRef.current.focus();
    }
  }, [focus]);

  async function pingMvp() {
    setHealth("checking…");
    const result = await checkMvpHealth(live.baseUrl);
    setHealth(result.ok ? JSON.stringify(result.body) : `ERROR: ${result.error}`);
  }

  return (
    <AppShell>
      <h1 className="text-2xl font-bold mb-4">الإعدادات</h1>

      <section className="border rounded-md p-4 bg-card mb-4 space-y-3">
        <h2 className="font-semibold">وضع التشغيل</h2>
        <div className="flex gap-2">
          <Button variant={mode === "demo" ? "default" : "outline"} onClick={() => setMode("demo")}>
            Demo Mode
          </Button>
          <Button variant={mode === "live" ? "default" : "outline"} onClick={() => setMode("live")}>
            Live / MVP Engine
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Demo Mode يستخدم بيانات ثابتة. Live Mode يستدعي محرك التدقيق (FastAPI MVP) عبر{" "}
          <span className="font-mono">POST /api/v1/reviews</span>.
        </p>
      </section>

      <section className="border rounded-md p-4 bg-card mb-4 space-y-3">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <h2 className="font-semibold">محرك MVP (الواجهة ↔ الخلفية)</h2>
          <Badge variant="outline">افتراضي: http://127.0.0.1:8001</Badge>
        </div>
        <div className="grid sm:grid-cols-2 gap-3 text-sm">
          <div className="sm:col-span-2">
            <Label>API Base URL</Label>
            <Input
              value={live.baseUrl}
              onChange={(e) => setLiveSettings({ baseUrl: e.target.value })}
              dir="ltr"
              placeholder="http://127.0.0.1:8001"
            />
          </div>
          <div className="sm:col-span-2 flex items-center gap-2">
            <Button
              type="button"
              variant={live.useMvpEngine ? "default" : "outline"}
              onClick={() => setLiveSettings({ useMvpEngine: true })}
            >
              Use MVP Engine
            </Button>
            <Button
              type="button"
              variant={!live.useMvpEngine ? "default" : "outline"}
              onClick={() => setLiveSettings({ useMvpEngine: false })}
            >
              Legacy OpenAI phases
            </Button>
          </div>
          <div className="sm:col-span-2 flex gap-2 items-center">
            <Button type="button" variant="secondary" onClick={pingMvp}>
              اختبار الاتصال
            </Button>
            {health && (
              <span className="text-xs font-mono break-all" dir="ltr">
                {health}
              </span>
            )}
          </div>
        </div>
      </section>

      <section className="border rounded-md p-4 bg-card mb-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">إعدادات Legacy LLM (اختياري)</h2>
          <Badge variant="outline">فقط إذا عطّلت MVP Engine</Badge>
        </div>
        <div className="grid sm:grid-cols-2 gap-3 text-sm">
          <div>
            <Label>Model</Label>
            <Input
              value={live.model}
              onChange={(e) => setLiveSettings({ model: e.target.value })}
              dir="ltr"
            />
          </div>
          <div className="sm:col-span-2">
            <Label>API Key</Label>
            <Input
              ref={apiRef}
              type="password"
              value={apiKey}
              onChange={(e) => {
                setApiKey(e.target.value);
                setLiveSettings({ apiKey: e.target.value });
              }}
              dir="ltr"
              placeholder="sk-…"
            />
            <p className="text-[11px] text-muted-foreground mt-1">
              غير مطلوب لمسار MVP. مفتاح Gemini يُضبط على الخادم عبر .env وليس هنا.
            </p>
          </div>
        </div>
      </section>

      <section className="border rounded-md p-4 bg-card mb-4 space-y-3">
        <h2 className="font-semibold">دور المستخدم</h2>
        <div className="flex gap-2">
          {(["editor", "language_reviewer", "demo_admin"] as const).map((r) => (
            <Button key={r} variant={role === r ? "default" : "outline"} onClick={() => setRole(r)}>
              {r}
            </Button>
          ))}
        </div>
      </section>

      <section className="border rounded-md p-4 bg-card mb-4 space-y-3">
        <h2 className="font-semibold">إدارة العرض التوضيحي</h2>
        <Button variant="destructive" onClick={() => resetAll()}>
          إعادة تعيين كل بيانات النموذج
        </Button>
      </section>
    </AppShell>
  );
}
