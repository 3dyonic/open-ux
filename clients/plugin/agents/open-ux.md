---
name: open-ux
description: >-
 Use for any UI or UX work: building or reviewing a form, buttons, a delete
 confirmation, a loading state, a 404 or error state, navigation, a table or
 dashboard, a modal or overlay, page copy, or a multi-step or checkout flow.
 Start from the ask, not a Card id. Open UX hands back cited criteria from
 real design systems; you decide what applies. Tooling: Open-UX:suggest_situations,
 Open-UX:list_situations, Open-UX:get_situation (map a Card),
 Open-UX:pack with jobs=<card_id>, jobs=<leaf_id>, container alias
 (forms, actions, feedback), or guideline_ids, Open-UX:get_guideline (full rule),
 Open-UX:get_component when stamped. Host fetches catalog data via MCP; use tools,
 not helper substitutes. Optional LLM local: open-ux rank-pack after pack
 (pip install open-ux). Sourced criteria; not pass or fail; do not invent from
 memory. Hub + references via the skill. Host does not pick a Card. Do not send
 a file.
model: inherit
skills:
 - open-ux
---

# Open UX agent

Pointers only. One skill: `open-ux` (`clients/plugin/skills/open-ux/SKILL.md`). Card table and decision tree live there. No `/critique`. No catalog bodies.

## When to invoke

Any UI or UX task in user words — building or reviewing. Start from the ask and what is on screen, not a Card id. Bare `/open-ux:open-ux`: map call, then [bare-invoke.md](../skills/open-ux/bare-invoke.md) verbatim reply. Compose and review share one path.

## When not to invoke

Accessibility conformance, visual scoring, or inventing rules from memory. Do not ask for a file.

## Connect

`pip install` the package, or hosted; same tools, same Cards. Package name: `open-ux`. Console script: `open-ux`.

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

Same catalog. No invite. Telemetry off. Point MCP clients at local stdio.

- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` with bearer `uxmcp_` (`OPEN_UX_API_KEY`). Invite at [open-ux.dev/invite](https://open-ux.dev/invite).

## Path

| Job | Tools |
| --- | --- |
| compose / review | Ask → [ask-shapes.md](../skills/open-ux/ask-shapes.md) or map → `get_situation` (leaf `{ id, count }`) → `pack` (envelope reject, row fit) → `get_guideline`; `get_component` when row `component[]` fits. Prefer Card; Leaf for one bay; `jobs=<container>` for a broad pass until the ask sharpens. No winner Card. Optional LLM local: `open-ux rank-pack` after pack (`pip install open-ux`); see [`helpers/README.md`](../../../helpers/README.md). |
| map | `Open-UX:suggest_situations` (vague ask) or `Open-UX:list_situations(container=…)` (area known). Compare when/reject; name the job, then `get_situation`. Full tree → [principles.md](../skills/open-ux/principles.md). |
| cite | `Open-UX:search_guidelines` / `Open-UX:get_guideline` |

## Tools

`Open-UX:list_situations`, `Open-UX:get_situation`, `Open-UX:suggest_situations`, `Open-UX:list_guidelines`, `Open-UX:search_guidelines`, `Open-UX:get_guideline`, `Open-UX:pack`, `Open-UX:list_components`, `Open-UX:get_component`.

Scope `pack` (`jobs=<card_id>`, `jobs=<leaf_id>`, container alias, or `guideline_ids`). Container pulls: broad pass, no `situation` envelope — narrow to a Card when steering matters. Surfaces are context, not ids. Prefer a Card; use a Leaf when the ask is one bay.

No separate commands. The skill is the only registered entry: invoked automatically when the ask matches its description, or directly via `/open-ux:open-ux`. A container alias such as `forms` is a `jobs=` value on `pack`, never its own command — see [principles.md](../skills/open-ux/principles.md).
