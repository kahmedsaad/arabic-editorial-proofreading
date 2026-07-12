import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { getState } from "@/lib/store";
import { bulkEntities, listEntities, upsertEntity, type MvpEntity } from "@/lib/api/mvp";

export const Route = createFileRoute("/entities")({
  component: EntitiesPage,
  head: () => ({ meta: [{ title: "مستودع الكيانات" }] }),
});

function emptyEntity(): MvpEntity {
  return {
    entity_id: "",
    canonical_ar: "",
    aliases: [],
    category: "organization",
    active: true,
    policy_profiles: [],
    version: "1.0",
  };
}

function EntitiesPage() {
  const base = getState().liveSettings.baseUrl;
  const [entities, setEntities] = useState<MvpEntity[]>([]);
  const [paste, setPaste] = useState("");
  const [editing, setEditing] = useState<MvpEntity | null>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  async function reload() {
    try {
      setEntities(await listEntities(base));
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void reload();
  }, []);

  async function saveEdit() {
    if (!editing) return;
    try {
      await upsertEntity(editing, base);
      setMsg(`تم حفظ ${editing.entity_id}`);
      setEditing(null);
      await reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function doBulk() {
    try {
      const saved = await bulkEntities(paste, base);
      setMsg(`أُدرجت ${saved.length} كيانات`);
      setPaste("");
      await reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h1 className="text-2xl font-bold">مستودع الكيانات ({entities.length})</h1>
        <Button variant="outline" onClick={() => setEditing(emptyEntity())}>
          كيان جديد
        </Button>
      </div>

      <section className="border rounded-md p-3 bg-card mb-4 space-y-2">
        <h2 className="font-semibold text-sm">لصق من Excel</h2>
        <p className="text-xs text-muted-foreground">
          أعمدة: approved_ar / canonical_ar, aliases, category/type, current_title, policy_profiles
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

      {editing && (
        <section className="border rounded-md p-4 bg-card mb-4 space-y-2">
          <h2 className="font-semibold">تحرير كيان</h2>
          <div className="grid sm:grid-cols-2 gap-2">
            <Input
              placeholder="entity_id"
              value={editing.entity_id}
              onChange={(e) => setEditing({ ...editing, entity_id: e.target.value })}
              dir="ltr"
            />
            <Input
              placeholder="الاسم المعتمد"
              value={editing.canonical_ar}
              onChange={(e) => setEditing({ ...editing, canonical_ar: e.target.value })}
            />
            <Input
              placeholder="aliases مفصولة بفاصلة"
              value={editing.aliases.join(", ")}
              onChange={(e) =>
                setEditing({
                  ...editing,
                  aliases: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                })
              }
            />
            <Input
              placeholder="category"
              value={editing.category}
              onChange={(e) => setEditing({ ...editing, category: e.target.value })}
              dir="ltr"
            />
            <Input
              placeholder="current_title"
              value={editing.current_title ?? ""}
              onChange={(e) => setEditing({ ...editing, current_title: e.target.value })}
            />
            <Input
              placeholder="policy_profiles"
              value={(editing.policy_profiles ?? []).join(", ")}
              onChange={(e) =>
                setEditing({
                  ...editing,
                  policy_profiles: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                })
              }
            />
          </div>
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

      <div className="overflow-x-auto border rounded-md">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-xs">
            <tr>
              <th className="text-right p-2">المعرف</th>
              <th className="text-right p-2">الاسم المعتمد</th>
              <th className="text-right p-2">النوع</th>
              <th className="text-right p-2">اللقب الحالي</th>
              <th className="text-right p-2">أسماء بديلة</th>
              <th className="text-right p-2">النسخة</th>
              <th className="text-right p-2"></th>
            </tr>
          </thead>
          <tbody>
            {entities.map((e) => (
              <tr key={e.entity_id} className="border-t">
                <td className="p-2 font-mono">{e.entity_id}</td>
                <td className="p-2 font-arabic" dir="rtl">
                  {e.canonical_ar}
                </td>
                <td className="p-2">
                  <Badge variant="outline">{e.category}</Badge>
                </td>
                <td className="p-2 font-arabic" dir="rtl">
                  {e.current_title ?? "—"}
                </td>
                <td className="p-2 text-xs">{e.aliases.join("، ") || "—"}</td>
                <td className="p-2 text-xs">v{e.version ?? "1.0"}</td>
                <td className="p-2">
                  <Button size="sm" variant="outline" onClick={() => setEditing(e)}>
                    تعديل
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
