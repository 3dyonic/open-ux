---
name: open-ux
description: >-
  Use when building or checking UI — composing or reviewing. Open UX offer:
  cited UX packs for the job you name — Open-UX:pack with jobs=<card_id>,
  jobs=<leaf_id>,
  container alias (forms, actions, feedback), or guideline_ids. Tooling:
  Open-UX:get_situation (map a Card), pack (browse cites), get_guideline (full
  rule), get_component (control context when stamped). Same wire: open-ux pack,
  helpers/pack.py, helpers/get_component.py. Sourced criteria — you decide; not
  pass or fail; do not invent from memory. Hub + references — read on demand.
  Host does not pick a Card.
---

# Open UX

Need in → cited criteria out. We are a catalog. They choose what to take. You already have the UI. We hand you a page of matching cited rules so you don't invent UX from memory. Cited criteria help you decide. The decision is yours. The host does not pick a Card.

Compose and review share this one trigger. Compare Cards that fit. Open more than one if the ask spans them. You decide what to take.

## Loop

1. **Card table** — [cards.md](cards.md): pick a Card (or compare `when` / Reject neighbors).
2. **`Open-UX:get_situation`** — map the Card: facets, merged `guideline_ids`, and **`leaves: [{ id, count }]`** (how stocked each Leaf bay is).
3. **Scope the pull** — whole Card (`jobs=<card_id>`) or one bay (`jobs=<leaf_id>`) when the ask is narrow. See [examples.md](examples.md) for container → cite scope sizes.
4. **`Open-UX:pack`** — read **`reject`** on the envelope **`situation`** (Card reject is never skipped on Card/Leaf pulls). Skim rows: **`overview`**, **`apply_when`**, **`not_when`**, **`rule`**, **`component`**. **`cite_via`** is `get_guideline` — rows are browse slices, not full cites.
5. **Deep read on a fitting row** — always come back to the pack page, `next_offset`, or another Card:
   - **`Open-UX:get_guideline`** on row **`id`** — cited rule (source, citations, `agent_hint`, full `description`). Primary.
   - **`Open-UX:get_component`** on row **`component[]`** — context helper when the id is stamped and the ask is the control (variant names, danger vs primary, hit target, a11y, keyboard), not the house. Usually after **`get_guideline`** on the same row.
6. **Loop the page** — if `next_offset` is set, call **`pack`** again with that **`offset`**.

`pack` pages at 10. The host does not rank. Do not write a pack fetcher or a BM25 ranker — see [tools.md](tools.md).

Cross-reference similar rules — same **`facet`**, **`Open-UX:search_guidelines`**, or other Cards in the table. Two sources on one Card can disagree; say both.

The catalog stays open: after a Card you can take another or call the map again.

## Route

Always loaded — match the ask, satisfy **`jobs=`**, then open references for depth.

| Ask | `jobs=` |
| --- | --- |
| Form labels / fields / control choice | `design_a_form` or Leaf `choose_control_for_choice` |
| Validation / inline errors | `handle_form_errors` |
| Primary vs secondary / small submit | `design_actions_and_ctas` or Leaf `pick_primary_action` |
| Delete confirm / unsaved leave / danger button | `protect_destructive_and_leave` or Leaf `disable_or_confirm_destructive` / `warn_before_leave` |
| Loading / spinner / 404 / failure tone | `compose_feedback` |
| Checkout / wizard / steps | `build_a_multi_step_flow` |
| Broad forms pass (no Card yet) | `forms` |

Vague surface → **`suggest_situations`** first. Full Card table and reject neighbors → [cards.md](cards.md). More ask phrasing → [ask-shapes.md](ask-shapes.md). Scope sizes → [examples.md](examples.md).

## References

One skill package. Read the reference that matches the task — do not load all upfront.

| Reference | Read when |
| --- | --- |
| [glossary.md](glossary.md) | Map, container, Card, Leaf, cite, pack, component — vocabulary |
| [ask-shapes.md](ask-shapes.md) | User language → Card / Leaf / `get_component` |
| [examples.md](examples.md) | **`jobs=`** scope sizes (container → Card → Leaf → cite) |
| [shapes.md](shapes.md) | JSON wire for map and pack responses |
| [cards.md](cards.md) | Situation Card table — when / reject |
| [guideline.md](guideline.md) | After **`get_guideline`** — full cite fields |
| [component.md](component.md) | After **`get_component`** — control record fields |
| [tools.md](tools.md) | Tool list, helpers, CLI |
| [connect.md](connect.md) | Install, stdio, hosted MCP |

Match the ask in [ask-shapes.md](ask-shapes.md) first; satisfy **`jobs=`** per [examples.md](examples.md); route Cards via [cards.md](cards.md).
