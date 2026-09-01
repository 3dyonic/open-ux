---
name: open-ux
description: Connect to Open UX, list cited guidelines, run one audit. Use when reviewing or writing UI against shared UX rules.
---

# Open UX

cited UX rules agents audit against / shared cited guidelines

This skill does **not** contain rule bodies. The catalog is the source of truth.

## Path

1. **Connect** — hosted URL + bearer `uxmcp_` in client settings (`OPEN_UX_URL`, `OPEN_UX_API_KEY`). Self-host stdio needs no key.
2. **Key** — if hosted and unauthenticated, tell the human to request an invite on the hosted `/invite` page (landing **Get a key**). Do not invent a key.
3. **List** — call `list_guidelines`. If the catalog is empty, say so. Do not invent rules.
4. **One audit** — call `audit` with `{ target: { type: "html"|"jsx"|"description", content } }`. Narrate `verdict` + `guideline_id`. Reuse `reasons[]` (catalog `pass_when` / `fail_when` + id). Do not write house soft-copy.

If a result is `incomplete`, finish on the client using the returned `rule` / `pass_when` / `fail_when`. There is no server LLM.
