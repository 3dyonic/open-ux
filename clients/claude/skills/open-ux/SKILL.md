---
name: open-ux
description: >-
  Use when building or checking UI — composing or reviewing a form, field
  labels, input choice, validation, buttons or CTAs, delete/unsaved confirm,
  loading, 404, or error states, navigation, a table or dashboard, a modal, or a
  multi-step flow. Open UX is a cited UX catalog for agents. Open Situation
  Cards that fit; you decide which packs to take. Call Open-UX:get_situation
  and Open-UX:pack with jobs=<card_id>. Host does not pick a Card. Expect pages; loop next_offset; go in and out of a cite. Start from
  overview — short definition, the fast grab. Don't invent UX rules from memory;
  use the cited records on work already in hand. Cited criteria help
  you decide; the decision is yours. Returns citations, not pass or fail.
  home/cart/checkout are context, not ids. Use Open-UX:suggest_situations
  only if the task is a vague surface or pasted UI. Cite via
  Open-UX:search_guidelines or Open-UX:get_guideline. pip install open-ux
  (stdio, no key) or hosted (live catalog).
---

# Open UX

Need in → cited criteria out. We are a catalog. They choose what to take. You already have the UI. We hand you a page of matching cited rules so you don't invent UX from memory. Cited criteria help you decide. The decision is yours. The host does not pick a Card.

Compose and review share this one trigger. Compare Cards that fit. Open more than one if the ask spans them. You decide what to take.

## Loop

1. **Card table** — pick a Card (or compare `when` / Reject neighbors).
2. **`Open-UX:get_situation`** — map the Card: facets, merged `guideline_ids`, and **`leaves: [{ id, count }]`** (how stocked each Leaf bay is).
3. **Scope the pull** — whole Card (`jobs=<card_id>`) or one bay (`jobs=<leaf_id>`) when the ask is narrow (control choice, primary loudness, overlay layer, …).
4. **`Open-UX:pack`** — read **`reject`** on the envelope **`situation`** (Card reject is never skipped on Card/Leaf pulls). Skim rows: **`overview`**, **`apply_when`**, **`not_when`**, **`rule`**. **`cite_via`** is `get_guideline` — rows are browse slices, not full cites.
5. **`Open-UX:get_guideline`** — open one id when you need `agent_hint`, `description`, or citations — then back to the pack page, `next_offset`, or another Card.

`pack` pages at 10. If `next_offset` is set, call again with that `offset`. The host does not rank. Do not write a pack fetcher or a BM25 ranker — use the Python helpers below.

Cross-reference similar rules — same `facet`, `Open-UX:search_guidelines`, or other Cards in the table. Two sources on one Card can disagree; say both. `Open-UX:get_component` opens one widget record when `component[]` names an id.

## Shapes

**Map** (`get_situation` facet):

```json
{
  "id": "wrong_control_for_the_choice",
  "title": "Wrong control for the choice",
  "leaves": [
    { "id": "choose_control_for_choice", "count": 20 }
  ],
  "guideline_ids": ["…"]
}
```

**Pack** (Card or Leaf pull — envelope + page):

**`overview`** is the short definition — what this cite *is*. Start there. Fast confidence. Not a grade.

`pack` is a page, not the Card:

```json
{
  "situation": {
    "card": "design_a_form",
    "when": ["…"],
    "reject": [{ "id": "handle_form_errors", "why": "…" }],
    "leaf": "choose_control_for_choice"
  },
  "cite_via": "get_guideline",
  "guidelines": [{
    "id": "",
    "name": "",
    "overview": "",
    "apply_when": "",
    "not_when": "",
    "rule": "",
    "hints": [],
    "component": [],
    "leaf": "",
    "card": "",
    "facet": ""
  }],
  "count": 10,
  "total": 13,
  "offset": 0,
  "host": "citations_only",
  "next_offset": 10
}
```

Envelope **`leaf`** only when `jobs=` is a Leaf id. Container pulls (`forms` / `actions` / `feedback`) omit **`situation`**; they still set **`cite_via`**.

Read envelope **`reject`**, then row `apply_when` / `not_when`. If `next_offset` is set, loop the page. Row `id` → `get_guideline` for the full cite — then come back to the pack.

One Card is many sources. Related Cards are not a fork with a winner. That is the catalog. The host will not pick.

This is a catalog, not a judge. `host` is `citations_only`. Do not write a score as if we graded. The decision is yours.

Surfaces (`home`, `cart`, `checkout`) are context, not Cards. Container aliases `forms` / `actions` / `feedback` work as a broad first scope. The catalog stays open: after a Card you can take another or call the map again.

When you need a map of what exists — by **category**, then **source** — read [`catalog/MANIFEST.md`](../../../../catalog/MANIFEST.md). Then fetch one id.

## Examples

- **Signup / settings fields.** Card `design_a_form`. Map with `get_situation`, pack `jobs=design_a_form`, read envelope **`reject`**, loop `next_offset`, `get_guideline` for one id, back to the page. Same if you are reviewing that form.
- **Cancel as link vs button.** Leaf `choose_control_for_choice` on `design_a_form` (map counts first). Pack `jobs=choose_control_for_choice` — not `pick_primary_action` (that bay is variant loudness / implementation).
- **Primary vs secondary styling.** Leaf `pick_primary_action` on `design_actions_and_ctas`. Pack `jobs=pick_primary_action`.
- **Spinner / loading on the control.** Card `compose_feedback` — not a separate loading Leaf.
- **Review a delete confirm.** Card `protect_destructive_and_leave`. A button ask can also open `design_actions_and_ctas`. You decide.
- **Vague checkout.** `Open-UX:suggest_situations` with the task text. Read the catalog map, open the Cards that fit (`list_situations` with a container if useful), `get_situation` (leaf counts), then `pack` with `jobs=<card_id>` or a Leaf. More than one Card is fine.
- **Already have a guideline id.** `Open-UX:get_guideline` for that one cited body.
- **Delete confirm with a danger button.** Card `protect_destructive_and_leave`. Pack row stamps `component: ["button"]`. Skim cites on the pack; `Open-UX:get_component` with `id=button` for variant names (primary vs danger); back to the pack or open one cite with `get_guideline`.

## Connect

`pip install` the package, or hosted — same tools, same Cards. Package name: `open-ux`. Console script: `open-ux`.

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

Same catalog. No invite. Telemetry off. Point MCP clients at local stdio.

- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` + bearer `uxmcp_` (`OPEN_UX_API_KEY`). Request an invite at `/invite` (landing **Get a key**).

## Situation Cards

The table is the map. Compare `when`. Other Cards in Reject are neighbors to open if they fit — not a host winner. You decide.

| Container | Card | When | Reject (use this instead) |
| --- | --- | --- | --- |
| Forms & input (`forms`) | `design_a_form` | Signup, settings, or checkout *fields*; labels; placeholders; choosing a control; grouping; required marks; helper text | Validation / inline errors → `handle_form_errors`. Login / password → `compose_sign_in`. Wizard / steps → `build_a_multi_step_flow`. CTA wording → `design_actions_and_ctas`. Table / dashboard → `compose_a_data_display` |
| Forms & input (`forms`) | `handle_form_errors` | Composing validation; inline or summary errors; submit-failure messaging *on a form* | Page-level 404 / hard error / toast → `compose_feedback`. Unmarked required before submit → `design_a_form` |
| Forms & input (`forms`) | `compose_sign_in` | Login, show password, forgot-password, credential fields | Ordinary non-credential fields → `design_a_form`. Inline validation after submit → `handle_form_errors` |
| Actions & decisions (`actions`) | `design_actions_and_ctas` | Primary vs secondary; submit / continue label; toolbar; buttons too small; command panel | Delete / discard / unsaved leave → `protect_destructive_and_leave`. Field labels stay `design_a_form`. Page voice or link text → `write_the_interface`. Spinner / loading on the control → `compose_feedback` |
| Actions & decisions (`actions`) | `protect_destructive_and_leave` | Delete confirmation; discard; leave unsaved work; confirm / undo | Unclear Continue / Submit label → `design_actions_and_ctas`. Failure tone after it already fired → `compose_feedback` |
| Feedback & status (`feedback`) | `compose_feedback` | Toast after save; loading (including on the control); 404; hard error (not a field); failure tone | Inline field errors → `handle_form_errors`. Progress inside a wizard → `build_a_multi_step_flow` |
| Navigation & wayfinding | `orient_in_the_place` | Sidebar; breadcrumbs; tabs or menu; which *section* they are in; top nav | Step indicators inside a wizard → `build_a_multi_step_flow`. Search control placement → `compose_search` |
| Navigation & wayfinding | `compose_search` | Header or homepage search; search box vs link; place the search control | Site chrome / which section → `orient_in_the_place`. Link destination wording → `write_the_interface` |
| Layout & data display | `compose_a_data_display` | Table or card grid; dashboard; scannable table; chart vs table | Controls inside a form → `design_a_form`. Page scan path → `compose_the_layout`. Overlay choice → `choose_an_overlay` |
| Layout & data display | `compose_the_layout` | Page structure and headings; inverted pyramid; keep the page scannable | Table / chart / map → `compose_a_data_display`. Voice or link wording → `write_the_interface` |
| Layout & data display | `write_the_interface` | Link destination text; you/your voice; page copy that is not a button or field label | Button / command verbs → `design_actions_and_ctas`. Field labels stay `design_a_form`. Section chrome → `orient_in_the_place` |
| Overlays & content structure | `choose_an_overlay` | Modal vs accordion; tooltip vs inline help; hide advanced options; side panel | Destructive decision inside a dialog → `protect_destructive_and_leave`. Fields inside a modal → `design_a_form`. Page layout → `compose_the_layout` |
| Multi-step flows | `build_a_multi_step_flow` | Checkout *flow*; split a long form into steps; progress indicator; go back to an earlier step; change a previous answer; leave mid-flow; onboarding *sequence* | Single form on one screen → `design_a_form`. Site-level nav chrome → `orient_in_the_place`. Leave-warn as the only ask → `protect_destructive_and_leave` |

`checkout` / `home` / `cart` are not Cards.

## Tools

Fully qualified `Open-UX:*` names. `/list` `/get` `/pack` / map / cite stay on tools. You compare Cards from the table. No winner from the host.

- `Open-UX:get_situation` — Card when / reject / facets / **`leaves: { id, count }`** / merged pointers / `component[]` (not rule bodies)
- `Open-UX:pack` — `jobs=<card_id>` or `jobs=<leaf_id>` or `guideline_ids`. Card/Leaf pulls: **`situation`** + **`cite_via`**. Read reject and row fit (`apply_when` / `not_when`). Loop `next_offset`. Row `id` → `get_guideline`. The decision is yours.
- Python helpers (available, not required). Your choice whether to use them. List: [`helpers/registry.json`](../../../../helpers/registry.json). Do not invent these:
  - `python3 helpers/pack.py --jobs <card_id>` — same pack as `Open-UX:pack`
  - `python3 helpers/rank_pack.py --query "…" < pack.json` — BM25 over this page (`overview` / `apply_when` / `hints` / `component`). Fail-open. No winner.
  - `open-ux pack --jobs <card_id>` — same wire
  - `python3 helpers/get_component.py button --include-used-on` — same wire as `Open-UX:get_component`
  - `open-ux component button --include-used-on` — same wire
- `Open-UX:list_situations` — Card index; with `container=` that kind's specs (`when` / `reject`)
- `Open-UX:suggest_situations` — catalog map (lock-order overviews). Vague surface or pasted UI. Does not pick a Card.
- `Open-UX:get_guideline` / `Open-UX:search_guidelines` / `Open-UX:list_guidelines` — cite. Full-record fields: [guideline.md](guideline.md).
- `Open-UX:list_components` / `Open-UX:get_component` — widget index and record. Open `get_component` only for ids on a pack row or Card. Full-record fields: [component.md](component.md).

Empty shelf → say so. We are a catalog. They choose what to take. Cited criteria help you decide; the decision is yours. We don't return pass or fail.

Without a Claude session, [`helpers/mcp_call.py`](../../../../helpers/mcp_call.py) speaks `tools/list` and `tools/call`. In Claude, call the tools. Do not treat `mcp_call.py` as the skill path. Contributor scripts live in `scripts/` — not for agents.
