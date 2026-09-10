# Agent tools

Fully qualified on the wire: `Open-UX:<name>`. Criteria pull: **`pack`**. Full list below.

## Situation map

**`suggest_situations`:** Takes `task_text` (what you are composing) and returns the full catalog map of all 13 Situation Cards, grouped by container. Does not pick one for you, does not rank: just the map. Next: compare jobs with **`list_situations(container=…)`** or **`get_situation`**, then **`pack`** with `jobs=<card_id>`, `jobs=<leaf_id>`, or `jobs=<container>` for a broad pass (no **`situation`** envelope).

**`list_situations`:** Lists Situation Cards, optionally filtered by `container`. Unscoped, it is the full index (no when/reject). With `container=`, returns when/reject specs. No rule bodies. Response **`note`** points to the next step (`suggest_situations` for a vague ask; `get_situation` then **`pack`** when a job is named).

**`get_situation`:** Fetches one Situation Card by id: when / reject criteria and facets (`leaves: [{ id, count }]`). Fails if you pass a Leaf id instead of a Card id. No rule text.

## Criteria

**`pack`:** Returns cited rule criteria for a job. Takes `jobs` (Card, Leaf, or container id) or `guideline_ids`, plus `limit` / `offset` to page (`next_offset`). Card/Leaf pulls include **`situation`** (when, reject). Container pulls are a broad pass: **`cite_via` only**, no **`situation`** — narrow to a Card when the ask sharpens. Host **ignores** `query`: use **`open-ux rank-pack`** locally ([`helpers/registry.json`](../helpers/registry.json)) to reorder one page. Does not take a file, does not return pass/fail: hands back relevant rules to check your own work against.

**`get_guideline`:** Fetches one full guideline body by id when you already know which rule you want. Primary deep read after **`pack`**.

When the row or Card stamps **`component[]`**, **`get_component`** is a context helper for that job: control shape (variants, a11y, keyboard) while you stay on the cite pull.

## Index and search

**`list_guidelines`:** Paged catalog index (id, title, jobs, lane, placement). No rule bodies.

**`search_guidelines`:** Scope the index by `jobs` / `lane`. Host ignores `query`. No rule bodies.

## Components

Context helper for Cards and **`jobs=`** pulls: not a second catalog map. Records in `catalog/components/`: variants, accessibility, and keyboard. **`button.json`** is the exemplar. Cards and cites stamp **`component[]`**; **`pack`** rows echo those ids.

**`list_components`:** Component index (id, title, overview). No variant bodies.

**`get_component`:** One component record by `id`. Section switches (default on unless noted): `include_vs`, `include_variants`, `include_accessibility`, `include_keyboard`; opt-in: `include_keywords`, `include_used_on` (Cards and cites that stamp this id). False omits the key. Open when **`component[]`** on the Card or pack row names the id. Full fields: [`component.md`](../clients/plugin/skills/open-ux/component.md).

## LLM helper (agent, local)

**`pip install open-ux`** ships all helpers as **`open-ux`** subcommands: list with **`open-ux helpers list`**. See [`helpers/README.md`](../helpers/README.md). After **`pack`**, the model may run **`open-ux rank-pack`** locally to reorder one page (host does not rank). Not a substitute for MCP tools. Plugin + key alone do not install helpers.

## Contributor CLI (same pip package, not agent path)

Terminal/CI: `open-ux pack`, `open-ux cite`, `open-ux component`, `open-ux components`, `open-ux tools`. Agents with MCP connected use **`Open-UX:*` tools**. Local stdio: [`clients/plugin/mcp.stdio.json`](../clients/plugin/mcp.stdio.json).
