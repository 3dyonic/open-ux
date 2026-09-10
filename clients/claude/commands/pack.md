---
description: Fetch a cited criteria pack for a Situation Card. The decision is yours.
---

Call `Open-UX:pack` with `jobs=` / `guideline_ids`. Browse a page of 10. Start from `overview` and `apply_when`. Expect pagination: if `next_offset` is set, loop. Go in and out — `get_guideline` then back to the pack. Cross-reference similar rules. Open more than one Card if useful; you decide. Helpers `python3 helpers/pack.py --jobs <card_id>` and `python3 helpers/rank_pack.py` ([`helpers/registry.json`](../../../helpers/registry.json)) are available if useful. Do not invent a ranker. Example: `/pack design_a_form`. Do not send a file. The host does not pass or fail.
