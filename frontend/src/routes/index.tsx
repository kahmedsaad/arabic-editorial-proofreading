import { createFileRoute, Link, redirect, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { setMode, useStore } from "@/lib/store";
import { Badge } from "@/components/ui/badge";
import { allArticles } from "@/lib/articles";
import { getAuthSession } from "@/lib/auth";

export const Route = createFileRoute("/")({
  beforeLoad: () => {
    if (typeof window !== "undefined" && !getAuthSession()) {
      throw redirect({ to: "/login" });
    }
  },
  head: () => ({
    meta: [
      { title: "تدقيق تحريري — عرض تجريبي" },
      {
        name: "description",
        content: "الصق مقالاً عربياً واحصل على اقتراحات تحريرية للمراجعة البشرية.",
      },
    ],
  }),
  component: Index,
});

function Index() {
  const mode = useStore((s) => s.mode);
  const customCount = useStore((s) => s.customArticles.length);
  const navigate = useNavigate();
  const articles = allArticles();

  return (
    <AppShell>
      <section className="space-y-2 mb-8">
        <h1 className="text-3xl font-bold">تدقيق تحريري عربي — عرض تجريبي</h1>
        <p className="text-muted-foreground max-w-3xl">
          الصق مقالاً أو اختر نموذجاً، ثم راجع الاقتراحات: القواعد والكيانات المرتبطة، المرشحات، الحكم،
          والتحقق، ثم القرار النهائي مع قبول أو رفض أو تعليق.
        </p>
        <p className="text-sm font-semibold text-emerald-700">
          لا يُطبَّق أي اقتراح آلي على النص الأصلي. كل تغيير يحتاج موافقة المحرر.
        </p>
      </section>

      <section className="grid md:grid-cols-2 gap-4 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>وضع التشغيل</CardTitle>
            <CardDescription>
              العرض التجريبي يستخدم بيانات ثابتة. المحرك الحي يستدعي واجهة التدقيق.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex gap-2 flex-wrap">
              <Button
                variant={mode === "demo" ? "default" : "outline"}
                onClick={() => setMode("demo")}
              >
                عرض تجريبي
              </Button>
              <Button
                variant={mode === "live" ? "default" : "outline"}
                onClick={() => setMode("live")}
              >
                محرك حي
              </Button>
              <Link to="/settings" className="self-center text-sm underline text-muted-foreground">
                الإعدادات
              </Link>
            </div>
            {mode === "live" && (
              <Badge variant="outline">يستدعي POST /api/v1/reviews</Badge>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>ابدأ بسرعة</CardTitle>
            <CardDescription>مقال جديد أو نموذج جاهز</CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2 flex-wrap">
            <Button onClick={() => navigate({ to: "/new-article" })}>مقال جديد</Button>
            <Button variant="outline" onClick={() => navigate({ to: "/rules" })}>
              القواعد
            </Button>
            <Button variant="outline" onClick={() => navigate({ to: "/entities" })}>
              الكيانات
            </Button>
          </CardContent>
        </Card>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-3">
          المقالات ({articles.length}
          {customCount ? ` منها ${customCount} مخصصة` : ""})
        </h2>
        <div className="grid md:grid-cols-2 gap-3">
          {articles.map((a) => (
            <Link
              key={a.article_id}
              to="/review/$articleId"
              params={{ articleId: a.article_id }}
              className="border rounded-md p-4 bg-card hover:border-primary transition-colors block"
            >
              <div className="font-semibold" dir="rtl">
                {a.title}
              </div>
              <div className="text-xs text-muted-foreground mt-1 font-mono">{a.article_id}</div>
              <div className="text-xs mt-2 flex gap-2 flex-wrap">
                <Badge variant="secondary">{a.content_type}</Badge>
                <Badge variant="outline">{a.main_entities.length} كيانات</Badge>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
