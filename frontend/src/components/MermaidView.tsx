import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

let initialized = false;
function ensureInit() {
  if (initialized) return;
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "loose",
    theme: "neutral",
    fontFamily: "inherit",
    flowchart: { htmlLabels: true, curve: "basis" },
  });
  initialized = true;
}

interface Props {
  source: string;
  /** Used as the SVG element id so multiple diagrams can co-exist. */
  id?: string;
}

export function MermaidView({ source, id }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    ensureInit();
    const renderId = "m_" + (id ?? Math.random().toString(36).slice(2, 9));
    (async () => {
      try {
        const { svg } = await mermaid.render(renderId, source.trim());
        if (!cancelled && ref.current) {
          ref.current.innerHTML = svg;
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          if (ref.current) ref.current.innerHTML = "";
        }
      }
    })();
    return () => { cancelled = true; };
  }, [source, id]);

  return (
    <div className="w-full">
      <div ref={ref} className="mermaid-host overflow-x-auto bg-white dark:bg-zinc-900 rounded-md p-3 border" dir="ltr" />
      {error && (
        <p className="text-xs text-red-600 mt-2" dir="ltr">Mermaid error: {error}</p>
      )}
    </div>
  );
}