# Agent tools

Fully qualified on the wire: `Open-UX:<name>`. There is **no** `audit` tool — use **`pack`**.

## Situation map

**`suggest_situations`** — Takes `task_text` (what you are composing) and returns the full catalog map of all 13 Situation Cards, grouped by container. Does not pick one for you, does not rank — just the map.

**`list_situations`** — Lists Situation Cards, optionally filtered by `container`. Unscoped, it is the full index. No rule bodies — card metadata only (id, title, container; with `container=`, when / reject specs).

**`get_situation`** — Fetches one Situation Card by id: when / reject criteria and facets (`leaves: [{ id, count }]`). Fails if you pass a Leaf id instead of a Card id. No rule text.

## Criteria

**`pack`** — Returns cited rule criteria for a job. Takes `jobs` (Card, Leaf, or container id) or `guideline_ids`, plus `limit` / `offset` to page (`next_offset`). Host **ignores** `query` — use **`open-ux rank-pack`** locally ([`helpers/registry.json`](../helpers/registry.json)) to reorder one page. Does not take a file, does not return pass/fail — hands back relevant rules to check your own work against.

**`get_guideline`** — Fetches one full guideline body by id when you already know which rule you want. Primary deep read after **`pack`**.

When the row or Card stamps **`component[]`**, **`get_component`** is a context helper for that job — control shape (variants, a11y, keyboard) while you stay on the cite pull.

## Index and search

**`list_guidelines`** — Paged catalog index (id, title, jobs, lane, placement). No rule bodies.

**`search_guidelines`** — Scope the index by `jobs` / `lane`. Host ignores `query`. No rule bodies.

## Components

Context helper for Cards and **`jobs=`** pulls — not a second catalog map. Records in `catalog/components/` — variants, accessibility, and keyboard. **`button.json`** is the exemplar. Cards and cites stamp **`component[]`**; **`pack`** rows echo those ids.

**`list_components`** — Component index (id, title, overview). No variant bodies.

**`get_component`** — One component record by `id`. Section switches (default on unless noted): `include_vs`, `include_variants`, `include_accessibility`, `include_keyboard`; opt-in: `include_keywords`, `include_used_on` (Cards and cites that stamp this id). False omits the key. Open when **`component[]`** on the Card or pack row names the id. Full fields: [`component.md`](../clients/claude/skills/open-ux/component.md).

## LLM helper (agent, local)

After **`pack`** returns a page, the model may run **`open-ux rank-pack`** locally (`pip install open-ux` on the machine) to reorder rows — host does not rank. See [`helpers/registry.json`](../helpers/registry.json) → `agent_helpers`. Plugin + key alone do not ship the CLI; one local pip install is enough. Not a substitute for MCP tools.

## Contributor CLI (not agent path)

Same wire as MCP for terminal/CI: `open-ux pack`, `open-ux cite`, `open-ux component`, `open-ux components`. Listed under `contributor_wire` in [`helpers/registry.json`](../helpers/registry.json). Agents use **`Open-UX:*` tools**. Local stdio: [`clients/claude/mcp.stdio.json`](../clients/claude/mcp.stdio.json).
