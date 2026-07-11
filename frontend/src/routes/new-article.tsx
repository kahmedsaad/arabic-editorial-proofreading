import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { addArticle, useStore, getApiKey } from "@/lib/store";
import type { Article, ArticleSection } from "@/lib/types";

export const Route = createFileRoute("/new-article")({
  head: () => ({ meta: [{ title: "مقال جديد — Editorial Lab" }] }),
  component: NewArticlePage,
});

const SURFACES: ArticleSection["surface"][] = ["headline", "metadata", "caption", "lead", "paragraph", "section_heading"];

function NewArticlePage() {
  const navigate = useNavigate();
  const mode = useStore((s) => s.mode);
  const [title, setTitle] = useState("");
  const [contentType, setContentType] = useState("breaking_news");
  const [paste, setPaste] = useState("");
  const [sections, setSections] = useState<ArticleSection[]>([
    { section_id: "headline", surface: "headline", label: "العنوان", text: "" },
    { section_id: "lead", surface: "lead", label: "المقدمة", text: "" },
    { section_id: "p1", surface: "paragraph", label: "فقرة 1", text: "" },
  ]);

  function pasteToSections() {
    const lines = paste.split(/\n+/).map((s) => s.trim()).filter(Boolean);
    if (!lines.length) return;
    const [head, ...rest] = lines;
    const next: ArticleSection[] = [
      { section_id: "headline", surface: "headline", label: "العنوان", text: head },
    ];
    rest.forEach((t, i) => next.push({ section_id: `p${i + 1}`, surface: i === 0 ? "lead" : "paragraph", label: i === 0 ? "المقدمة" : `فقرة ${i}`, text: t }));
    setSections(next);
    if (!title) setTitle(head.slice(0, 100));
  }

  function updateSection(idx: number, patch: Partial<ArticleSection>) {
    setSections((s) => s.map((x, i) => (i === idx ? { ...x, ...patch } : x)));
  }
  function removeSection(idx: number) {
    setSections((s) => s.filter((_, i) => i !== idx));
  }
  function addSection() {
    setSections((s) => [...s, { section_id: `s${s.length}`, surface: "paragraph", label: `فقرة ${s.length}`, text: "" }]);
  }

  function submit(autorun: boolean) {
    const finalTitle = title.trim() || sections.find((s) => s.surface === "headline")?.text || "مقال بلا عنوان";
    const clean = sections.filter((s) => s.text.trim());
    if (!clean.length) return;
    const id = `custom-${Date.now().toString(36)}`;
    const article: Article = {
      article_id: id,
      title: finalTitle,
      topic: finalTitle,
      language: "ar",
      content_type: contentType,
      main_entities: [],
      sections: clean,
    };
    addArticle(article);
    if (autorun) {
      navigate({ to: "/review/$articleId/phases", params: { articleId: id }, search: { autorun: 1 } });
    } else {
      navigate({ to: "/review/$articleId", params: { articleId: id } });
    }
  }

  const hasKey = !!getApiKey();

  return (
    <AppShell>
      <div className="mb-4 flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-2xl font-bold">مقال جديد</h1>
          <p className="text-xs text-muted-foreground">
            ألصق نصاً عربياً أو اكتب الأقسام يدوياً، ثم شغّل المراحل (Demo أو Live LLM عبر مفتاحك).
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant={mode === "live" ? "destructive" : "secondary"}>{mode}</Badge>
          <Badge variant={hasKey ? "default" : "outline"}>{hasKey ? "API key set" : "no API key"}</Badge>
        </div>
      </div>

      <section className="grid md:grid-cols-2 gap-3 mb-6">
        <div className="border rounded-md p-3 bg-card">
          <Label>العنوان</Label>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} dir="rtl" />
          <Label className="mt-3 block">نوع المحتوى</Label>
          <select className="w-full border rounded h-9 px-2 bg-background" value={contentType} onChange={(e) => setContentType(e.target.value)} dir="ltr">
            {["breaking_news", "news", "opinion", "sports", "culture", "tech", "science"].map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div className="border rounded-md p-3 bg-card">
          <Label>إلصاق سريع (السطر الأول عنوان، ثم فقرات)</Label>
          <textarea
            className="w-full border rounded p-2 h-28 text-sm bg-background"
            value={paste}
            onChange={(e) => setPaste(e.target.value)}
            dir="rtl"
            placeholder="عنوان المقال…&#10;المقدمة…&#10;فقرة 1…"
          />
          <Button size="sm" className="mt-2" type="button" variant="outline" onClick={pasteToSections}>تحويل إلى أقسام</Button>
        </div>
      </section>

      <section className="space-y-3 mb-6">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">الأقسام</h2>
          <Button size="sm" variant="outline" type="button" onClick={addSection}>+ قسم</Button>
        </div>
        {sections.map((s, i) => (
          <div key={i} className="border rounded-md p-3 bg-card grid md:grid-cols-[140px_1fr_auto] gap-2 items-start">
            <select
              className="border rounded h-9 px-2 bg-background text-sm"
              value={s.surface}
              onChange={(e) => updateSection(i, { surface: e.target.value as ArticleSection["surface"] })}
              dir="ltr"
            >
              {SURFACES.map((sf) => <option key={sf}>{sf}</option>)}
            </select>
            <textarea
              className="w-full border rounded p-2 text-sm bg-background min-h-[64px]"
              value={s.text}
              onChange={(e) => updateSection(i, { text: e.target.value })}
              dir="rtl"
              placeholder="نص القسم…"
            />
            <Button size="sm" variant="ghost" type="button" onClick={() => removeSection(i)}>حذف</Button>
          </div>
        ))}
      </section>

      <section className="flex gap-2 flex-wrap">
        <Button onClick={() => submit(true)} disabled={mode === "live" && !hasKey}>
          احفظ وشغّل المراحل {mode === "live" ? "(Live)" : "(Demo)"}
        </Button>
        <Button variant="outline" onClick={() => submit(false)}>احفظ فقط</Button>
        {mode === "live" && !hasKey && (
          <span className="text-xs text-red-600 self-center">أضف مفتاح API في الإعدادات لتشغيل Live.</span>
        )}
      </section>
    </AppShell>
  );
}