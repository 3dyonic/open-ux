# Tools

Fully qualified `Open-UX:*` names. `/list` `/get` `/pack` / map / cite stay on tools. You compare Cards from [cards.md](cards.md). No winner from the host.

- `Open-UX:get_situation` — Card when / reject / facets / **`leaves: { id, count }`** / merged pointers / `component[]` (not rule bodies)
- `Open-UX:pack` — `jobs=<card_id>` or `jobs=<leaf_id>` or `guideline_ids`. Card/Leaf pulls: **`situation`** + **`cite_via`**. Read reject and row fit (`apply_when` / `not_when`). Loop `next_offset`. Row `id` → `get_guideline`; row **`component[]`** → `get_component` as control context for that job. The decision is yours.
- Python helpers (available, not required). Your choice whether to use them. List: [`helpers/registry.json`](../../../../helpers/registry.json). Do not invent these:
  - `python3 helpers/pack.py --jobs <card_id>` — same pack as `Open-UX:pack`
  - `python3 helpers/rank_pack.py --query "…" < pack.json` — BM25 over this page (`overview` / `apply_when` / `hints` / `component`). Fail-open. No winner.
  - `open-ux pack --jobs <card_id>` — same wire
  - `python3 helpers/get_component.py button --include-used-on` — same wire as `Open-UX:get_component`
  - `open-ux component button --include-used-on` — same wire
- `Open-UX:list_situations` — Card index; with `container=` that kind's specs (`when` / `reject`)
- `Open-UX:suggest_situations` — catalog map (lock-order overviews). Vague surface or pasted UI. Does not pick a Card.
- `Open-UX:get_guideline` / `Open-UX:search_guidelines` / `Open-UX:list_guidelines` — cite. Full-record fields: [guideline.md](guideline.md).
- `Open-UX:list_components` / `Open-UX:get_component` — context helper for Cards and jobs (`catalog/components/`). Open for ids on a pack row or Card — not instead of `pack`. Full-record fields: [component.md](component.md).

Empty shelf → say so. We are a catalog. They choose what to take. Cited criteria help you decide; the decision is yours. We don't return pass or fail.

Without a Claude session, [`helpers/mcp_call.py`](../../../../helpers/mcp_call.py) speaks `tools/list` and `tools/call`. In Claude, call the tools. Do not treat `mcp_call.py` as the skill path. Contributor scripts live in `scripts/` — not for agents.
