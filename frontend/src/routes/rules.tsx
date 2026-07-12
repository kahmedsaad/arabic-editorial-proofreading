import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { getState } from "@/lib/store";
import {
  authorRules,
  bulkRules,
  listRules,
  upsertRule,
  type MvpRule,
} from "@/lib/api/mvp";

export const Route = createFileRoute("/rules")({
  component: RulesPage,
  head: () => ({ meta: [{ title: "مستودع القواعد" }] }),
});

function emptyRule(): MvpRule {
  return {
    rule_id: "",
    version: "1.0",
    title_ar: "",
    category: "terminology",
    rule_type: "mechanical",
    description_ar: "",
    applies_to_zones: ["body", "headline"],
    severity: "medium",
    keywords: [],
    examples: [],
    active: true,
  };
}

function RulesPage() {
  const base = getState().liveSettings.baseUrl;
  const [rules, setRules] = useState<MvpRule[]>([]);
  const [q, setQ] = useState("");
  const [paste, setPaste] = useState("");
  const [authorText, setAuthorText] = useState("");
  const [preview, setPreview] = useState<MvpRule[]>([]);
  const [editing, setEditing] = useState<MvpRule | null>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  async function reload() {
    try {
      setRules(await listRules(base));
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void reload();
  }, []);

  const filtered = rules.filter(
    (r) =>
      !q ||
      r.rule_id.toLowerCase().includes(q.toLowerCase()) ||
      r.title_ar.includes(q) ||
      r.description_ar.includes(q),
  );

  async function saveEdit() {
    if (!editing) return;
    setErr("");
    try {
      await upsertRule(editing, base);
      setMsg(`تم حفظ ${editing.rule_id}`);
      setEditing(null);
      await reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function doBulk() {
    setErr("");
    try {
      const saved = await bulkRules(paste, base);
      setMsg(`أُدرجت ${saved.length} قاعدة من اللصق`);
      setPaste("");
      await reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function doAuthor(confirm: boolean) {
    setErr("");
    try {
      const res = await authorRules(authorText, confirm, base);
      setPreview(res.preview);
      if (confirm) {
        setMsg(`أُضيفت ${res.saved.length} قاعدة`);
        setAuthorText("");
        setPreview([]);
        await reload();
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h1 className="text-2xl font-bold">مستودع القواعد ({rules.length})</h1>
        <div className="flex gap-2">
          <Input
            placeholder="بحث…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="max-w-xs"
            dir="rtl"
          />
          <Button variant="outline" onClick={() => setEditing(emptyRule())}>
            قاعدة جديدة
          </Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-4 mb-6">
        <section className="border rounded-md p-3 bg-card space-y-2">
          <h2 className="font-semibold text-sm">لصق من Excel / جداول</h2>
          <p className="text-xs text-muted-foreground">
            أعمدة مثل: title_ar, description_ar, category, keywords (مفصولة بـ ;)
          </p>
          <Textarea
            value={paste}
            onChange={(e) => setPaste(e.target.value)}
            className="min-h-[100px] text-xs"
            dir="rtl"
          />
          <Button size="sm" onClick={doBulk} disabled={!paste.trim()}>
            إدراج اللصق
          </Button>
        </section>
        <section className="border rounded-md p-3 bg-card space-y-2">
          <h2 className="font-semibold text-sm">تأليف قاعدة بمساعدة النموذج</h2>
          <Textarea
            value={authorText}
            onChange={(e) => setAuthorText(e.target.value)}
            className="min-h-[100px]"
            dir="rtl"
            placeholder="اكتب القاعدة بلغة حرة أو الصق عدة صفوف…"
          />
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => doAuthor(false)} disabled={!authorText.trim()}>
              معاينة
            </Button>
            <Button size="sm" onClick={() => doAuthor(true)} disabled={!authorText.trim()}>
              تأكيد والإضافة
            </Button>
          </div>
          {preview.length > 0 && (
            <pre className="text-[11px] bg-muted/50 p-2 rounded overflow-x-auto" dir="ltr">
              {JSON.stringify(preview, null, 2)}
            </pre>
          )}
        </section>
      </div>

      {editing && (
        <section className="border rounded-md p-4 bg-card mb-4 space-y-2">
          <h2 className="font-semibold">تحرير قاعدة</h2>
          <div className="grid sm:grid-cols-2 gap-2 text-sm">
            <Input
              placeholder="rule_id"
              value={editing.rule_id}
              onChange={(e) => setEditing({ ...editing, rule_id: e.target.value })}
              dir="ltr"
            />
            <Input
              placeholder="العنوان"
              value={editing.title_ar}
              onChange={(e) => setEditing({ ...editing, title_ar: e.target.value })}
            />
            <Input
              placeholder="category"
              value={editing.category}
              onChange={(e) => setEditing({ ...editing, category: e.target.value })}
              dir="ltr"
            />
            <Input
              placeholder="rule_type"
              value={editing.rule_type}
              onChange={(e) => setEditing({ ...editing, rule_type: e.target.value })}
              dir="ltr"
            />
            <Input
              placeholder="severity"
              value={editing.severity}
              onChange={(e) => setEditing({ ...editing, severity: e.target.value })}
              dir="ltr"
            />
            <Input
              placeholder="keywords مفصولة بفاصلة"
              value={editing.keywords.join(", ")}
              onChange={(e) =>
                setEditing({
                  ...editing,
                  keywords: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                })
              }
            />
          </div>
          <Textarea
            value={editing.description_ar}
            onChange={(e) => setEditing({ ...editing, description_ar: e.target.value })}
            dir="rtl"
          />
          <div className="flex gap-2">
            <Button onClick={saveEdit}>حفظ (نسخة جديدة)</Button>
            <Button variant="ghost" onClick={() => setEditing(null)}>
              إلغاء
            </Button>
          </div>
        </section>
      )}

      {msg && <p className="text-sm text-emerald-700 mb-2">{msg}</p>}
      {err && <p className="text-sm text-destructive mb-2">{err}</p>}

      <div className="grid md:grid-cols-2 gap-3">
        {filtered.map((r) => (
          <div key={r.rule_id} className="border rounded-md p-3 bg-card">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="font-semibold font-mono text-sm">
                {r.rule_id} — {r.title_ar}
              </h3>
              <div className="flex gap-1">
                <Badge variant="outline">{r.rule_type}</Badge>
                <Badge variant="secondary">{r.severity}</Badge>
                <Badge variant="outline">v{r.version}</Badge>
              </div>
            </div>
            <p className="text-sm mt-2 font-arabic" dir="rtl">
              {r.description_ar}
            </p>
            <Button size="sm" variant="outline" className="mt-2" onClick={() => setEditing(r)}>
              تعديل
            </Button>
          </div>
        ))}
      </div>
    </AppShell>
  );
}
