import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { ENTITIES } from "@/data/seed";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/entities")({
  component: EntitiesPage,
  head: () => ({ meta: [{ title: "مستودع الكيانات" }] }),
});

function EntitiesPage() {
  return (
    <AppShell>
      <h1 className="text-2xl font-bold mb-4">مستودع الكيانات ({ENTITIES.length})</h1>
      <div className="overflow-x-auto border rounded-md">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-xs">
            <tr>
              <th className="text-right p-2">المعرف</th>
              <th className="text-right p-2">الاسم المعتمد</th>
              <th className="text-right p-2">النوع</th>
              <th className="text-right p-2">اللقب الحالي</th>
              <th className="text-right p-2">ملفات السياسة</th>
              <th className="text-right p-2">آخر تحقق</th>
            </tr>
          </thead>
          <tbody>
            {ENTITIES.map((e) => (
              <tr key={e.entity_id} className="border-t">
                <td className="p-2 font-mono">{e.entity_id}</td>
                <td className="p-2 font-arabic" dir="rtl">{e.approved_ar}</td>
                <td className="p-2"><Badge variant="outline">{e.type}</Badge></td>
                <td className="p-2 font-arabic" dir="rtl">{e.current_title ?? "—"}</td>
                <td className="p-2 text-xs">{e.policy_profiles.join(", ") || "—"}</td>
                <td className="p-2 text-xs">{e.last_verified ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}