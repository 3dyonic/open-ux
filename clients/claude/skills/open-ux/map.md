# Map

Fallback **inside** the `open-ux` skill. Not a second skill package.

Use when the ask is a **surface** (`home`, `cart`, `checkout`) or pasted UI with no compose job named.

1. Call `Open-UX:suggest_situations` with `task_text`. Optional `surface` is ranking bias only — never a catalog id.
2. Pick one returned Card. Surfaces are not ids.
3. Continue the compose path: `Open-UX:get_situation` → `Open-UX:audit` with `jobs=<card_id>`.

If suggest returns empty, say so. Do not invent a Card. Do not start map when the user already named a Card or a clear compose job.
