---
name: pack
description: Fetch a cited criteria pack for a Situation Card. The decision is yours.
---

Map first: `Open-UX:get_situation` (leaf `{ id, count }`). Then `Open-UX:pack` with `jobs=` card or leaf / `guideline_ids`.
Card/Leaf pulls: envelope `situation` (`reject`; `leaf` when scoped), `cite_via` → `get_guideline`. Rows: `overview`, `apply_when`, `not_when`, `component`.
Deep read: `get_guideline`; `get_component` for control context when row `component[]` fits. Back to pack; loop `next_offset`.
Optional LLM-local reorder: `open-ux rank-pack` after pack (`pip install open-ux`; [`helpers/registry.json`](../../../helpers/registry.json)). Example: `/pack design_a_form`. No file. Host does not pass or fail.
