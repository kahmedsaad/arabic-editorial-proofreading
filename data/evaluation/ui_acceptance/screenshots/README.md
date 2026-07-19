# UI acceptance screenshots — v1

The Chrome MCP (Chrome DevTools) server used for this test runs in a sandbox whose
configured workspace roots do **not** include this repository. Every attempt to save a
screenshot to a file path (workspace-relative and absolute, including this
`screenshots/` directory) was rejected with:

```
Access denied: path <...> is not within any of the configured workspace roots.
```

Because of this, the required screenshots could not be written to disk from the MCP
server. They were captured **inline** (viewport PNGs) in the agent transcript at the
moments listed below and serve as the visual evidence for this run.

## Captured screenshots (inline in transcript)

| Intended filename | Case | Review id | What it shows |
|-------------------|------|-----------|----------------|
| `E01_form.png` | E01 (first case) | custom-mrrg6m8v | Filled `/new-article` form: live + MVP engine badges, headline `افتتاح المكتبة الجديدة`, lead body with `افتتح البلدية`. |
| `M01_review.png` | M01 (medium) | custom-mrrgemjk | Review result: candidates 2 → final findings 0. |
| `D01_review.png` | D01 (difficult) | custom-mrrgmk4a | Review result: "التحقق والتصحيح — مرفوض بعد التحقق: 1 · النتائج النهائية: 0" (validator rejecting a detected contradiction). |
| `E06_review.png` | E06 (clean control) | custom-mrrgdewp | Review result: 0 candidates, 0 findings, no punctuation FP. |
| `D07_review.png` | D07 (clean control) | custom-mrrgu6sq | Review result: 0 candidates, 0 findings (correct 25% figure not flagged). |

No UI errors, timeouts, or authentication failures occurred during the run, so no
error screenshots were required.
