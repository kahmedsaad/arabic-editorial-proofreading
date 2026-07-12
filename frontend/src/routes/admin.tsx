import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { getAuthSession } from "@/lib/auth";

export const Route = createFileRoute("/admin")({
  beforeLoad: () => {
    if (typeof window === "undefined") return;
    const session = getAuthSession();
    if (!session || session.role !== "admin") {
      throw redirect({ to: "/login" });
    }
  },
  component: AdminLayout,
  head: () => ({ meta: [{ title: "لوحة الإدارة" }] }),
});

function AdminLayout() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}
