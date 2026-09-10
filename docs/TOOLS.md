# Agent tools

Fully qualified on the wire: `Open-UX:<name>`. There is **no** `audit` tool — use **`pack`**.

## Situation map

**`suggest_situations`** — Takes `task_text` (what you are composing) and returns the full catalog map of all 13 Situation Cards, grouped by container. Does not pick one for you, does not rank — just the map.

**`list_situations`** — Lists Situation Cards, optionally filtered by `container`. Unscoped, it is the full index. No rule bodies — card metadata only (id, title, container; with `container=`, when / reject specs).

**`get_situation`** — Fetches one Situation Card by id: when / reject criteria and facets (`leaves: [{ id, count }]`). Fails if you pass a Leaf id instead of a Card id. No rule text.

## Criteria

**`pack`** — Returns cited rule criteria for a job. Takes `jobs` (Card, Leaf, or container id) or `guideline_ids`, plus `limit` / `offset` to page (`next_offset`). Host **ignores** `query` — use `helpers/rank_pack.py` locally ([`helpers/registry.json`](../helpers/registry.json)) to reorder one page. Does not take a file, does not return pass/fail — hands back relevant rules to check your own work against.

**`get_guideline`** — Fetches one full guideline body by id when you already know which rule you want.

## Index and search

**`list_guidelines`** — Paged catalog index (id, title, jobs, lane, placement). No rule bodies.

**`search_guidelines`** — Scope the index by `jobs` / `lane`. Host ignores `query`. No rule bodies.

## Widgets

**`list_components`** / **`get_component`** — Widget index and record; optional `used_on` reverse index. Open `get_component` only for ids on a pack row or Card.
