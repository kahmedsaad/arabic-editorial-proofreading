# Handoff mailbox (ChatGPT ↔ Cursor)

ChatGPT and Cursor **cannot** talk directly. Use these files as the bridge.

## Files

| File | Who writes | Who reads |
|------|------------|-----------|
| `from_chatgpt.md` | You / ChatGPT | Cursor Auto |
| `to_chatgpt.md` | Cursor Auto | You → paste into ChatGPT |
| `CONTEXT.md` | Either (keep short) | Both |

## Workflow

1. In ChatGPT: ask for a Cursor prompt for your next goal.
2. Paste that prompt into `from_chatgpt.md` (replace contents).
3. In Cursor: say **“read handoff/from_chatgpt.md and do it”**.
4. When Cursor finishes, open `to_chatgpt.md` and paste it into ChatGPT.

## Rules

- One task at a time in `from_chatgpt.md`
- Do not put secrets (API keys, passwords) here
- Keep `CONTEXT.md` as the short project truth; don’t duplicate huge docs
