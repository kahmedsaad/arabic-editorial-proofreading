const TOKEN_KEY = "aj-demo/auth-token";
const ROLE_KEY = "aj-demo/auth-role";
const USER_KEY = "aj-demo/auth-user";

export type AuthSession = {
  token: string;
  role: "user" | "admin";
  username: string;
};

export function getAuthSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem(TOKEN_KEY);
  const role = localStorage.getItem(ROLE_KEY) as AuthSession["role"] | null;
  const username = localStorage.getItem(USER_KEY);
  if (!token || !role || !username) return null;
  return { token, role, username };
}

export function setAuthSession(session: AuthSession) {
  localStorage.setItem(TOKEN_KEY, session.token);
  localStorage.setItem(ROLE_KEY, session.role);
  localStorage.setItem(USER_KEY, session.username);
}

export function clearAuthSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(USER_KEY);
}

export function authHeaders(): Record<string, string> {
  const session = getAuthSession();
  if (!session?.token) return {};
  return { Authorization: `Bearer ${session.token}` };
}

export function isAdmin(): boolean {
  return getAuthSession()?.role === "admin";
}
