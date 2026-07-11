import { useState } from "react";
import type { Suggestion } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import {
  acceptSuggestion,
  rejectSuggestion,
  editSuggestion,
  commentSuggestion,
} from "@/lib/store";
import { getRule, getGolden } from "@/data/seed";

const SEVERITY_TONE: Record<string, string> = {
  ban: "destructive",
  hard_warning: "destructive",
  soft_warning: "secondary",
  replace: "default",
  suggest: "default",
  acceptable_with_note: "outline",
  acceptable: "outline",
};

export function SuggestionCard({
  articleId, s, active, onSelect,
}: { articleId: string; s: Suggestion; active: boolean; onSelect: () => void }) {
  const [editing, setEditing] = useState(false);
  const [edited, setEdited] = useState(s.edited_text ?? s.suggested_text ?? "");
  const [note, setNote] = useState(s.editor_note ?? "");

  const tone = (SEVERITY_TONE[s.severity] ?? "secondary") as
    | "default" | "secondary" | "destructive" | "outline";

  return (
    <Card
      onClick={onSelect}
      className={`cursor-pointer transition-shadow ${active ? "ring-2 ring-ring" : ""}`}
      id={`sug-${s.suggestion_id}`}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <CardTitle className="text-sm font-semibold">
            {s.suggestion_id} · {s.type} · {s.phase}
          </CardTitle>
          <Badge variant={tone}>{s.severity}</Badge>
        </div>
        <div className="text-xs text-muted-foreground">
          status: <span className="font-mono">{s.status}</span> · validator:{" "}
          <span className="font-mono">{s.validator_status}</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="grid grid-cols-1 gap-1">
          <div>
            <span className="text-muted-foreground text-xs">original (locked)</span>
            <div className="rounded bg-muted/60 px-2 py-1 font-arabic" dir="rtl">
              {s.anchor.original_text}
            </div>
          </div>
          {s.suggested_text != null && (
            <div>
              <span className="text-muted-foreground text-xs">suggested replacement</span>
              {editing ? (
                <Textarea
                  value={edited}
                  onChange={(e) => setEdited(e.target.value)}
                  dir="rtl"
                  className="font-arabic"
                />
              ) : (
                <div className="rounded bg-emerald-50 dark:bg-emerald-950/30 px-2 py-1 font-arabic" dir="rtl">
                  {s.edited_text ?? s.suggested_text}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="text-xs text-muted-foreground">{s.reason}</div>

        <div className="text-xs space-y-1">
          {s.rule_ids.length > 0 && (
            <div>
              <span className="font-semibold">rules:</span>{" "}
              {s.rule_ids.map((id) => (
                <span key={id} title={getRule(id)?.natural_language ?? id} className="mr-1 font-mono">
                  {id}
                </span>
              ))}
            </div>
          )}
          {s.golden_ids && s.golden_ids.length > 0 && (
            <div>
              <span className="font-semibold">precedents:</span>{" "}
              {s.golden_ids.map((id) => (
                <span key={id} title={getGolden(id)?.expected_reason ?? id} className="mr-1 font-mono">
                  {id}
                </span>
              ))}
            </div>
          )}
          {s.proof_steps.length > 0 && (
            <details className="mt-1">
              <summary className="cursor-pointer text-muted-foreground">proof steps</summary>
              <ul className="list-disc pr-5 space-y-0.5 mt-1">
                {s.proof_steps.map((p, i) => (
                  <li key={i} className="font-mono text-[11px]">{p}</li>
                ))}
              </ul>
            </details>
          )}
        </div>

        <div className="space-y-2">
          <Input
            placeholder="ملاحظة المحرر (اختياري)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            dir="rtl"
            onBlur={() => note !== (s.editor_note ?? "") && commentSuggestion(articleId, s.suggestion_id, note)}
          />
          <div className="flex gap-2 flex-wrap">
            <Button
              size="sm"
              variant="default"
              disabled={s.suggested_text == null && !editing}
              onClick={(e) => {
                e.stopPropagation();
                if (editing) editSuggestion(articleId, s.suggestion_id, edited);
                acceptSuggestion(articleId, s.suggestion_id);
                setEditing(false);
              }}
            >قبول</Button>
            <Button
              size="sm"
              variant="outline"
              onClick={(e) => { e.stopPropagation(); setEditing((v) => !v); }}
            >{editing ? "إلغاء التعديل" : "تعديل"}</Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => { e.stopPropagation(); rejectSuggestion(articleId, s.suggestion_id); }}
            >رفض</Button>
          </div>
          <p className="text-[11px] text-muted-foreground">
            لا يُطبَّق على النص الأصلي. القبول يضيف التغيير إلى المعاينة المنقَّحة فقط.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}