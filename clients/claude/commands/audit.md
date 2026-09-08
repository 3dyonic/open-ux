---
description: Fetch cited UX criteria for a Situation Card. The decision is yours.
---

Call `Open-UX:audit` with `jobs=` / `guideline_ids`. Browse a page of 10. Start from `overview`. Expect pagination: if `next_offset` is set, loop. Go in and out — `get_guideline` then back to the shelf. Cross-reference similar rules. A helper `python3 scripts/audit.py --jobs <card_id>` is available if useful. Example: `/audit design_a_form`. Do not send a file. The host does not pass or fail.
