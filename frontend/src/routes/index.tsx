import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { setMode, useStore, getApiKey } from "@/lib/store";
import { Badge } from "@/components/ui/badge";
import { allArticles } from "@/lib/articles";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Editorial Proofreading & Style Compliance Lab" },
      { name: "description", content: "Pick a fixture article and a mode to start the staged editorial review." },
    ],
  }),
  component: Index,
});

function Index() {
  const mode = useStore((s) => s.mode);
  const customCount = useStore((s) => s.customArticles.length);
  const navigate = useNavigate();
  const articles = allArticles();
  const hasKey = !!getApiKey();

  function chooseLive() {
    setMode("live");
    if (!hasKey) navigate({ to: "/settings", search: { focus: "apiKey" } });
  }

  return (
    <AppShell>
      <section className="space-y-2 mb-8">
        <h1 className="text-3xl font-bold">مختبر التدقيق التحريري والامتثال للأسلوب — Al Jazeera Arabic</h1>
        <p className="text-muted-foreground max-w-3xl">
          نموذج تفاعلي يُظهر كيف يعمل محرك مرحلي للتدقيق التحريري: تدقيق لغوي، أسلوب آلي، كيانات، شخصيات عامة،
          معجم منظَّم، رسم بياني للمقال، استرجاع قواعد ومراجع، حزمة سياق للنموذج اللغوي، تحقّق، ثم مراجعة بشرية.
        </p>
        <p className="text-sm font-semibold text-emerald-700">
          لا يُطبَّق أي اقتراح آلي على النص الأصلي. كل تغيير يحتاج موافقة المحرر.
        </p>
      </section>

      <section className="grid md:grid-cols-2 gap-4 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>اختر وضع التشغيل</CardTitle>
            <CardDescription>Demo Mode يستخدم بيانات ثابتة. Live Mode يستدعي نموذجك اللغوي.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex gap-2 flex-wrap">
              <Button variant={mode === "demo" ? "default" : "outline"} onClick={() => setMode("demo")}>Demo Mode</Button>
              <Button variant={mode === "live" ? "default" : "outline"} onClick={chooseLive}>Live Experiment Mode</Button>
              <Link to="/settings" className="self-center text-sm underline text-muted-foreground">إعدادات Live</Link>
            </div>
            {mode === "live" && (
              <div className="text-xs flex items-center gap-2">
                <Badge variant={hasKey ? "default" : "destructive"}>{hasKey ? "API key set" : "Missing API key"}</Badge>
                {!hasKey && (
                  <Link to="/settings" search={{ focus: "apiKey" }} className="underline">أضف المفتاح</Link>
                )}
              </div>
            )}
            <div className="pt-1">
              <Link to="/new-article"><Button size="sm" variant="secondary">+ مقال جديد لتشغيل المراحل</Button></Link>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>روح القصة</CardTitle>
            <CardDescription>المرحلية، الاسترجاع المُحكم، والمحرر هو القرار النهائي.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-1">
            <p>1. الكيانات: مَن وماذا. 2. المعجم المنظَّم: أي العبارات تستحق المراجعة.</p>
            <p>3. القواعد العلائقية: متى تنطبق؟ 4. المرجعيات الذهبية: ماذا قرّر المحررون من قبل؟</p>
          </CardContent>
        </Card>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-3">
          المقالات {customCount > 0 && <span className="text-xs text-muted-foreground">(منها {customCount} مخصّص)</span>}
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          {articles.map((a) => (
            <Card key={a.article_id}>
              <CardHeader>
                <CardTitle className="text-base leading-7">{a.title}</CardTitle>
                <CardDescription>
                  <Badge variant="outline">{a.content_type}</Badge>{" "}
                  <span className="text-xs">{a.article_id}</span>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-3">{a.sections[1]?.text ?? a.sections[0].text}</p>
                <div className="mt-4 flex gap-2">
                  <Link to="/review/$articleId" params={{ articleId: a.article_id }}>
                    <Button>ابدأ المراجعة</Button>
                  </Link>
                  <Link to="/review/$articleId/phases" params={{ articleId: a.article_id }} search={{ autorun: mode === "live" ? 1 : undefined }}>
                    <Button variant="outline">{mode === "live" ? "تشغيل Live" : "عرض المراحل"}</Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
