---
name: open-ux
description: >-
  Use when building or checking UI — composing or reviewing a form, field
  labels, input choice, validation, buttons or CTAs, delete/unsaved confirm,
  empty or error states, navigation, a table or dashboard, a modal, or a
  multi-step flow. Open UX is a cited UX catalog for agents. Compose (default)
  and review: pick one Situation Card, then run scripts/audit.py
  --jobs=<card_id>. Never a file. Never scores. Returns cited criteria, not
  pass or fail. home/cart/checkout are context, not ids. Map fallback:
  scripts/suggest.py. Cite: scripts/get.py. Hosted: uxmcp_ bearer
  (OPEN_UX_API_KEY). Self-host: OPEN_UX_URL or stdio.
---

# Open UX

Cited UX rules. The catalog is the source of truth. No rule bodies or guideline ids in this file.

One package: `open-ux`. Do not load `open-ux-forms` / `open-ux-actions` / `open-ux-feedback`.

Connect: hosted `https://open-ux.dev/mcp` + `OPEN_UX_API_KEY` (`uxmcp_`). Self-host: `OPEN_UX_URL` or `OPEN_UX_TRANSPORT=stdio`. If hosted 401s, send the human to `/invite`. Do not invent a key.

Need is a **Situation Card** or container alias (`forms` / `actions` / `feedback`). Leaf ids are not needs. Surfaces are not ids. Reject **crosses containers** — pick the Card the ask actually is.

| Job | Script |
| --- | --- |
| **compose** / **review** | `scripts/audit.py --jobs design_a_form` (or `--guideline-ids`). Optional `--query`, `--limit`. You judge. |
| **map** | `scripts/suggest.py "task text"` then audit that Card |
| **cite** | `scripts/get.py <guideline_id>` · index `scripts/list.py --guidelines` |
| **index** | `scripts/list.py` · `scripts/get.py <card_id>` |

Always `jobs=` or `--guideline-ids`. Never a file. Never pass or fail from the host. If empty, say so. Do not invent rules.

Catalog map (category, then source): [`catalog/MANIFEST.md`](../../../../catalog/MANIFEST.md).

## Cards

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
