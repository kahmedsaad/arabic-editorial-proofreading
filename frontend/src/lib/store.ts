import { useSyncExternalStore } from "react";
import type { AppMode, Article, AuditEvent, LiveSettings, Suggestion, SuggestionStatus } from "./types";
import { SEED_AUDIT, SEED_SUGGESTIONS } from "@/data/seed";

// ---- localStorage-backed global store -------------------------------------
// (Lovable Cloud persistence will replace this in a follow-up iteration.)

type State = {
  mode: AppMode;
  liveSettings: LiveSettings;
  // suggestions per article_id
  suggestions: Record<string, Suggestion[]>;
  audit: AuditEvent[];
  role: "editor" | "language_reviewer" | "demo_admin";
  customArticles: Article[];
};

const STORAGE_KEY = "aj-editor-lab/v1";

function envApiBaseUrl(): string | undefined {
  if (typeof import.meta === "undefined") return undefined;
  const v = (import.meta as ImportMeta & { env?: Record<string, string> }).env
    ?.VITE_API_BASE_URL;
  return v ? v.replace(/\/$/, "") : undefined;
}

function resolveLiveBaseUrl(stored?: string): string {
  const fromEnv = envApiBaseUrl();
  const local =
    !stored ||
    stored.includes("127.0.0.1") ||
    stored.includes("localhost");
  if (fromEnv && local) return fromEnv;
  return (stored || fromEnv || "http://127.0.0.1:8001").replace(/\/$/, "");
}

const initialState: State = {
  mode: "live",
  liveSettings: {
    baseUrl: resolveLiveBaseUrl(),
    apiKey: "",
    model: "mvp-engine",
    useMvpEngine: true,
  },
  suggestions: { "aj-hezbollah-drones-v3": SEED_SUGGESTIONS },
  audit: SEED_AUDIT,
  role: "editor",
  customArticles: [],
};

let state: State = load();
const listeners = new Set<() => void>();

function load(): State {
  if (typeof window === "undefined") return initialState;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return initialState;
    const parsed = JSON.parse(raw) as Partial<State>;
    return {
      ...initialState,
      ...parsed,
      // never persist the API key
      liveSettings: {
        ...initialState.liveSettings,
        ...(parsed.liveSettings ?? {}),
        baseUrl: resolveLiveBaseUrl(parsed.liveSettings?.baseUrl),
        apiKey: "",
        useMvpEngine: parsed.liveSettings?.useMvpEngine ?? true,
      },
      suggestions: { ...initialState.suggestions, ...(parsed.suggestions ?? {}) },
      customArticles: parsed.customArticles ?? [],
    };
  } catch {
    return initialState;
  }
}

function persist() {
  if (typeof window === "undefined") return;
  const { apiKey: _ignore, ...safeSettings } = state.liveSettings;
  void _ignore;
  const toSave = { ...state, liveSettings: { ...safeSettings, apiKey: "" } };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
  } catch {
    /* ignore quota */
  }
  // sessionStorage holds the api key only while the tab is open
  try {
    sessionStorage.setItem(STORAGE_KEY + "/key", state.liveSettings.apiKey ?? "");
  } catch {
    /* ignore */
  }
}

function setState(updater: (s: State) => State) {
  state = updater(state);
  persist();
  listeners.forEach((l) => l());
}

export function getState(): State {
  return state;
}

export function subscribe(l: () => void) {
  listeners.add(l);
  return () => listeners.delete(l);
}

export function useStore<T>(selector: (s: State) => T): T {
  return useSyncExternalStore(
    (l) => {
      listeners.add(l);
      return () => listeners.delete(l);
    },
    () => selector(state),
    () => selector(initialState),
  );
}

// ---- action helpers --------------------------------------------------------

export function setMode(mode: AppMode) {
  setState((s) => ({ ...s, mode }));
  log("system", "mode_changed", { note: `Mode set to ${mode}` });
}

export function setRole(role: State["role"]) {
  setState((s) => ({ ...s, role }));
}

export function setLiveSettings(partial: Partial<LiveSettings>) {
  setState((s) => ({ ...s, liveSettings: { ...s.liveSettings, ...partial } }));
}

export function getApiKey(): string {
  if (typeof window === "undefined") return "";
  return sessionStorage.getItem(STORAGE_KEY + "/key") || state.liveSettings.apiKey || "";
}

export function getSuggestions(articleId: string): Suggestion[] {
  return state.suggestions[articleId] ?? [];
}

export function setSuggestions(articleId: string, suggestions: Suggestion[]) {
  setState((s) => ({ ...s, suggestions: { ...s.suggestions, [articleId]: suggestions } }));
}

export function updateSuggestion(
  articleId: string,
  suggestion_id: string,
  patch: Partial<Suggestion>,
) {
  setState((s) => {
    const list = s.suggestions[articleId] ?? [];
    return {
      ...s,
      suggestions: {
        ...s.suggestions,
        [articleId]: list.map((x) => (x.suggestion_id === suggestion_id ? { ...x, ...patch } : x)),
      },
    };
  });
}

export function resetArticle(articleId: string) {
  if (articleId === "aj-hezbollah-drones-v3") {
    setSuggestions(articleId, SEED_SUGGESTIONS);
  } else {
    setSuggestions(articleId, []);
  }
  log("demo_admin", "reset_article", { article_id: articleId });
}

export function resetAll() {
  setState(() => ({ ...initialState, suggestions: { "aj-hezbollah-drones-v3": SEED_SUGGESTIONS } }));
}

// ---- custom articles -------------------------------------------------------

export function addArticle(article: Article) {
  setState((s) => ({
    ...s,
    customArticles: [article, ...s.customArticles.filter((a) => a.article_id !== article.article_id)],
    suggestions: { ...s.suggestions, [article.article_id]: [] },
  }));
  log("editor_demo", "article_created", { article_id: article.article_id, note: article.title });
}

// ---- audit log -------------------------------------------------------------

export function log(
  actor: string,
  action: string,
  extra: Partial<AuditEvent> & { article_id?: string },
) {
  const evt: AuditEvent = {
    event_id: "EV-" + Math.random().toString(36).slice(2, 10).toUpperCase(),
    timestamp: new Date().toISOString(),
    actor,
    action,
    article_id: extra.article_id ?? "",
    ...extra,
  };
  setState((s) => ({ ...s, audit: [evt, ...s.audit].slice(0, 500) }));
}

// ---- editor actions --------------------------------------------------------

export function acceptSuggestion(articleId: string, suggestion_id: string) {
  const s = getSuggestions(articleId).find((x) => x.suggestion_id === suggestion_id);
  if (!s) return;
  updateSuggestion(articleId, suggestion_id, { status: "accepted" as SuggestionStatus });
  log("editor_demo", "accepted_suggestion", {
    article_id: articleId,
    suggestion_id,
    candidate_id: s.candidate_id,
    original_text: s.anchor.original_text,
    suggested_text: s.edited_text ?? s.suggested_text,
    rules: s.rule_ids,
  });
}

export function rejectSuggestion(articleId: string, suggestion_id: string) {
  const s = getSuggestions(articleId).find((x) => x.suggestion_id === suggestion_id);
  if (!s) return;
  updateSuggestion(articleId, suggestion_id, { status: "rejected" as SuggestionStatus });
  log("editor_demo", "rejected_suggestion", {
    article_id: articleId,
    suggestion_id,
    original_text: s.anchor.original_text,
    suggested_text: s.suggested_text,
    rules: s.rule_ids,
  });
}

export function editSuggestion(articleId: string, suggestion_id: string, edited_text: string) {
  updateSuggestion(articleId, suggestion_id, {
    edited_text,
    status: "edited_by_human" as SuggestionStatus,
  });
  log("editor_demo", "edited_suggestion", {
    article_id: articleId,
    suggestion_id,
    suggested_text: edited_text,
  });
}

export function commentSuggestion(articleId: string, suggestion_id: string, note: string) {
  updateSuggestion(articleId, suggestion_id, { editor_note: note });
  log("editor_demo", "commented_suggestion", {
    article_id: articleId,
    suggestion_id,
    note,
  });
}