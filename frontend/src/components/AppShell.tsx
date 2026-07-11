import { Link } from "@tanstack/react-router";
import { ReactNode } from "react";
import { useStore } from "@/lib/store";
import { Badge } from "@/components/ui/badge";

export function AppShell({ children }: { children: ReactNode }) {
  const mode = useStore((s) => s.mode);
  return (
    <div className="min-h-screen bg-background text-foreground" dir="rtl">
      <header className="border-b sticky top-0 z-30 bg-background/95 backdrop-blur">
        <div className="mx-auto max-w-7xl px-4 py-3 flex items-center gap-4 flex-wrap">
          <Link to="/" className="font-bold text-lg">مختبر التدقيق التحريري</Link>
          <span className="text-xs text-muted-foreground">Editorial Proofreading &amp; Style Compliance Lab</span>
          <nav className="flex gap-1 text-sm mr-auto ml-0 flex-wrap" dir="rtl">
            <NavLink to="/" label="الرئيسية" />
            <NavLink to="/new-article" label="مقال جديد" />
            <NavLink to="/rules" label="القواعد" />
            <NavLink to="/entities" label="الكيانات" />
            <NavLink to="/lexical" label="المعجم" />
            <NavLink to="/golden" label="المرجعيات" />
            <NavLink to="/audit" label="سجل التدقيق" />
            <NavLink to="/settings" label="الإعدادات" />
          </nav>
          <div className="flex items-center gap-2">
            <Badge variant={mode === "demo" ? "secondary" : "destructive"}>
              {mode === "demo" ? "Demo Mode" : "Live LLM simulation — not production accuracy"}
            </Badge>
            <Badge variant="outline" className="text-emerald-600 border-emerald-300">Original locked</Badge>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}

function NavLink({ to, label }: { to: string; label: string }) {
  return (
    <Link
      to={to}
      className="px-3 py-1.5 rounded-md hover:bg-accent transition-colors"
      activeProps={{ className: "px-3 py-1.5 rounded-md bg-accent font-semibold" }}
      activeOptions={{ exact: to === "/" }}
    >
      {label}
    </Link>
  );
}