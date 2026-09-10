# Tools

Fully qualified `Open-UX:*` names. `/list` `/get` `/pack` / map / cite stay on **MCP tools**. You compare Cards from [cards.md](cards.md). No winner from the host.

## MCP (agent path)

The host fetches and serves catalog data. Use tools — do not substitute helpers or CLI.

- `Open-UX:get_situation` — Card when / reject / facets / **`leaves: { id, count }`** / merged pointers / `component[]` (not rule bodies)
- `Open-UX:pack` — `jobs=<card_id>` or `jobs=<leaf_id>` or `guideline_ids`. Card/Leaf pulls: **`situation`** + **`cite_via`**. Read reject and row fit (`apply_when` / `not_when`). Loop `next_offset`. Row `id` → `get_guideline`; row **`component[]`** → `get_component` as control context for that job. The decision is yours. Host **ignores** `query`.
- `Open-UX:list_situations` — Card index; with `container=` that kind's specs (`when` / `reject`)
- `Open-UX:suggest_situations` — catalog map (lock-order overviews). Vague surface or pasted UI. Does not pick a Card.
- `Open-UX:get_guideline` / `Open-UX:search_guidelines` / `Open-UX:list_guidelines` — cite. Full-record fields: [guideline.md](guideline.md).
- `Open-UX:list_components` / `Open-UX:get_component` — context helper for Cards and jobs (`catalog/components/`). Open for ids on a pack row or Card — not instead of `pack`. Full-record fields: [component.md](component.md).

Empty shelf → say so. We are a catalog. They choose what to take. Cited criteria help you decide; the decision is yours. We don't return pass or fail.

## LLM helper (optional, local)

One helper for work the host does not do. List: [`helpers/registry.json`](../../../../helpers/registry.json) → **`agent_helpers`**. Do not invent these:

- `open-ux rank-pack --query "…" < pack.json` — BM25 over one page you already got from **`Open-UX:pack`**. Requires **`pip install open-ux`** on the machine (ships with the package). Repo shim: `helpers/rank_pack.py`. Fail-open. No winner.

Never use `rank_pack` to fetch a pack, pick a Card, or replace the skill loop.

## Contributor wire (not skill path)

Terminal and CI mirrors — [helpers registry](../../../../helpers/registry.json) → **`contributor_wire`**: `open-ux pack`, `open-ux component`, `helpers/mcp_call.py`. Contributors only; agents use MCP tools above.

Contributor scripts live in `scripts/` — not for agents.
