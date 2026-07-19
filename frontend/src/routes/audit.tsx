import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { useStore } from "@/lib/store";
import { requireAuth } from "@/lib/auth";

export const Route = createFileRoute("/audit")({
  beforeLoad: () => {
    requireAuth();
  },
  component: AuditPage,
  head: () => ({ meta: [{ title: "سجل التدقيق" }] }),
});

function AuditPage() {
  const audit = useStore((s) => s.audit);
  return (
    <AppShell>
      <h1 className="text-2xl font-bold mb-4">سجل التدقيق ({audit.length})</h1>
      <p className="text-xs text-muted-foreground mb-3">
        كل إجراء — قبول، رفض، تعديل، تعليق، تشغيل مرحلة، تصدير — يُسجَّل هنا مع وقت ومُنفِّذ.
      </p>
      {audit.length === 0 && <p className="text-sm text-muted-foreground">لا توجد أحداث بعد. ابدأ المراجعة لتسجيل الأحداث.</p>}
      <div className="overflow-x-auto border rounded-md">
        <table className="w-full text-xs">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-right p-2">الوقت</th>
              <th className="text-right p-2">المُنفِّذ</th>
              <th className="text-right p-2">الإجراء</th>
              <th className="text-right p-2">المقال</th>
              <th className="text-right p-2">الاقتراح</th>
              <th className="text-right p-2">تفاصيل</th>
            </tr>
          </thead>
          <tbody>
            {audit.map((e) => (
              <tr key={e.event_id} className="border-t">
                <td className="p-2 font-mono">{e.timestamp.slice(11, 19)}</td>
                <td className="p-2">{e.actor}</td>
                <td className="p-2 font-mono">{e.action}</td>
                <td className="p-2 font-mono">{e.article_id || "—"}</td>
                <td className="p-2 font-mono">{e.suggestion_id ?? "—"}</td>
                <td className="p-2">{e.note ?? (e.original_text ? `«${e.original_text}» → «${e.suggested_text ?? ""}»` : "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}