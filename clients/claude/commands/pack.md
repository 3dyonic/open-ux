---
description: Fetch a cited criteria pack for a Situation Card. The decision is yours.
---

Map first: `Open-UX:get_situation` (leaf `{ id, count }`). Then `Open-UX:pack` with `jobs=` card or leaf / `guideline_ids`.
Card/Leaf pulls: envelope `situation` (`reject`; `leaf` when scoped), `cite_via` → `get_guideline`. Rows: `overview`, `apply_when`, `not_when`, `component`.
Deep read: `get_guideline` (rule) or `get_component` (widget shape). Back to pack; loop `next_offset`.
Helpers `helpers/pack.py`, `helpers/rank_pack.py` ([`helpers/registry.json`](../../../helpers/registry.json)) available. Example: `/pack design_a_form`. No file. Host does not pass or fail.
