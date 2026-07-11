import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { RULES } from "@/data/seed";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";
import { Input } from "@/components/ui/input";

export const Route = createFileRoute("/rules")({
  component: RulesPage,
  head: () => ({ meta: [{ title: "مستودع القواعد" }] }),
});

function RulesPage() {
  const [q, setQ] = useState("");
  const filtered = RULES.filter((r) =>
    !q || r.rule_id.toLowerCase().includes(q.toLowerCase()) || r.name.toLowerCase().includes(q.toLowerCase()) || r.natural_language.includes(q),
  );
  return (
    <AppShell>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">مستودع القواعد ({RULES.length})</h1>
        <Input placeholder="بحث في القواعد…" value={q} onChange={(e) => setQ(e.target.value)} className="max-w-xs" dir="rtl" />
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        {filtered.map((r) => (
          <div key={r.rule_id} className="border rounded-md p-3 bg-card">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="font-semibold font-mono text-sm">{r.rule_id} — {r.name}</h3>
              <div className="flex gap-1">
                <Badge variant="outline">{r.type}</Badge>
                <Badge variant="secondary">{r.default_decision}</Badge>
                {r.area && <Badge variant="outline">{r.area}</Badge>}
              </div>
            </div>
            <p className="text-sm mt-2 font-arabic" dir="rtl">{r.natural_language}</p>
            <div className="text-xs text-muted-foreground mt-2 grid sm:grid-cols-2 gap-1">
              <div>fields: <span className="font-mono">{r.trigger_fields.join(", ") || "—"}</span></div>
              <div>requires: <span className="font-mono">{r.requires.join(", ") || "—"}</span></div>
              <div>surfaces: <span className="font-mono">{(r.applies_when.surfaces ?? []).join(", ") || "any"}</span></div>
              <div>exceptions: <span className="font-mono">{r.exceptions.join(", ") || "—"}</span></div>
            </div>
          </div>
        ))}
      </div>
    </AppShell>
  );
}