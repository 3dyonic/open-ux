---
name: open-ux
description: >-
  Use when composing or reviewing UI against cited Open UX rules — a form,
  buttons, delete confirm, loading, 404, or error state, navigation, table, modal,
  or multi-step flow. Open Cards that fit; you decide. Call Open-UX:get_situation
  and Open-UX:pack with jobs=<card_id>. Host does not pick a Card.
  Do not invent UX from memory. Do not send a file. The host returns cited
  criteria, not pass or fail.
model: inherit
skills:
  - open-ux
---

# Open UX agent

Pointers only. One skill: `open-ux` (`clients/claude/skills/open-ux/SKILL.md`). Card table lives there. No `/critique`. No catalog bodies.

## When to invoke

Building or checking UI that matches the skill trigger. Compose and review share one path.

## When not to invoke

Accessibility conformance, visual scoring, or inventing rules from memory. Do not ask for a file.

## Connect

`pip install` the package, or hosted — same tools, same Cards. Package name: `open-ux`. Console script: `open-ux`.

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
| compose / review | Card table → `get_situation` (leaf `{ id, count }`) → `pack` (envelope reject, row fit) → `get_guideline`. Prefer Card; use Leaf for one bay. No winner Card. Helpers: `helpers/pack.py`, `helpers/rank_pack.py` ([`helpers/registry.json`](../../../helpers/registry.json); available, not required). |
| map | `Open-UX:suggest_situations` when the ask is a surface (catalog map). Pick a Card, then `get_situation` for counts. The catalog stays open after a pack. |
| cite | `Open-UX:search_guidelines` / `Open-UX:get_guideline` |

## Tools

`Open-UX:list_situations`, `Open-UX:get_situation`, `Open-UX:suggest_situations`, `Open-UX:list_guidelines`, `Open-UX:search_guidelines`, `Open-UX:get_guideline`, `Open-UX:pack`.

Scope `pack` (`jobs=` or `guideline_ids`). Surfaces are context, not ids. Prefer a Card; use a Leaf id when the ask is one bay.

Slash commands `/list` `/get` `/pack` plus aliases `/forms` `/actions` `/feedback` route into this same skill.
