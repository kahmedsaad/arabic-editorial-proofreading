// Best-effort JSON extraction from an LLM response. Returns either
// { ok: true, value } or { ok: false, raw, error } so callers can show
// the raw text instead of crashing the pipeline.
export type ExtractResult =
  | { ok: true; value: unknown }
  | { ok: false; raw: string; error: string };

export function extractJson(input: string): ExtractResult {
  if (typeof input !== "string") {
    return { ok: false, raw: String(input), error: "non-string response" };
  }
  let cleaned = input
    .replace(/```json\s*/gi, "")
    .replace(/```\s*/g, "")
    .trim();
  const start = cleaned.search(/[\{\[]/);
  if (start !== -1) {
    const openCh = cleaned[start];
    const closeCh = openCh === "[" ? "]" : "}";
    const end = cleaned.lastIndexOf(closeCh);
    if (end > start) cleaned = cleaned.substring(start, end + 1);
  }
  try {
    return { ok: true, value: JSON.parse(cleaned) };
  } catch (e1) {
    const repaired = cleaned
      .replace(/,\s*}/g, "}")
      .replace(/,\s*]/g, "]")
      // eslint-disable-next-line no-control-regex
      .replace(/[\x00-\x1F\x7F]/g, "");
    try {
      return { ok: true, value: JSON.parse(repaired) };
    } catch (e2) {
      const msg = e2 instanceof Error ? e2.message : String(e2);
      return { ok: false, raw: input, error: msg };
    }
  }
}