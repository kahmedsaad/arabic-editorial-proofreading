import { useEffect, useRef, useState } from "react";
import { SEED_PHASES, ENTITIES, LEXICAL, RULES, GOLDEN } from "@/data/seed";
import { findArticle } from "@/lib/articles";
import { SYSTEM_PROMPTS, buildUserPrompt } from "./prompts";
import type { PhaseRecord } from "@/lib/types";
import { getApiKey, getState, log, setSuggestions } from "@/lib/store";
import { callLlmPhase } from "@/lib/llm.functions";
import { extractJson } from "./json";
import { createMvpReview, findingsToSuggestions, type MvpReviewResponse } from "@/lib/api/mvp";

export type RunStatus = "idle" | "running" | "done" | "error";

export interface PhaseRun extends PhaseRecord {
  status: "pending" | "running" | "complete" | "error";
  error?: string;
  raw?: string;
  started_at?: string;
  finished_at?: string;
}

const ORDER = SEED_PHASES.map((p) => p.phase);

function withStatus(): PhaseRun[] {
  return SEED_PHASES.map((p) => ({ ...p, status: "pending" }));
}

function payloadFor(phase: string, article: ReturnType<typeof findArticle>) {
  if (!article) return {};
  const base = {
    article_id: article.article_id,
    title: article.title,
    content_type: article.content_type,
    sections: article.sections,
  };
  switch (phase) {
    case "entity_extraction":
      return {
        ...base,
        entities: ENTITIES.map((e) => ({
          entity_id: e.entity_id,
          approved_ar: e.approved_ar,
          aliases: e.aliases,
        })),
      };
    case "lexical_election":
      return {
        ...base,
        lexical_fields: LEXICAL.map((l) => ({
          lex_id: l.lex_id,
          canonical: l.canonical,
          field: l.field,
          forms: l.forms,
          semantic_neighbors: l.semantic_neighbors,
        })),
      };
    case "article_graph":
      return {
        article: base,
        entities: ENTITIES.slice(0, 30).map((e) => ({
          entity_id: e.entity_id,
          approved_ar: e.approved_ar,
        })),
        active_rules: RULES.map((r) => ({ rule_id: r.rule_id, area: r.area })),
        golden: GOLDEN.map((g) => ({ gold_id: g.gold_id, span_text: g.span_text })),
      };
    case "semantic_search":
      return {
        article: base,
        lexical_fields: LEXICAL.map((l) => ({
          field: l.field,
          neighbors: l.semantic_neighbors,
          example: l.example,
        })),
      };
    case "llm_final_judgment":
      return { article: base, rules: RULES, golden: GOLDEN };
    default:
      return base;
  }
}

export function usePipeline(articleId: string) {
  const [status, setStatus] = useState<RunStatus>("idle");
  const [phases, setPhases] = useState<PhaseRun[]>(withStatus());
  const [lastReview, setLastReview] = useState<MvpReviewResponse | null>(null);
  const cancelled = useRef(false);

  useEffect(() => () => {
    cancelled.current = true;
  }, []);

  async function runPhase(i: number): Promise<"complete" | "error"> {
    const article = findArticle(articleId);
    if (!article) return "error";
    const base = SEED_PHASES[i];
    const mode = getState().mode;
    const t0 = new Date().toISOString();
    setPhases((prev) =>
      prev.map((p, idx) =>
        idx === i ? { ...p, status: "running", started_at: t0, error: undefined, raw: undefined } : p,
      ),
    );

    let output: unknown = base.output;
    let source: PhaseRecord["source"] = "mock";
    let raw: string | undefined;
    let error: string | undefined;

    try {
      if (mode === "live" && SYSTEM_PROMPTS[base.phase]) {
        const { liveSettings } = getState();
        const apiKey = getApiKey();
        if (!apiKey) throw new Error("Live Mode is on but no API key is set in Settings.");
        const system = SYSTEM_PROMPTS[base.phase];
        const user = buildUserPrompt(base.phase, payloadFor(base.phase, article));
        const result = await callLlmPhase({
          data: {
            baseUrl: liveSettings.baseUrl,
            apiKey,
            model: liveSettings.model,
            system,
            user,
          },
        });
        if (!result.ok) {
          error = `LLM error ${result.status}: ${result.error}`;
        } else {
          raw = result.json;
          const parsed = extractJson(result.json);
          if (parsed.ok) {
            output = parsed.value;
            source = "llm-simulated";
          } else {
            output = { raw: result.json, parse_error: parsed.error };
            source = "llm-simulated";
            error = `JSON parse failed: ${parsed.error}`;
          }
        }
      } else {
        await new Promise((r) => setTimeout(r, 220));
      }
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    }

    if (cancelled.current) return "error";
    const t1 = new Date().toISOString();
    const finalStatus: PhaseRun["status"] = error ? "error" : "complete";
    setPhases((prev) =>
      prev.map((p, idx) =>
        idx === i ? { ...p, status: finalStatus, output, source, raw, error, finished_at: t1 } : p,
      ),
    );
    log("system", error ? "phase_error" : "phase_complete", {
      article_id: articleId,
      note: `${base.phase}${error ? `: ${error}` : ` (${source})`}`,
    });
    return finalStatus;
  }

  async function runMvpEngine(): Promise<"complete" | "error"> {
    const article = findArticle(articleId);
    if (!article) return "error";
    const { liveSettings } = getState();
    const t0 = new Date().toISOString();

    // Collapse UI phases into one MVP engine call for clarity.
    setPhases((prev) =>
      prev.map((p) => ({
        ...p,
        status: "running",
        started_at: t0,
        error: undefined,
        raw: undefined,
        source: "repository-driven" as const,
      })),
    );

    try {
      const review = await createMvpReview(article, liveSettings.baseUrl);
      if (cancelled.current) return "error";
      setLastReview(review);
      const suggestions = findingsToSuggestions(article, review.findings, review.review_id);
      setSuggestions(articleId, suggestions);
      const t1 = new Date().toISOString();
      const summary = {
        review_id: review.review_id,
        findings: review.findings.length,
        rejected: review.rejected_findings.length,
        mechanical: review.mechanical_finding_count,
        ai: review.ai_finding_count,
      };
      setPhases((prev) =>
        prev.map((p) => ({
          ...p,
          status: "complete",
          finished_at: t1,
          source: "repository-driven",
          output: summary,
          raw: JSON.stringify(summary, null, 2),
        })),
      );
      log("system", "mvp_review_complete", {
        article_id: articleId,
        note: `review=${review.review_id} findings=${suggestions.length}`,
      });
      return "complete";
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const t1 = new Date().toISOString();
      setPhases((prev) =>
        prev.map((p) => ({
          ...p,
          status: "error",
          finished_at: t1,
          error: message,
        })),
      );
      log("system", "mvp_review_error", { article_id: articleId, note: message });
      return "error";
    }
  }

  async function run() {
    cancelled.current = false;
    setStatus("running");
    setPhases(withStatus());
    const article = findArticle(articleId);
    if (!article) {
      setStatus("error");
      return;
    }
    const mode = getState().mode;
    const useMvp = getState().liveSettings.useMvpEngine !== false;
    log("system", "pipeline_start", {
      article_id: articleId,
      note: `mode=${mode} mvp=${useMvp}`,
    });

    if (mode === "live" && useMvp) {
      const res = await runMvpEngine();
      setStatus(res === "error" ? "error" : "done");
      log("system", "pipeline_complete", {
        article_id: articleId,
        note: res === "error" ? "mvp error" : "mvp ok",
      });
      return;
    }

    let anyError = false;
    for (let i = 0; i < ORDER.length; i++) {
      if (cancelled.current) return;
      const res = await runPhase(i);
      if (res === "error") anyError = true;
    }
    setStatus(anyError ? "error" : "done");
    log("system", "pipeline_complete", {
      article_id: articleId,
      note: anyError ? "with errors" : "ok",
    });
  }

  function reset() {
    cancelled.current = true;
    setStatus("idle");
    setPhases(withStatus());
    setLastReview(null);
  }

  return { status, phases, run, runPhase, reset, lastReview };
}
