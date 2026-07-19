import { Link, useNavigate } from "@tanstack/react-router";
import { ReactNode, useEffect, useState } from "react";
import { useStore } from "@/lib/store";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getState } from "@/lib/store";
import { clearAuthSession, getAuthSession, isAdmin, type AuthSession } from "@/lib/auth";
import { logoutMvp } from "@/lib/api/mvp";

export function AppShell({ children }: { children: ReactNode }) {
  const mode = useStore((s) => s.mode);
  const [session, setSession] = useState<AuthSession | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const current = getAuthSession();
    setSession(current);
    if (!current) {
      navigate({ to: "/login" });
    }
  }, [navigate]);

  const admin = session?.role === "admin" || isAdmin();

  async function handleLogout() {
    await logoutMvp(getState().liveSettings.baseUrl);
    clearAuthSession();
    setSession(null);
    navigate({ to: "/login" });
  }

  return (
    <div className="min-h-screen bg-background text-foreground" dir="rtl">
      <header className="border-b sticky top-0 z-30 bg-background/95 backdrop-blur">
        <div className="mx-auto max-w-7xl px-4 py-3 flex items-center gap-4 flex-wrap">
          <Link to="/" className="font-bold text-lg">تدقيق تحريري — عرض تجريبي</Link>
          <span className="text-xs text-muted-foreground">Arabic Editorial Review Demo</span>
          <nav className="flex gap-1 text-sm mr-auto ml-0 flex-wrap" dir="rtl">
            <NavLink to="/" label="الرئيسية" />
            <NavLink to="/new-article" label="مقال جديد" />
            <NavLink to="/rules" label="القواعد" />
            <NavLink to="/entities" label="الكيانات" />
            <NavLink to="/audit" label="سجل الإجراءات" />
            {admin && <NavLink to="/admin" label="الإدارة" />}
            {admin && <NavLink to="/admin/logs" label="سجلات التشخيص" />}
            <NavLink to="/settings" label="الإعدادات" />
          </nav>
          <div className="flex items-center gap-2">
            {session ? (
              <>
                <Badge variant="outline">{session.username} · {session.role}</Badge>
                <Button size="sm" variant="ghost" onClick={handleLogout}>خروج</Button>
              </>
            ) : (
              <Link to="/login" className="text-sm underline">تسجيل الدخول</Link>
            )}
            <Badge variant={mode === "demo" ? "secondary" : "outline"}>
              {mode === "demo" ? "عرض تجريبي" : "محرك حي"}
            </Badge>
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
