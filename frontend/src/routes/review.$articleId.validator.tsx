import { createFileRoute } from "@tanstack/react-router";
import { SEED_VALIDATOR } from "@/data/seed";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/review/$articleId/validator")({
  component: ValidatorPage,
});

function ValidatorPage() {
  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">المُتحقق (Validator)</h2>
      <p className="text-xs text-muted-foreground">
        التحقق من المخطط، صحة معرفات المرشحين، حقل requires_editor_approval، عدم التطبيق التلقائي، عدم تعديل نص الاقتباس.
      </p>
      <div className="border rounded-md p-3 bg-card">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-semibold">الحالة:</span>
          <Badge variant="default">{SEED_VALIDATOR.status}</Badge>
        </div>
        <ul className="text-sm space-y-1">
          {SEED_VALIDATOR.checks.map((c) => (
            <li key={c.name} className="flex justify-between font-mono">
              <span>{c.name}</span>
              <Badge variant={c.status === "passed" ? "secondary" : "destructive"}>{c.status}</Badge>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}