---
name: open-ux
description: >-
  Use when composing or reviewing UI — a form, field labels, input choice,
  validation, buttons or CTAs, delete/unsaved confirm, empty or error states,
  navigation, a table or dashboard, a modal, or a multi-step flow. Open UX is
  a cited UX catalog for agents. Pick one Situation Card for the compose job,
  then call Open-UX:get_situation and Open-UX:audit with jobs=<card_id>. Do
  not browse the catalog. Do not send a file. Returns cited criteria, not pass
  or fail. home/cart/checkout are context, not ids. Use
  Open-UX:suggest_situations only if the task is vague or the UI is pasted.
  Hosted: uxmcp_ bearer. Self-host stdio: no key.
---

# Open UX

Cited UX rules agents audit against. The catalog is the source of truth.

This skill does **not** contain rule bodies or guideline ids. Route to a Card, then call the server.

## Connect

1. Hosted URL + bearer `uxmcp_` in client settings (`OPEN_UX_URL`, `OPEN_UX_API_KEY`). Self-host stdio needs no key.
2. If hosted and unauthenticated, tell the human to request an invite on the hosted `/invite` page (landing **Get a key**). Do not invent a key.

## Path

1. Pick a **Situation Card** from the table below. That is the need.
2. Call `Open-UX:get_situation` with that Card id. You get when / reject / facets / leaf pointers. Not rule bodies.
3. Call `Open-UX:audit` with `jobs=<card_id>` (or `Open-UX:get_guideline` once you have an id). Apply the returned `rule` / `pass_when` / `fail_when` to the work you already have.
4. Fall back to `Open-UX:suggest_situations` only when the task is vague or the artifact is pasted UI. Do not start there.

Do not pass a file. The host does not return pass or fail. Surfaces (`home`, `cart`, `checkout`) are context, not catalog ids. Decompose them into a Card. Leaf ids (`avoid_placeholder_as_label`) are not needs — do not put them on `jobs=`.

If the catalog is empty, say so. Do not invent rules.

## Containers → Cards

| Container | Pick this Card | When |
| --- | --- | --- |
| Forms & input | `design_a_form` | Signup, settings, or checkout *fields*; labels; choosing a control; grouping; required; helper text |
| Forms & input | `handle_form_errors` | Validation, inline or summary errors, submit-failure messaging *on a form* |
| Actions & decisions | `design_actions_and_ctas` | Primary vs secondary; submit / continue label; toolbar; buttons too small |
| Actions & decisions | `protect_destructive_and_leave` | Delete confirmation; discard; leave unsaved work; confirm / undo |
| Feedback & status | `compose_feedback` | Toast after save; loading; empty state; 404; hard error (not a field); failure tone |
| Navigation & wayfinding | `orient_in_the_place` | Sidebar; breadcrumbs; tabs or menu; which *section* they are in; top nav |
| Layout & data display | `compose_a_data_display` | Table or card grid; dashboard; scannable table; chart vs table |
| Overlays & content structure | `choose_an_overlay` | Modal vs accordion; tooltip vs inline help; progressive disclosure; side panel |
| Multi-step flows | `build_a_multi_step_flow` | Checkout *flow*; split a long form into steps; progress indicator; leave mid-flow; onboarding *sequence* |

`compose_a_data_display` and `choose_an_overlay` are provisional. Still pick them when that is the job; do not invent a tenth Card.

## Reject (closest wrong Card)

- Validation / inline errors → `handle_form_errors`, not `design_a_form` or `compose_feedback`
- Delete / unsaved leave → `protect_destructive_and_leave`, not `design_actions_and_ctas`
- Wizard / steps → `build_a_multi_step_flow`, not `orient_in_the_place`
- Table / dashboard → `compose_a_data_display`, not `design_a_form`
- `checkout` / `home` / `cart` → decompose; they are not Cards

## Tools

Use fully qualified names. Bare names fail when other MCP servers are loaded.

- `Open-UX:list_situations` — optional `container`. Card index only.
- `Open-UX:get_situation` — Card id. Fails on a Leaf id.
- `Open-UX:suggest_situations` — `task_text`, optional `surface` (ranking bias only). Fallback.
- `Open-UX:audit` — `jobs=<card_id>` or `guideline_ids`. Optional `query`, `limit`. Cited criteria. No file. No verdict.
- `Open-UX:get_guideline` / `Open-UX:list_guidelines` / `Open-UX:search_guidelines` — after you have ids or a Card.

There is no server LLM. If a call returns empty, say so.
