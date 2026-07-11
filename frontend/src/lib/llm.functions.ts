import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

// Live LLM phase call. The user's API key is sent per-request from the
// browser and never persisted on the server. We just forward the prompt
// to an OpenAI-compatible chat-completions endpoint and return parsed JSON.

const Input = z.object({
  baseUrl: z.string().url(),
  apiKey: z.string().min(8),
  model: z.string().min(1),
  system: z.string(),
  user: z.string(),
  temperature: z.number().min(0).max(1).optional(),
});

export const callLlmPhase = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) => Input.parse(input))
  .handler(async ({ data }) => {
    const url = data.baseUrl.replace(/\/$/, "") + "/chat/completions";
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${data.apiKey}`,
      },
      body: JSON.stringify({
        model: data.model,
        messages: [
          { role: "system", content: data.system },
          { role: "user", content: data.user },
        ],
        response_format: { type: "json_object" },
        temperature: data.temperature ?? 0,
      }),
    });
    if (!res.ok) {
      const text = await res.text();
      return { ok: false as const, status: res.status, error: text.slice(0, 500) };
    }
    const body = (await res.json()) as { choices?: Array<{ message?: { content?: string } }> };
    const content = body.choices?.[0]?.message?.content ?? "{}";
    // Always return the raw content. The caller decides how strict to be
    // about JSON parsing — we don't want a malformed-but-useful response
    // to halt the entire pipeline.
    let parseOk = true;
    try { JSON.parse(content); } catch { parseOk = false; }
    return { ok: true as const, json: content, parseOk };
  });