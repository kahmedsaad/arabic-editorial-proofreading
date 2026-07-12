import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { getState } from "@/lib/store";
import { listPrompts, setPublicPassword, updatePrompt } from "@/lib/api/mvp";

export const Route = createFileRoute("/admin/")({
  component: AdminSettingsPage,
  head: () => ({ meta: [{ title: "لوحة الإدارة" }] }),
});

type PromptRow = { phase: string; body: string; version: number; updated_at: string };

function AdminSettingsPage() {
  const base = getState().liveSettings.baseUrl;
  const [prompts, setPrompts] = useState<PromptRow[]>([]);
  const [active, setActive] = useState("discover");
  const [body, setBody] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  async function reload() {
    try {
      const rows = await listPrompts(base);
      setPrompts(rows);
      const current = rows.find((r) => r.phase === active) ?? rows[0];
      if (current) {
        setActive(current.phase);
        setBody(current.body);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function selectPhase(phase: string) {
    setActive(phase);
    const row = prompts.find((p) => p.phase === phase);
    setBody(row?.body ?? "");
  }

  async function savePrompt() {
    setMsg("");
    setErr("");
    try {
      await updatePrompt(active, body, base);
      setMsg(`تم حفظ برومت «${active}» بنسخة جديدة.`);
      await reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function savePassword() {
    setMsg("");
    setErr("");
    try {
      await setPublicPassword(password, base);
      setMsg("تم تحديث كلمة مرور المستخدم العام (user) في الجلسة الحالية.");
      setPassword("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <>
      <div className="flex items-center justify-between flex-wrap gap-2 mb-4">
        <h1 className="text-2xl font-bold">لوحة الإدارة</h1>
        <Link to="/admin/logs" className="text-sm underline">
          سجلات التشخيص →
        </Link>
      </div>
      <p className="text-sm text-muted-foreground mb-6">
        تحرير برومبتات المراحل. كلمة مرور <span className="font-mono">admin</span> من{" "}
        <span className="font-mono">.env → ADMIN_PASSWORD</span> (حالياً بعد إعادة التشغيل).
      </p>

      <section className="border rounded-md p-4 bg-card mb-6 space-y-3">
        <h2 className="font-semibold">كلمة مرور المستخدم العام (user)</h2>
        <p className="text-xs text-muted-foreground">
          المصدر الدائم: <span className="font-mono">PUBLIC_PASSWORD</span> في{" "}
          <span className="font-mono">.env</span>. التغيير هنا يعمل حتى إعادة تشغيل الخادم.
        </p>
        <div className="flex gap-2 flex-wrap items-end">
          <div className="flex-1 min-w-[200px]">
            <Label>كلمة المرور الجديدة لـ user</Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              dir="ltr"
            />
          </div>
          <Button onClick={savePassword} disabled={password.length < 4}>
            حفظ كلمة المرور
          </Button>
        </div>
      </section>

      <section className="border rounded-md p-4 bg-card space-y-3">
        <h2 className="font-semibold">برومبتات المراحل</h2>
        <div className="flex gap-2 flex-wrap">
          {prompts.map((p) => (
            <Button
              key={p.phase}
              size="sm"
              variant={active === p.phase ? "default" : "outline"}
              onClick={() => selectPhase(p.phase)}
            >
              {p.phase}
              <Badge variant="secondary" className="mr-2">
                v{p.version}
              </Badge>
            </Button>
          ))}
        </div>
        <Textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          className="min-h-[280px] font-mono text-xs"
          dir="ltr"
        />
        <Button onClick={savePrompt}>حفظ البرومت</Button>
      </section>

      {msg && <p className="text-sm text-emerald-700 mt-4">{msg}</p>}
      {err && <p className="text-sm text-destructive mt-4">{err}</p>}
    </>
  );
}
