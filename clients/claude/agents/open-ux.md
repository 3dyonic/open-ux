---
name: open-ux
description: Pointers for the Open UX skill and hosted tools. Use when composing or reviewing UI against cited UX rules.
---

# Open UX agent

Pointers only. One skill: `open-ux` (`clients/claude/skills/open-ux/SKILL.md`). No `/critique`. No catalog bodies.

## Connect

`pip install` the package, or hosted — same tools, same Cards.

- **Package** (local): `pip install open-ux`, then `python -m open_ux stdio` (console script: `open-ux`). Same catalog. No invite. Telemetry off.
- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` with bearer `uxmcp_` (`OPEN_UX_API_KEY`). Invite at [open-ux.dev/invite](https://open-ux.dev/invite).

## Path

| Job | How |
| --- | --- |
| compose / review | Pick a Card → `Open-UX:get_situation` → **must** run `scripts/audit.py` `jobs=<card_id>` |
| map | `Open-UX:suggest_situations` (not a script) |
| cite | `Open-UX:search_guidelines` / `Open-UX:get_guideline` (not a script) |

Scope audit (`jobs=` or `guideline_ids`). Surfaces are context, not ids. Leaf ids are not needs.

Slash commands `/list` `/get` stay on `Open-UX:*` tools. `/audit` plus aliases `/forms` `/actions` `/feedback` pick a Card, then must run the audit script.
