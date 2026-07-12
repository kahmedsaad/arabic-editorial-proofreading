import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { loginMvp } from "@/lib/api/mvp";
import { setAuthSession } from "@/lib/auth";
import { getState } from "@/lib/store";

export const Route = createFileRoute("/login")({
  component: LoginPage,
  head: () => ({ meta: [{ title: "تسجيل الدخول" }] }),
});

function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("user");
  const [password, setPassword] = useState("demo");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const base = getState().liveSettings.baseUrl;
      const session = await loginMvp(username.trim(), password, base);
      setAuthSession(session);
      navigate({ to: session.role === "admin" ? "/admin" : "/" });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4" dir="rtl">
      <form onSubmit={onSubmit} className="w-full max-w-sm border rounded-lg p-6 bg-card space-y-4">
        <div>
          <h1 className="text-xl font-bold">تسجيل الدخول</h1>
          <p className="text-sm text-muted-foreground mt-1">
            المستخدم العام: <span className="font-mono">user</span> — أو حساب الإدارة:{" "}
            <span className="font-mono">admin</span>
          </p>
        </div>
        <div className="space-y-2">
          <Label>اسم المستخدم</Label>
          <Input value={username} onChange={(e) => setUsername(e.target.value)} dir="ltr" />
        </div>
        <div className="space-y-2">
          <Label>كلمة المرور</Label>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            dir="ltr"
          />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? "جارٍ الدخول…" : "دخول"}
        </Button>
      </form>
    </div>
  );
}
