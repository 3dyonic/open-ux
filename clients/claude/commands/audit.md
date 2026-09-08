---
description: Fetch cited UX criteria for a Situation Card. The decision is yours.
---

Call `Open-UX:audit` with `jobs=` / `guideline_ids`. Follow `next_offset` until it is absent. A helper `python3 scripts/audit.py --jobs <card_id>` is available if useful. Example: `/audit design_a_form`. Do not send a file. The host does not pass or fail.
