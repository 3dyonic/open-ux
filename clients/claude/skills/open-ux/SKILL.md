---
name: open-ux
description: >-
  Use when building or checking UI — composing or reviewing a form, field
  labels, input choice, validation, buttons or CTAs, delete/unsaved confirm,
  empty or error states, navigation, a table or dashboard, a modal, or a
  multi-step flow. Open UX is a cited UX catalog for agents. Pick one
  Situation Card, then call Open-UX:get_situation and Open-UX:audit with
  jobs=<card_id>. Don't invent UX rules from memory; apply the cited pack
  to work already in hand. Returns cited criteria, not pass or fail.
  home/cart/checkout are context, not ids. Use Open-UX:suggest_situations
  only if the task is a vague surface or pasted UI. Cite via
  Open-UX:search_guidelines or Open-UX:get_guideline. pip install open-ux
  (stdio, no key) or hosted (live catalog).
---

# Open UX

Need in → cited criteria pack out. You already have the UI. We hand you the matching cited rules so you don't invent UX from memory.

Compose and review share this one trigger. Pick a Situation Card, call `Open-UX:get_situation`, then fetch the pack — prefer `scripts/audit.py` so you don't invent args, or call `Open-UX:audit` with `jobs=<card_id>`. Surfaces (`home`, `cart`, `checkout`) are context, not Cards. Container aliases `forms` / `actions` / `feedback` work as a broad first scope.

When you need a map of what exists — by **category**, then **source** — read [`catalog/MANIFEST.md`](../../../../catalog/MANIFEST.md). Then fetch one id.

## Examples

- **Signup / settings fields.** Card `design_a_form`. Pack via `jobs=design_a_form`. Same if you are reviewing that form.
- **Review a delete confirm.** Card `protect_destructive_and_leave`.
- **Vague checkout.** `Open-UX:suggest_situations` with the task text, then pick a Card (often `build_a_multi_step_flow` or `design_a_form`) and audit that.
- **Already have a guideline id.** `Open-UX:get_guideline` for that one cited body.

## Connect

`pip install` the package, or hosted — same tools, same Cards.

- **Package** (local): `pip install open-ux`, then `python -m open_ux stdio` (console script: `open-ux`). Same catalog. No invite. Telemetry off.
- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` + bearer `uxmcp_` (`OPEN_UX_API_KEY`). Request an invite at `/invite` (landing **Get a key**).

## Situation Cards

Reject **crosses containers** — pick the Card the ask actually is.

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

`checkout` / `home` / `cart` are not Cards.

## Tools

Fully qualified `Open-UX:*` names. `/list` `/get` / map / cite stay on tools. Card pick is the table above (judgment).

- `Open-UX:get_situation` — Card when / reject / pointers (not rule bodies)
- `Open-UX:audit` — `jobs=<card_id>` or `guideline_ids`. The pack. First-class; equally valid to call this instead of the helper.
- Helper (available, not required): `python3 scripts/audit.py --jobs <card_id>` or `--guideline-ids`. Prefer the script when composing or reviewing so you don't invent args. Your choice.
- `Open-UX:list_situations` — Card index; optional `container`
- `Open-UX:suggest_situations` — vague surface or pasted UI
- `Open-UX:get_guideline` / `Open-UX:search_guidelines` / `Open-UX:list_guidelines` — cite

Empty pack → say so. We don't return pass or fail.

Without a Claude session, [`scripts/mcp_call.py`](../../../../scripts/mcp_call.py) speaks `tools/list` and `tools/call`. In Claude, call the tools. Do not treat `mcp_call.py` as the skill path.
