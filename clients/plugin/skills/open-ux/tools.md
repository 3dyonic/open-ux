# Tools

Fully qualified `Open-UX:*` names. List, get, pack, map, and cite all stay on **MCP tools** — there are no separate slash commands. You compare Cards from [cards.md](cards.md). No winner from the host.

## By verb (9 tools)

| Verb | Tools | Shape |
| --- | --- | --- |
| List | `list_situations`, `list_guidelines`, `list_components` | Browse index, no rule bodies |
| Get | `get_situation`, `get_guideline`, `get_component` | One thing, full body, by id |
| Pull | `pack`, `suggest_situations`, `search_guidelines` | Multi-row, cited, paged |

Every tool name signals its verb. A new tool should fit one of the three or it does not belong on the wire.

## MCP (agent path)

The host fetches and serves catalog data. Use tools; do not substitute helpers or CLI.

- `Open-UX:get_situation`: Card when / reject / facets / **`leaves: { id, count }`** / merged pointers / `component[]` (not rule bodies)
- `Open-UX:pack`: `jobs=<card_id>` or `jobs=<leaf_id>` or `guideline_ids`. Card/Leaf pulls: **`situation`** + **`cite_via`**. Read reject and row fit (`apply_when` / `not_when`). Loop `next_offset`. Row `id` → `get_guideline`; row **`component[]`** → `get_component` as control context for that job. The decision is yours. Host **ignores** `query`.
- `Open-UX:list_situations`: Card index; with `container=` that kind's specs (`when` / `reject`)
- `Open-UX:suggest_situations`: catalog map (lock order overviews). Vague surface or pasted UI. Does not pick a Card.
- `Open-UX:get_guideline` / `Open-UX:search_guidelines` / `Open-UX:list_guidelines`: cite. Full-record fields: [guideline.md](guideline.md).
- `Open-UX:list_components` / `Open-UX:get_component`: context helper for Cards and jobs (`catalog/components/`). Open for ids on a pack row or Card: not instead of `pack`. Full-record fields: [component.md](component.md).

Empty shelf → say so. We are a catalog. They choose what to take. Cited criteria help you decide; the decision is yours. We don't return pass or fail.

## LLM helper (optional, local)

**`pip install open-ux`** ships all helpers as **`open-ux`** subcommands: **`open-ux helpers list`**. Details: [`helpers/README.md`](../../../../helpers/README.md). Do not invent these.

Agent helper (LLM local, after **`Open-UX:pack`**):

- `open-ux rank-pack --query "…" < pack.json`: BM25 over one page. Fail open. No winner.

Never use `rank_pack` to fetch a pack, pick a Card, or replace the skill loop.

## Contributor wire (not skill path)

Also on pip (terminal / CI only: not agent path when MCP is connected): `open-ux pack`, `open-ux component`, `open-ux tools list`. See **`contributor_wire`** in **`open-ux helpers list`**.

Contributor scripts live in `scripts/`: not for agents.

## API ergonomics

These disciplines keep the catalog scalable while the tool count stays at nine:

- **One scoping parameter, three sizes.** `jobs=` takes a container, Card, or Leaf id; the envelope grows with it. A graduated parameter beats parallel entry points for the same concept.
- **Map before you pull.** `get_situation` (ids + counts) precedes `pack` (bodies), so you know roughly how much sits behind a scope before choosing how narrow to go.
- **`reject` travels with `situation`.** Steering away from adjacent Cards rides in the same payload as steering toward one — not a second call.
- **Ranking stays off the server.** `query` on `pack` / `search_guidelines` is non-authoritative; reorder one fetched page with optional local `open-ux rank-pack` only.
- **`component[]` is stamped, not enumerated.** Open `get_component` only when a row or Card names the id. See [component.md](component.md).
- **One registered skill.** New capability → new `jobs=` value or a new row in a reference file the skill already points to — not a new registered entry. Decision tree → [principles.md](principles.md).
