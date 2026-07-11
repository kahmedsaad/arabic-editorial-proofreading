import { createFileRoute } from "@tanstack/react-router";
import { SEED_LLM_PACKET, SEED_LLM_RESPONSE } from "@/data/seed";
import { SYSTEM_PROMPTS } from "@/lib/pipeline/prompts";

export const Route = createFileRoute("/review/$articleId/llm-packet")({
  component: LlmPacketPage,
});

function LlmPacketPage() {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">حزمة سياق النموذج اللغوي</h2>
        <p className="text-xs text-muted-foreground">
          تُرسَل فقط المرشحات والقواعد النشطة والمراجعات الذهبية — لا تُرسَل القاعدة كاملة. كل ناتج يتطلب موافقة محرر.
        </p>
      </div>
      <details open>
        <summary className="cursor-pointer text-sm font-semibold">برومت النظام — final relational judgment</summary>
        <pre className="text-[11px] bg-muted/50 p-3 rounded overflow-x-auto mt-1" dir="ltr">{SYSTEM_PROMPTS.llm_final_judgment}</pre>
      </details>
      <div className="border rounded-md p-3 bg-card space-y-2">
        <h3 className="text-sm font-semibold">جميع برومتات النظام للمراحل</h3>
        {Object.entries(SYSTEM_PROMPTS).map(([phase, prompt]) => (
          <details key={phase}>
            <summary className="cursor-pointer text-xs font-mono">{phase}</summary>
            <pre className="text-[11px] bg-muted/50 p-3 rounded overflow-x-auto mt-1" dir="ltr">{prompt}</pre>
          </details>
        ))}
      </div>
      <details>
        <summary className="cursor-pointer text-sm font-semibold">الحزمة (Packet JSON)</summary>
        <pre className="text-[11px] bg-muted/50 p-3 rounded overflow-x-auto mt-1" dir="ltr">{JSON.stringify(SEED_LLM_PACKET, null, 2)}</pre>
      </details>
      <details>
        <summary className="cursor-pointer text-sm font-semibold">رد النموذج (Response JSON)</summary>
        <pre className="text-[11px] bg-muted/50 p-3 rounded overflow-x-auto mt-1" dir="ltr">{JSON.stringify(SEED_LLM_RESPONSE, null, 2)}</pre>
      </details>
    </div>
  );
}