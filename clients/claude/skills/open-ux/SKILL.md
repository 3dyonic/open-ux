---
name: open-ux
description: >-
  Use when building or checking UI — composing or reviewing a form, field
  labels, input choice, validation, buttons or CTAs, delete/unsaved confirm,
  empty or error states, navigation, a table or dashboard, a modal, or a
  multi-step flow. Open UX is a cited UX catalog for agents. Compose (default):
  pick one Situation Card, then call Open-UX:get_situation and Open-UX:audit
  with jobs=<card_id>. Review uses the same Cards and audit; you judge locally;
  do not send a file. Returns cited criteria, not pass or fail.
  home/cart/checkout are context, not ids. Use Open-UX:suggest_situations only
  if the task is a vague surface or pasted UI. Cite via
  Open-UX:search_guidelines or Open-UX:get_guideline. Hosted (live catalog): uxmcp_ bearer. Or download the package (stdio, no key).
---

# Open UX

Cited UX rules agents audit against. The catalog is the source of truth.

This skill does **not** contain rule bodies or guideline ids. Route to a Card, then call the server.

One skill in the system prompt. Compose and review share this pull trigger (“building or checking UI”). Only `open-ux` is always-on. Do not load `open-ux-forms`, `open-ux-actions`, or `open-ux-feedback` packages — those do not exist.

When you need a map of what exists — by **category**, then **source** — read [`catalog/MANIFEST.md`](../../../../catalog/MANIFEST.md). Then fetch one id. Do not load every rule file.

## Offerings

| Job | When | Path |
| --- | --- | --- |
| **compose** (default) | Building UI | Pick a Card → `Open-UX:get_situation` → `Open-UX:audit` with `jobs=<card_id>` |
| **review** | Checking UI already in hand | Same Cards and `audit`. You judge. No file to the host. Read [review.md](review.md) if needed. |
| **map** | The ask is a surface (`home` / `cart` / `checkout`) or pasted UI | Fallback **inside this skill**: `Open-UX:suggest_situations`. Not a second skill. Read [map.md](map.md) if needed. |
| **cite** | Look up one shared rule | `Open-UX:search_guidelines` / `Open-UX:get_guideline`. Read [cite.md](cite.md) if needed. |

Sibling files cost nothing until you read them.

## Connect

Hosted or download the package — same tools, same Cards.

- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` + bearer `uxmcp_` (`OPEN_UX_API_KEY`). Request an invite at `/invite` (landing **Get a key**).
- **Package** (local): clone [github.com/3dyonic/open-ux](https://github.com/3dyonic/open-ux) (MIT), `pip install -e "packages/mcp[dev]"`, then `python -m open_ux stdio`. Same catalog. No invite. Telemetry off. Optional: `python -m open_ux validate-catalog`.

## Compose path

1. Pick a **Situation Card** from the table below. That is the need.
2. Call `Open-UX:get_situation` with that Card id. You get when / reject / facets / leaf pointers. Not rule bodies.
3. Call `Open-UX:audit` with `jobs=<card_id>` (or `guideline_ids` once you have ids). That returns the Card's cited criteria. Apply them to the work you already have.
4. Fall back to `Open-UX:suggest_situations` only when the task is a vague surface or the artifact is pasted UI. Do not start there.

Always scope `audit`: pass `jobs=` or `guideline_ids`. Never call it empty. Never send a file, `content`, or a scan payload. The host does not return pass or fail.

Surfaces (`home`, `cart`, `checkout`) are context, not catalog ids. Decompose them into a Card. Leaf ids are not needs — do not put them on `jobs=`. Container aliases `forms` / `actions` / `feedback` are valid broad scopes for the first three containers only.

If the catalog is empty, say so. Do not invent rules.

## Containers → Cards

Seven containers. Aliases `forms` / `actions` / `feedback` apply to the first three only. Reject **crosses containers** — pick the Card the ask actually is, not the container you arrived through.

| Container | Card | When | Reject (use this instead) |
| --- | --- | --- | --- |
| Forms & input (`forms`) | `design_a_form` | Signup, settings, or checkout *fields*; labels; placeholders; choosing a control; grouping; required marks; helper text | Validation / inline errors → `handle_form_errors`. Login / password → `compose_sign_in`. Wizard / steps → `build_a_multi_step_flow`. CTA wording → `design_actions_and_ctas`. Table / dashboard → `compose_a_data_display` |
| Forms & input (`forms`) | `handle_form_errors` | Composing validation; inline or summary errors; submit-failure messaging *on a form* | Page-level empty / 404 / hard error / toast → `compose_feedback`. Unmarked required before submit → `design_a_form` |
| Forms & input (`forms`) | `compose_sign_in` | Login, show password, forgot-password, credential fields | Ordinary non-credential fields → `design_a_form`. Inline validation after submit → `handle_form_errors` |
| Actions & decisions (`actions`) | `design_actions_and_ctas` | Primary vs secondary; submit / continue label; toolbar; buttons too small; command panel | Delete / discard / unsaved leave → `protect_destructive_and_leave`. Field labels stay `design_a_form`. Page voice or link text → `write_the_interface` |
| Actions & decisions (`actions`) | `protect_destructive_and_leave` | Delete confirmation; discard; leave unsaved work; confirm / undo | Unclear Continue / Submit label → `design_actions_and_ctas`. Failure tone after it already fired → `compose_feedback` |
| Feedback & status (`feedback`) | `compose_feedback` | Toast after save; loading; empty state; 404; hard error (not a field); failure tone | Inline field errors → `handle_form_errors`. Progress inside a wizard → `build_a_multi_step_flow`. Loading on the control itself → `design_actions_and_ctas` |
| Navigation & wayfinding | `orient_in_the_place` | Sidebar; breadcrumbs; tabs or menu; which *section* they are in; top nav | Step indicators inside a wizard → `build_a_multi_step_flow`. Search control placement → `compose_search` |
| Navigation & wayfinding | `compose_search` | Header or homepage search; search box vs link; place the search control | Site chrome / which section → `orient_in_the_place`. Link destination wording → `write_the_interface` |
| Layout & data display | `compose_a_data_display` | Table or card grid; dashboard; scannable table; chart vs table | Controls inside a form → `design_a_form`. Page scan path → `compose_the_layout`. Overlay choice → `choose_an_overlay` |
| Layout & data display | `compose_the_layout` | Page structure and headings; inverted pyramid; keep the page scannable | Table / chart / map → `compose_a_data_display`. Voice or link wording → `write_the_interface` |
| Layout & data display | `write_the_interface` | Link destination text; you/your voice; page copy that is not a button or field label | Button / command verbs → `design_actions_and_ctas`. Field labels stay `design_a_form`. Section chrome → `orient_in_the_place` |
| Overlays & content structure | `choose_an_overlay` | Modal vs accordion; tooltip vs inline help; hide advanced options; side panel | Destructive decision inside a dialog → `protect_destructive_and_leave`. Fields inside a modal → `design_a_form`. Page layout → `compose_the_layout` |
| Multi-step flows | `build_a_multi_step_flow` | Checkout *flow*; split a long form into steps; progress indicator; leave mid-flow; onboarding *sequence* | Single form on one screen → `design_a_form`. Site-level nav chrome → `orient_in_the_place`. Leave-warn as the only ask → `protect_destructive_and_leave` |

`checkout` / `home` / `cart` are not Cards. Decompose them.

## Tools

Use fully qualified names. Bare names fail when other MCP servers are loaded.

- `Open-UX:list_situations` — optional `container`. Card index only.
- `Open-UX:get_situation` — Card id. Fails on a Leaf id.
- `Open-UX:suggest_situations` — `task_text`, optional `surface` (ranking bias only). Map fallback.
- `Open-UX:audit` — `jobs=<card_id>` or `guideline_ids`. Optional `query`, `limit`. Cited criteria. No file. No pass or fail from the host.
- `Open-UX:get_guideline` / `Open-UX:list_guidelines` / `Open-UX:search_guidelines` — after you have ids, or for cite.

There is no server LLM. If a call returns empty, say so.
