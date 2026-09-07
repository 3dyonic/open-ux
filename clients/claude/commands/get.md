---
description: Fetch one Open UX Situation Card or one guideline by id.
---

Call a get tool. Decide from `$ARGUMENTS`:

- Card id (compose job) → `Open-UX:get_situation`. Returns when / reject / facets / pointers. Not rule bodies.
- Guideline id → `Open-UX:get_guideline`. Returns the cited body for that id.

If `$ARGUMENTS` is empty, ask which Card or guideline id. Do not ask for a file. Do not invent an id. Surfaces (`home`, `cart`, `checkout`) are not ids — decompose or use `Open-UX:suggest_situations`.
