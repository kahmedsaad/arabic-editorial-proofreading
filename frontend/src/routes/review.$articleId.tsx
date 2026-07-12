import { createFileRoute, Link, Outlet, useParams } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { findArticle } from "@/lib/articles";
import { getAuthSession, isAdmin } from "@/lib/auth";

export const Route = createFileRoute("/review/$articleId")({
  component: ReviewLayout,
  head: () => ({ meta: [{ title: "مراجعة المقال" }] }),
});

function ReviewLayout() {
  const { articleId } = useParams({ from: "/review/$articleId" });
  const article = findArticle(articleId);
  if (!article) {
    return (
      <AppShell>
        <p>المقال غير موجود.</p>
      </AppShell>
    );
  }

  const admin = isAdmin() || getAuthSession()?.role === "admin";
  const tabs: Array<{ to: string; label: string; exact?: boolean; adminOnly?: boolean }> = [
    { to: "/review/$articleId", label: "المراجعة", exact: true },
    { to: "/review/$articleId/preview", label: "المعاينة المنقّحة" },
    { to: "/review/$articleId/validator", label: "نتائج التحقق", adminOnly: true },
    { to: "/review/$articleId/evaluation", label: "التقييم", adminOnly: true },
  ];

  return (
    <AppShell>
      <div className="mb-4">
        <h1 className="text-xl font-bold leading-7" dir="rtl">
          {article.title}
        </h1>
        <p className="text-xs text-muted-foreground font-mono">
          {article.article_id} · {article.content_type}
        </p>
      </div>
      <nav className="border-b mb-4 flex gap-1 flex-wrap text-sm" dir="rtl">
        {tabs
          .filter((t) => !t.adminOnly || admin)
          .map((t) => (
            <Link
              key={t.to}
              to={t.to as "/review/$articleId"}
              params={{ articleId }}
              activeOptions={{ exact: t.exact ?? false }}
              className="px-3 py-2 -mb-px border-b-2 border-transparent hover:border-muted-foreground/30"
              activeProps={{
                className: "px-3 py-2 -mb-px border-b-2 border-primary font-semibold",
              }}
            >
              {t.label}
            </Link>
          ))}
      </nav>
      <Outlet />
    </AppShell>
  );
}
