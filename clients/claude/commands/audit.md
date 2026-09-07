---
description: Fetch cited UX criteria for a Card or guideline ids. Always scoped. No file. No pass or fail from the host.
---

Call `Open-UX:audit` with a need. Never call it empty.

- Card: `jobs=<card_id>` (or container alias `forms` / `actions` / `feedback`).
- Known ids: `guideline_ids`.

`$ARGUMENTS` is the Card id, container alias, or a list of guideline ids. Optional query/limit if the user named them.

Do not send a file, markup, or a scan payload. Do not return pass or fail. Narrate the criteria pack (`id`, title, name, and the returned criteria). The caller applies it to work already in hand.

If the pack is empty, say so. Do not invent rules.
