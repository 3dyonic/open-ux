# Scope examples

Each example is a **scope shape** the MCP wire supports. **`Open-UX:pack`** requires **`jobs=`** or **`guideline_ids=`**. Optional: **`open-ux rank-pack`** on one page after a pack tool response (`pip install open-ux`): LLM local reorder only.

| Scope | Satisfy with | Envelope | When to use |
| --- | --- | --- | --- |
| **Container** | `jobs=forms` · `jobs=actions` · `jobs=feedback` (or full container id) | **`cite_via` only:** no **`situation`** | Broad pass over every Card in that kind of work |
| **Card** | `jobs=<card_id>` | **`situation`** + **`reject`** | One compose job; map with **`get_situation`** first (leaf counts, Card **`component[]`**) |
| **Leaf** | `jobs=<leaf_id>` | **`situation`** + **`leaf`** + **`reject`** | One bay on a Card: narrowest **`jobs=`** |
| **Cite ids** | `guideline_ids=[id, …]` when the id is known and **`jobs=`** is not | **`cite_via` only** | Minor update: prefer **`jobs=`** when you can name the Card or Leaf |
| **Single cite** | skip pack | n/a | **`get_guideline`** only: one body in hand |

**Container: broad forms pass.** `Open-UX:pack` with `jobs=forms` (`forms_and_input`). No Card **`reject`** envelope. Loop **`next_offset`**. Narrow **`jobs=`** to a Card when the ask sharpens.

**Card: signup / settings fields.** `Open-UX:get_situation` `design_a_form` → `Open-UX:pack` with `jobs=design_a_form`. Read envelope **`reject`**, row fit, loop **`next_offset`**, **`get_guideline`** on one id, back to the page.

**Card: delete confirm with danger button.** `Open-UX:pack` with `jobs=protect_destructive_and_leave`. Rows may stamp **`component: ["button"]`**. **`get_guideline`** for discard/confirm cites; **`Open-UX:get_component`** `button` for variant context: back to the pack between hops.

**Leaf: cancel link vs button.** Map counts on `design_a_form`, then `Open-UX:pack` with `jobs=choose_control_for_choice`: not `jobs=pick_primary_action` (loudness bay on another Card).

**Leaf: primary vs secondary styling.** `Open-UX:pack` with `jobs=pick_primary_action` (`design_actions_and_ctas`).

**Leaf: danger button in delete dialog only.** `Open-UX:pack` with `jobs=disable_or_confirm_destructive`: not `jobs=protect_destructive_and_leave` when the ask is only confirm / disable.

**Leaf: unsaved leave warning.** `Open-UX:pack` with `jobs=warn_before_leave`. **`get_guideline`** for leave-warn cites; **`Open-UX:get_component`** when button vs modal wording matters.

**Cite ids: one known rule (no Card yet).** `Open-UX:pack` with `guideline_ids=[…]`. Prefer `jobs=design_a_form` once you know the Card.

**Single cite: minor wording fix.** **`Open-UX:get_guideline`** on the id: no **`jobs=`** when the task is already one cite.

**No `jobs=` yet: vague checkout.** **`Open-UX:suggest_situations`** → pick a Card → **`get_situation`** → satisfy **`jobs=`** (`jobs=build_a_multi_step_flow` or a Leaf). More than one Card → separate packs, each with its own **`jobs=`**.

**Reorder one page (optional, LLM local).** Save the **`Open-UX:pack`** JSON, then `open-ux rank-pack --query "danger button" < pack.json`.
